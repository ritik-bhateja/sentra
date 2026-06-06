"""Property-based tests for auth/keycloak_client.py.

Property 10: Disabled Keycloak always yields the default role without a network call.

Uses Hypothesis to generate arbitrary emails and verifies that when
KEYCLOAK_ENABLED is not "True", resolve_role_for_email returns DEFAULT_ROLE
and never issues any HTTP request to Keycloak.

Validates: Requirements 12.4
"""

import sys
import os
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Ensure BackendAPI is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from auth.roles import DEFAULT_ROLE
from auth.keycloak_client import KeycloakClient, resolve_role_for_email


# --------------------------------------------------------------------------
# Strategies
# --------------------------------------------------------------------------

# Arbitrary email-like strings (valid and invalid formats)
email_strategy = st.one_of(
    # Standard email format
    st.from_regex(r"[a-z0-9]{1,20}@[a-z]{1,10}\.[a-z]{2,4}", fullmatch=True),
    # Arbitrary text (including empty, unicode, special chars)
    st.text(min_size=0, max_size=100),
)


# --------------------------------------------------------------------------
# Property 10: Disabled Keycloak always yields the default role
# Validates: Requirements 12.4
# --------------------------------------------------------------------------


class TestDisabledKeycloakDefaultsRole:
    """Property 10: When KEYCLOAK_ENABLED is not 'True', resolve_role_for_email
    returns DEFAULT_ROLE for any email, and no network call is made."""

    @given(email=email_strategy)
    @settings(max_examples=300)
    def test_disabled_returns_default_role(self, email: str):
        """For any email, a disabled KeycloakClient returns DEFAULT_ROLE."""
        client = KeycloakClient()
        # Ensure client is disabled regardless of environment
        client.enabled = False

        result = resolve_role_for_email(email, client)
        assert result == DEFAULT_ROLE

    @given(email=email_strategy)
    @settings(max_examples=300)
    @patch("auth.keycloak_client.requests")
    def test_disabled_makes_no_network_call(self, mock_requests, email: str):
        """For any email, a disabled KeycloakClient makes zero HTTP requests."""
        client = KeycloakClient()
        client.enabled = False

        resolve_role_for_email(email, client)

        # Verify no HTTP methods were called
        mock_requests.post.assert_not_called()
        mock_requests.get.assert_not_called()
        mock_requests.request.assert_not_called()

    @given(email=email_strategy)
    @settings(max_examples=200)
    def test_disabled_via_env_false(self, email: str):
        """KEYCLOAK_ENABLED='False' (explicit) yields default role."""
        with patch.dict(os.environ, {"KEYCLOAK_ENABLED": "False"}):
            client = KeycloakClient()
            assert not client.is_enabled()
            result = resolve_role_for_email(email, client)
            assert result == DEFAULT_ROLE

    @given(email=email_strategy)
    @settings(max_examples=200)
    def test_disabled_via_env_missing(self, email: str):
        """KEYCLOAK_ENABLED not set (missing) yields default role."""
        env = os.environ.copy()
        env.pop("KEYCLOAK_ENABLED", None)
        with patch.dict(os.environ, env, clear=True):
            client = KeycloakClient()
            assert not client.is_enabled()
            result = resolve_role_for_email(email, client)
            assert result == DEFAULT_ROLE

    @given(
        email=email_strategy,
        env_value=st.text(min_size=0, max_size=20).filter(lambda s: s != "True" and "\x00" not in s),
    )
    @settings(max_examples=300)
    def test_disabled_for_any_non_true_value(self, email: str, env_value: str):
        """Any KEYCLOAK_ENABLED value other than exactly 'True' disables."""
        with patch.dict(os.environ, {"KEYCLOAK_ENABLED": env_value}):
            client = KeycloakClient()
            assert not client.is_enabled()
            result = resolve_role_for_email(email, client)
            assert result == DEFAULT_ROLE

    def test_disabled_client_is_enabled_returns_false(self):
        """Explicit check that is_enabled() returns False when disabled."""
        client = KeycloakClient()
        client.enabled = False
        assert client.is_enabled() is False

    def test_enabled_client_is_enabled_returns_true(self):
        """Explicit check that is_enabled() returns True when enabled."""
        client = KeycloakClient()
        client.enabled = True
        assert client.is_enabled() is True

    @patch("auth.keycloak_client.requests")
    def test_disabled_with_configured_url_still_no_call(self, mock_requests):
        """Even with a valid-looking URL configured, disabled means no call."""
        client = KeycloakClient()
        client.enabled = False
        client.base_url = "http://keycloak.example.com:8080"
        client.realm = "sentra"
        client.client_id = "sentra-backend"
        client.client_secret = "secret"

        result = resolve_role_for_email("admin@company.com", client)

        assert result == DEFAULT_ROLE
        mock_requests.post.assert_not_called()
        mock_requests.get.assert_not_called()
        mock_requests.request.assert_not_called()
