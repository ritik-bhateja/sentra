"""Admin User Management service layer.

Orchestrates CRUD operations across RDS (login allow-list) and Keycloak
(role authority). Each method enforces atomicity and consistency rules:

- add_user: RDS insert rolled back on Keycloak failure (Req 9.1)
- delete_user: RDS deletion proceeds even if Keycloak fails (Req 9.2)
- change_role: No RDS changes needed; error returned on Keycloak failure (Req 9.4)
- list_users: Degrades gracefully if Keycloak unreachable (Req 7.2)

Requirements: 2.1, 2.2, 2.3, 2.4, 2.6, 3.1, 3.2, 3.3, 3.6, 4.1, 4.2,
             5.1, 5.2, 5.3, 5.4, 5.5, 7.1, 7.2, 7.4, 9.1, 9.2, 9.3, 9.4
"""

from __future__ import annotations

import logging
import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from auth.keycloak_client import KeycloakClient, KeycloakUnavailable
from auth.roles import Role
from models_v3 import User
from admin_schemas import (
    ASSIGNABLE_ROLES,
    UserWithRole,
    ListUsersResponse,
    RoleInfo,
    DeleteUserResponse,
)

logger = logging.getLogger(__name__)

# Simple email regex for validation (covers common cases).
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AdminService:
    """Business logic for admin user management operations."""

    # ------------------------------------------------------------------
    # List users
    # ------------------------------------------------------------------

    @staticmethod
    def list_users_with_roles(
        db: Session, keycloak_client: KeycloakClient
    ) -> ListUsersResponse:
        """Return all users from RDS enriched with Keycloak roles.

        Users are sorted by created_at DESC. If Keycloak is unreachable,
        roles are set to "unknown" and a warning is included.

        Requirements: 7.1, 7.2, 7.4
        """
        users = db.query(User).order_by(User.created_at.desc()).all()

        keycloak_available = True
        warning: str | None = None

        # Build response list
        user_list: list[UserWithRole] = []
        for user in users:
            role = "unknown"
            if keycloak_available:
                try:
                    roles = keycloak_client.get_realm_roles_for_email(user.email)
                    # Pick the most relevant Sentra role
                    if "admin" in roles:
                        role = "admin"
                    elif "viewer_with_query" in roles:
                        role = "viewer_with_query"
                    elif "viewer_without_query" in roles:
                        role = "viewer_without_query"
                    else:
                        role = "none"
                except KeycloakUnavailable:
                    keycloak_available = False
                    warning = (
                        "Could not reach Keycloak. Roles shown as 'unknown'."
                    )
                    role = "unknown"

            user_list.append(
                UserWithRole(
                    id=user.id,
                    email=user.email,
                    created_at=(
                        int(user.created_at.timestamp() * 1000)
                        if user.created_at
                        else None
                    ),
                    last_login=(
                        int(user.last_login.timestamp() * 1000)
                        if user.last_login
                        else None
                    ),
                    role=role,
                )
            )

        return ListUsersResponse(users=user_list, warning=warning)

    # ------------------------------------------------------------------
    # Add user
    # ------------------------------------------------------------------

    @staticmethod
    def add_user(
        db: Session, keycloak_client: KeycloakClient, email: str, role: str
    ) -> UserWithRole:
        """Create a user in RDS and Keycloak with the specified role.

        Atomicity: If Keycloak fails after RDS insert, the RDS insert is
        rolled back and HTTP 503 is raised.

        Requirements: 2.1, 2.2, 2.3, 2.4, 2.6, 9.1, 9.3
        """
        # Validate email format
        if not email or not email.strip():
            raise HTTPException(status_code=400, detail="Email is required")
        email = email.strip().lower()
        if not _EMAIL_RE.match(email):
            raise HTTPException(
                status_code=400, detail="Invalid email format"
            )

        # Validate role
        if not role:
            raise HTTPException(status_code=400, detail="Role is required")
        if role not in ASSIGNABLE_ROLES:
            raise HTTPException(
                status_code=400,
                detail=f"Role must be one of: {', '.join(ASSIGNABLE_ROLES)}",
            )

        # Check duplicate in RDS
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(
                status_code=409, detail=f"User already exists: {email}"
            )

        # Insert into RDS within a transaction
        new_user = User(email=email)
        db.add(new_user)
        db.flush()  # Get the ID without committing

        # Attempt Keycloak operations
        try:
            kc_user_id = keycloak_client.create_user(email)
            keycloak_client.assign_realm_role(kc_user_id, Role(role))
        except KeycloakUnavailable as exc:
            # Rollback the RDS insert
            db.rollback()
            logger.warning(
                "Keycloak unavailable during add_user for %s: %s", email, exc
            )
            raise HTTPException(
                status_code=503,
                detail="Keycloak service unavailable. Operation rolled back.",
            )

        # Commit the RDS insert
        db.commit()
        db.refresh(new_user)

        return UserWithRole(
            id=new_user.id,
            email=new_user.email,
            created_at=(
                int(new_user.created_at.timestamp() * 1000)
                if new_user.created_at
                else None
            ),
            last_login=None,
            role=role,
        )

    # ------------------------------------------------------------------
    # Change user role
    # ------------------------------------------------------------------

    @staticmethod
    def change_user_role(
        db: Session, keycloak_client: KeycloakClient, email: str, new_role: str
    ) -> UserWithRole:
        """Change a user's role in Keycloak.

        Roles live exclusively in Keycloak so no RDS changes are needed.
        If Keycloak fails, an error is returned without modifying anything.

        Requirements: 3.1, 3.2, 3.3, 3.6, 9.4
        """
        # Validate role
        if not new_role:
            raise HTTPException(status_code=400, detail="Role is required")
        if new_role not in ASSIGNABLE_ROLES:
            raise HTTPException(
                status_code=400,
                detail=f"Role must be one of: {', '.join(ASSIGNABLE_ROLES)}",
            )

        # Verify user exists in RDS
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User not found: {email}"
            )

        # Check if target user is an admin (cannot change admin roles)
        try:
            current_roles = keycloak_client.get_realm_roles_for_email(email)
        except KeycloakUnavailable as exc:
            logger.warning(
                "Keycloak unavailable during role check for %s: %s", email, exc
            )
            raise HTTPException(
                status_code=503,
                detail="Keycloak service unavailable. Cannot verify user role.",
            )

        if "admin" in current_roles:
            raise HTTPException(
                status_code=403,
                detail="Cannot modify admin users through this endpoint",
            )

        # Get the Keycloak user ID for role operations
        try:
            kc_user_id = keycloak_client._find_user_id_by_email(email)
            if kc_user_id is None:
                # User exists in RDS but not in Keycloak — create them
                kc_user_id = keycloak_client.create_user(email)
            else:
                # Remove existing Sentra roles before assigning new one
                sentra_roles = [
                    r for r in current_roles
                    if r in ("viewer_with_query", "viewer_without_query")
                ]
                if sentra_roles:
                    keycloak_client.remove_realm_roles(kc_user_id, sentra_roles)

            # Assign the new role
            keycloak_client.assign_realm_role(kc_user_id, Role(new_role))
        except KeycloakUnavailable as exc:
            logger.warning(
                "Keycloak failed during role change for %s: %s", email, exc
            )
            raise HTTPException(
                status_code=503,
                detail="Keycloak service unavailable. Role change failed.",
            )

        return UserWithRole(
            id=user.id,
            email=user.email,
            created_at=(
                int(user.created_at.timestamp() * 1000)
                if user.created_at
                else None
            ),
            last_login=(
                int(user.last_login.timestamp() * 1000)
                if user.last_login
                else None
            ),
            role=new_role,
        )

    # ------------------------------------------------------------------
    # Delete user
    # ------------------------------------------------------------------

    @staticmethod
    def delete_user(
        db: Session, keycloak_client: KeycloakClient, email: str
    ) -> DeleteUserResponse:
        """Delete a user from RDS and attempt Keycloak deletion.

        If Keycloak deletion fails, the RDS deletion still proceeds and
        a warning is included in the response.

        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.2, 9.3
        """
        # Verify user exists in RDS
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User not found: {email}"
            )

        # Check if target user is an admin (cannot delete admin users)
        try:
            current_roles = keycloak_client.get_realm_roles_for_email(email)
        except KeycloakUnavailable as exc:
            logger.warning(
                "Keycloak unavailable during admin check for %s: %s",
                email,
                exc,
            )
            raise HTTPException(
                status_code=503,
                detail="Keycloak service unavailable. Cannot verify user role.",
            )

        if "admin" in current_roles:
            raise HTTPException(
                status_code=403,
                detail="Cannot delete admin users through this endpoint",
            )

        # Delete from RDS
        db.delete(user)
        db.commit()

        # Attempt Keycloak deletion (warn on failure)
        warning: str | None = None
        try:
            keycloak_client.delete_user(email)
        except KeycloakUnavailable as exc:
            logger.warning(
                "Keycloak deletion failed for %s: %s", email, exc
            )
            warning = (
                f"Keycloak deletion failed: {exc}. "
                "Manual cleanup may be required."
            )

        message = (
            "User deleted successfully" if warning is None
            else "User deleted from RDS"
        )

        return DeleteUserResponse(
            message=message,
            email=email,
            warning=warning,
        )

    # ------------------------------------------------------------------
    # Get assignable roles
    # ------------------------------------------------------------------

    @staticmethod
    def get_assignable_roles() -> list[RoleInfo]:
        """Return the list of roles an admin can assign.

        The 'admin' role is intentionally excluded.

        Requirements: 4.1, 4.2
        """
        return [
            RoleInfo(
                value="viewer_with_query",
                display_name="Viewer (with Query Access)",
            ),
            RoleInfo(
                value="viewer_without_query",
                display_name="Viewer (without Query Access)",
            ),
        ]
