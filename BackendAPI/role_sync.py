"""Role synchronization service: mirrors authorized RDS users into Keycloak.

This module ensures every authorized user in the RDS ``users`` table has a
corresponding record in the Keycloak Sentra realm. New Keycloak users are
assigned the DEFAULT_ROLE (viewer_without_query). Existing Keycloak users are
left untouched — their current role assignments are never modified.

The sync is idempotent: running it multiple times produces the same final state
and never creates duplicates or overwrites roles.

CLI usage (follows existing ``add_authorized_user.py`` conventions):

    python role_sync.py sync

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 12.1
"""

from __future__ import annotations

import logging
import sys

from dotenv import load_dotenv

load_dotenv()

from auth.keycloak_client import KeycloakClient, KeycloakUnavailable
from auth.roles import DEFAULT_ROLE
from database import SessionLocal
from models_v3 import User

logger = logging.getLogger(__name__)


def sync_users(client: KeycloakClient, db) -> dict:
    """Mirror all authorized RDS users into Keycloak.

    For each user in the RDS ``users`` table:
    - If the user already exists in Keycloak → skip (leave role unchanged).
    - If the user does not exist → create them and assign DEFAULT_ROLE.
    - If an error occurs for a specific user → record it and continue.

    Args:
        client: An initialised KeycloakClient instance.
        db: A SQLAlchemy session (or compatible query interface).

    Returns:
        A summary dict with keys ``created``, ``skipped``, and ``errors``.
        ``errors`` is a list of (email, error_message) tuples.

    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 12.1
    """
    created = 0
    skipped = 0
    errors: list[tuple[str, str]] = []

    users = db.query(User).all()

    for user in users:
        try:
            if client.user_exists(user.email):
                # Leave existing role unchanged (Req 4.3)
                skipped += 1
                continue

            # Create user in Keycloak (Req 4.1)
            uid = client.create_user(user.email)
            # Assign default role to new user (Req 4.4, 12.1)
            client.assign_realm_role(uid, DEFAULT_ROLE)
            created += 1

        except KeycloakUnavailable as exc:
            # Record error and continue with next user (Req 4.5)
            errors.append((user.email, str(exc)))
            logger.warning(
                "Keycloak sync failed for %s: %s", user.email, exc
            )

    summary = {
        "created": created,
        "skipped": skipped,
        "errors": errors,
    }
    logger.info("Keycloak sync summary: %s", summary)
    return summary


def _run_sync() -> None:
    """Execute the sync operation using a fresh DB session and KeycloakClient."""
    client = KeycloakClient()

    if not client.is_enabled():
        print("⚠️  Keycloak is disabled (KEYCLOAK_ENABLED != 'True'). Nothing to sync.")
        return

    db = SessionLocal()
    try:
        summary = sync_users(client, db)
    finally:
        db.close()

    print()
    print("=" * 60)
    print("Keycloak User Synchronization - Summary")
    print("=" * 60)
    print(f"  Created:  {summary['created']}")
    print(f"  Skipped:  {summary['skipped']}")
    print(f"  Errors:   {len(summary['errors'])}")
    print("=" * 60)

    if summary["errors"]:
        print()
        print("Errors:")
        for email, msg in summary["errors"]:
            print(f"  ❌ {email}: {msg}")


if __name__ == "__main__":
    print("=" * 60)
    print("Sentra - Keycloak Role Sync Service")
    print("=" * 60)
    print()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python role_sync.py sync    - Sync all RDS users to Keycloak")
        print()
        print("Description:")
        print("  Creates Keycloak records for authorized RDS users that don't")
        print("  already exist in Keycloak. New users get the default role")
        print("  (viewer_without_query). Existing users are left unchanged.")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "sync":
        _run_sync()
    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: sync")
        sys.exit(1)
