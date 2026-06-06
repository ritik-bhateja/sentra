"""Role definitions for Keycloak RBAC integration.

Defines the three Sentra roles, their priority ordering, and helper functions
for role resolution and validation. Keycloak is the role authority; this module
provides the vocabulary and logic used throughout the backend.
"""

from enum import Enum


class Role(str, Enum):
    """Sentra application roles.

    Inherits from str so values serialize directly into JWT claims and compare
    cleanly against Keycloak realm-role name strings.
    """

    ADMIN = "admin"
    VIEWER_WITH_QUERY = "viewer_with_query"
    VIEWER_WITHOUT_QUERY = "viewer_without_query"


# Least-privilege default — assigned when no explicit role is found (Req 10.1).
DEFAULT_ROLE = Role.VIEWER_WITHOUT_QUERY

# Most-privileged first. Used for selection when multiple roles are present.
ROLE_PRIORITY: list[Role] = [
    Role.ADMIN,
    Role.VIEWER_WITH_QUERY,
    Role.VIEWER_WITHOUT_QUERY,
]


def select_most_privileged(role_names: list[str]) -> Role:
    """Pick the highest-priority Sentra role from a list of role-name strings.

    Ignores non-Sentra role names (noise from Keycloak realm roles that aren't
    ours). Returns DEFAULT_ROLE if no recognized Sentra role is present.

    The result is invariant under permutation or duplication of the input list.

    Requirements: 5.2, 5.3, 5.5, 10.2
    """
    present = set(role_names)
    for role in ROLE_PRIORITY:
        if role.value in present:
            return role
    return DEFAULT_ROLE


def coerce_role(value: str | None) -> Role:
    """Validate an arbitrary string (e.g. a JWT claim) into a Role.

    Returns the exact Role for valid inputs. Returns DEFAULT_ROLE for None,
    empty strings, or any string that isn't one of the three Sentra role values.

    Requirements: 6.3, 7.1, 7.4, 12.2
    """
    try:
        return Role(value)
    except (ValueError, TypeError):
        return DEFAULT_ROLE


def can_view_query(role: Role) -> bool:
    """Return True if the role is permitted to see the executed SQL query.

    Only admin and viewer_with_query may see query_executed.

    Requirements: 8.1, 8.2, 8.3, 10.3
    """
    return role in (Role.ADMIN, Role.VIEWER_WITH_QUERY)
