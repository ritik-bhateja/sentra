"""Keycloak Admin REST API client for RBAC role resolution.

This module provides a thin client over the Keycloak Admin REST API using the
``requests`` library (already a project dependency). It handles:

- Service-account token acquisition via client credentials grant (with caching)
- User lookup by email
- Realm-role mapping retrieval
- User creation and role assignment (for sync operations)

A top-level ``resolve_role_for_email`` function wraps the client and implements
the graceful-degradation contract: if Keycloak is disabled or unreachable the
caller always gets DEFAULT_ROLE rather than an exception.

Requirements: 2.4, 2.5, 4.1, 5.1, 5.2, 5.3, 5.4, 12.4
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import requests

from .roles import DEFAULT_ROLE, Role, select_most_privileged

logger = logging.getLogger(__name__)


class KeycloakUnavailable(Exception):
    """Raised when Keycloak cannot be reached or returns an unexpected error.

    Callers catch this to degrade gracefully to DEFAULT_ROLE (Req 5.4).
    """


class KeycloakClient:
    """Thin wrapper around the Keycloak Admin REST API.

    Reads configuration from environment variables:
    - KEYCLOAK_URL: Base URL of the Keycloak server
    - KEYCLOAK_REALM: Realm name (Sentra_Realm)
    - KEYCLOAK_CLIENT_ID: Confidential client id for the backend service account
    - KEYCLOAK_CLIENT_SECRET: Client secret for the service account
    - KEYCLOAK_ENABLED: Kill-switch ("True" to enable, anything else disables)

    Requirements: 2.4, 2.5
    """

    def __init__(self) -> None:
        self.base_url: str = os.getenv("KEYCLOAK_URL", "")
        self.realm: str = os.getenv("KEYCLOAK_REALM", "")
        self.client_id: str = os.getenv("KEYCLOAK_CLIENT_ID", "")
        self.client_secret: str = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
        self.enabled: bool = os.getenv("KEYCLOAK_ENABLED", "False") == "True"

        # Cached service-account token and its expiry (epoch seconds).
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

        # Timeout for all HTTP requests to Keycloak (seconds).
        self._timeout: float = 10.0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def is_enabled(self) -> bool:
        """Return True if Keycloak integration is active (kill-switch check)."""
        return self.enabled

    def get_realm_roles_for_email(self, email: str) -> list[str]:
        """Return the realm-role names assigned to the user identified by *email*.

        Returns an empty list if the user exists but has no realm roles, or if
        the user does not exist in Keycloak.

        Raises:
            KeycloakUnavailable: on transport/HTTP errors so callers can default.

        Requirements: 5.1, 5.2, 5.3
        """
        user_id = self._find_user_id_by_email(email)
        if user_id is None:
            return []

        url = (
            f"{self.base_url}/admin/realms/{self.realm}"
            f"/users/{user_id}/role-mappings/realm"
        )
        resp = self._authed_request("GET", url)
        # Each entry is a role representation dict with at minimum a "name" key.
        return [role_rep["name"] for role_rep in resp.json()]

    def user_exists(self, email: str) -> bool:
        """Return True if a user with the given email exists in the realm."""
        return self._find_user_id_by_email(email) is not None

    def create_user(self, email: str) -> str:
        """Create a new user in the realm with the given email.

        Returns the Keycloak user ID of the newly created user.

        Raises:
            KeycloakUnavailable: on transport/HTTP errors.

        Requirements: 4.1
        """
        url = f"{self.base_url}/admin/realms/{self.realm}/users"
        username = email.split("@")[0] if "@" in email else email
        payload = {
            "username": username,
            "email": email,
            "enabled": True,
        }
        resp = self._authed_request("POST", url, json=payload)

        # On success Keycloak returns 201 with the user location in the header.
        if resp.status_code == 201:
            location = resp.headers.get("Location", "")
            # Location format: .../users/{user_id}
            user_id = location.rsplit("/", 1)[-1] if location else ""
            if user_id:
                return user_id
            # Fallback: look up the user we just created.
            found_id = self._find_user_id_by_email(email)
            if found_id:
                return found_id
            raise KeycloakUnavailable(
                f"User created but could not determine ID for {email}"
            )

        # 409 means user already exists — treat as success, look up ID.
        if resp.status_code == 409:
            found_id = self._find_user_id_by_email(email)
            if found_id:
                return found_id
            raise KeycloakUnavailable(
                f"User reported as existing but not found: {email}"
            )

        raise KeycloakUnavailable(
            f"Failed to create user {email}: {resp.status_code} {resp.text}"
        )

    def assign_realm_role(self, user_id: str, role: Role) -> None:
        """Assign a realm role to the user identified by *user_id*.

        Fetches the role representation first, then posts it to the user's
        realm-role-mappings.

        Raises:
            KeycloakUnavailable: on transport/HTTP errors.
        """
        # Step 1: Get the role representation from the realm.
        role_rep = self._get_role_representation(role.value)

        # Step 2: Assign the role to the user.
        url = (
            f"{self.base_url}/admin/realms/{self.realm}"
            f"/users/{user_id}/role-mappings/realm"
        )
        resp = self._authed_request("POST", url, json=[role_rep])
        if resp.status_code not in (200, 204):
            raise KeycloakUnavailable(
                f"Failed to assign role {role.value} to user {user_id}: "
                f"{resp.status_code} {resp.text}"
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _service_token(self) -> str:
        """Obtain (or return cached) service-account access token.

        Uses the client credentials grant. Caches the token until 30 seconds
        before its stated expiry to avoid using an about-to-expire token.

        Raises:
            KeycloakUnavailable: if the token endpoint is unreachable or returns
            a non-200 response.
        """
        now = time.time()
        if self._token and now < self._token_expires_at:
            return self._token

        url = (
            f"{self.base_url}/realms/{self.realm}"
            f"/protocol/openid-connect/token"
        )
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        try:
            resp = requests.post(url, data=data, timeout=self._timeout)
        except requests.RequestException as exc:
            raise KeycloakUnavailable(
                f"Token request failed: {exc}"
            ) from exc

        if resp.status_code != 200:
            raise KeycloakUnavailable(
                f"Token endpoint returned {resp.status_code}: {resp.text}"
            )

        body = resp.json()
        self._token = body["access_token"]
        # Cache until 30s before expiry (or 60s if expires_in not present).
        expires_in = body.get("expires_in", 60)
        self._token_expires_at = now + max(expires_in - 30, 0)
        return self._token

    def _authed_request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> requests.Response:
        """Make an authenticated request to the Keycloak Admin REST API.

        Injects the Bearer token and handles transport errors uniformly.

        Raises:
            KeycloakUnavailable: on transport errors or unexpected HTTP status.
        """
        token = self._service_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        headers.setdefault("Content-Type", "application/json")
        kwargs["headers"] = headers
        kwargs.setdefault("timeout", self._timeout)

        try:
            resp = requests.request(method, url, **kwargs)
        except requests.RequestException as exc:
            raise KeycloakUnavailable(
                f"{method} {url} failed: {exc}"
            ) from exc

        # 4xx/5xx that aren't handled by the caller → raise.
        if resp.status_code >= 500:
            raise KeycloakUnavailable(
                f"{method} {url} returned {resp.status_code}: {resp.text}"
            )

        return resp

    def _find_user_id_by_email(self, email: str) -> Optional[str]:
        """Look up a user by exact email match. Returns user ID or None.

        Raises:
            KeycloakUnavailable: on transport/HTTP errors.
        """
        url = (
            f"{self.base_url}/admin/realms/{self.realm}/users"
        )
        resp = self._authed_request("GET", url, params={"email": email, "exact": "true"})
        if resp.status_code != 200:
            raise KeycloakUnavailable(
                f"User lookup for {email} failed: {resp.status_code} {resp.text}"
            )
        users = resp.json()
        if not users:
            return None
        return users[0]["id"]

    def _get_role_representation(self, role_name: str) -> dict:
        """Fetch the full role representation object for a realm role by name.

        Raises:
            KeycloakUnavailable: if the role is not found or request fails.
        """
        url = f"{self.base_url}/admin/realms/{self.realm}/roles/{role_name}"
        resp = self._authed_request("GET", url)
        if resp.status_code != 200:
            raise KeycloakUnavailable(
                f"Role '{role_name}' not found: {resp.status_code} {resp.text}"
            )
        return resp.json()


# ------------------------------------------------------------------
# Module-level convenience
# ------------------------------------------------------------------

def resolve_role_for_email(email: str, client: KeycloakClient) -> Role:
    """Resolve a user's effective Sentra role from Keycloak.

    Graceful degradation contract:
    - If Keycloak is disabled (kill-switch) → DEFAULT_ROLE, no network call.
    - If Keycloak is unreachable or errors → DEFAULT_ROLE, logged warning.
    - Otherwise → select_most_privileged over the user's realm roles.

    Requirements: 5.1, 5.2, 5.3, 5.4, 12.4
    """
    if not client.is_enabled():
        return DEFAULT_ROLE

    try:
        role_names = client.get_realm_roles_for_email(email)
    except KeycloakUnavailable as exc:
        logger.warning(
            "Keycloak role lookup failed for %s: %s", email, exc
        )
        return DEFAULT_ROLE

    return select_most_privileged(role_names)
