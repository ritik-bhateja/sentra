"""Pydantic request/response schemas for the Admin User Management API.

Defines strict validation for admin operations including user creation,
role changes, listing, and deletion. Role validation restricts assignable
roles to viewer_with_query and viewer_without_query (admin is never
assignable via the console).

Requirements: 2.5, 2.7, 3.5, 4.4, 8.1, 8.2, 8.3
"""

from pydantic import BaseModel, EmailStr, field_validator


# Roles that an admin can assign through the Admin Console.
# The 'admin' role is intentionally excluded.
ASSIGNABLE_ROLES: list[str] = ["viewer_with_query", "viewer_without_query"]


class AddUserRequest(BaseModel):
    """Request body for POST /admin/users.

    Validates:
    - email: must be a valid email format (Requirement 2.7, 8.1)
    - role: must be one of the assignable roles (Requirement 2.5)
    """

    email: EmailStr
    role: str

    @field_validator("role")
    @classmethod
    def role_must_be_assignable(cls, v: str) -> str:
        if v not in ASSIGNABLE_ROLES:
            raise ValueError(
                f"Role must be one of: {', '.join(ASSIGNABLE_ROLES)}"
            )
        return v


class ChangeRoleRequest(BaseModel):
    """Request body for PUT /admin/users/{email}/role.

    Validates:
    - role: must be one of the assignable roles (Requirement 3.5)
    """

    role: str

    @field_validator("role")
    @classmethod
    def role_must_be_assignable(cls, v: str) -> str:
        if v not in ASSIGNABLE_ROLES:
            raise ValueError(
                f"Role must be one of: {', '.join(ASSIGNABLE_ROLES)}"
            )
        return v


class UserWithRole(BaseModel):
    """Response model representing a user with their Keycloak role.

    Fields:
    - id: RDS user ID
    - email: user email address
    - created_at: Unix ms timestamp of account creation (nullable)
    - last_login: Unix ms timestamp of last login (nullable)
    - role: current Keycloak role, or "unknown" if Keycloak unreachable
    """

    id: int
    email: str
    created_at: int | None = None
    last_login: int | None = None
    role: str


class ListUsersResponse(BaseModel):
    """Response model for GET /admin/users.

    Fields:
    - users: list of all users with their roles
    - warning: set if Keycloak was unreachable during role lookup
    """

    users: list[UserWithRole]
    warning: str | None = None


class RoleInfo(BaseModel):
    """Response model for a single assignable role entry.

    Fields:
    - value: the role identifier (e.g. "viewer_with_query")
    - display_name: human-readable label (e.g. "Viewer (with Query Access)")
    """

    value: str
    display_name: str


class DeleteUserResponse(BaseModel):
    """Response model for DELETE /admin/users/{email}.

    Fields:
    - message: success description
    - email: the deleted user's email
    - warning: set if Keycloak deletion failed (RDS deletion still succeeded)
    """

    message: str
    email: str
    warning: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response body for admin endpoints."""

    detail: str
