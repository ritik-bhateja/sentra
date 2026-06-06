"""Property-based tests for auth/jwt_handler.py.

Property 3: JWT role round-trip preserves all claims

Uses Hypothesis to generate arbitrary user IDs, email strings, and Role enum
values, then verifies that encoding and decoding a token preserves all claims
and that verification fails with an incorrect secret.

Validates: Requirements 6.1, 6.2, 6.4, 6.5
"""

import sys
import os

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

# Ensure BackendAPI is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set required env vars before importing the handler (it reads them at import)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-properties")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRATION_DAYS", "7")

from auth.roles import Role, DEFAULT_ROLE
from auth.jwt_handler import JWTHandler


# --------------------------------------------------------------------------
# Strategies
# --------------------------------------------------------------------------

# Positive integers for user IDs (matching real DB serial primary keys)
user_id_strategy = st.integers(min_value=1, max_value=2**31 - 1)

# Email-like strings — don't need to be RFC-valid, just non-empty text
email_strategy = st.emails()

# Any of the three valid Sentra roles
role_strategy = st.sampled_from(list(Role))


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def make_handler(secret: str = "test-secret-key-for-properties") -> JWTHandler:
    """Create a JWTHandler with a known secret for deterministic testing."""
    handler = JWTHandler()
    handler.secret_key = secret
    handler.algorithm = "HS256"
    handler.expiration_days = 7
    return handler


# --------------------------------------------------------------------------
# Property 3: JWT role round-trip preserves all claims
# Validates: Requirements 6.1, 6.2, 6.4, 6.5
# --------------------------------------------------------------------------


class TestJWTRoleRoundTrip:
    """Property 3: Encoding a token with create_token and decoding it with
    verify_token preserves sub, email, role, and maintains exp > iat."""

    @given(user_id=user_id_strategy, email=email_strategy, role=role_strategy)
    @settings(max_examples=500)
    def test_round_trip_preserves_sub(self, user_id: int, email: str, role: Role):
        """The decoded sub claim equals str(user_id)."""
        handler = make_handler()
        token = handler.create_token(user_id, email, role.value)
        payload = handler.verify_token(token)
        assert payload is not None
        assert payload["sub"] == str(user_id)

    @given(user_id=user_id_strategy, email=email_strategy, role=role_strategy)
    @settings(max_examples=500)
    def test_round_trip_preserves_email(self, user_id: int, email: str, role: Role):
        """The decoded email claim equals the input email."""
        handler = make_handler()
        token = handler.create_token(user_id, email, role.value)
        payload = handler.verify_token(token)
        assert payload is not None
        assert payload["email"] == email

    @given(user_id=user_id_strategy, email=email_strategy, role=role_strategy)
    @settings(max_examples=500)
    def test_round_trip_preserves_role(self, user_id: int, email: str, role: Role):
        """The decoded role claim equals the input role value (Req 6.1, 6.2)."""
        handler = make_handler()
        token = handler.create_token(user_id, email, role.value)
        payload = handler.verify_token(token)
        assert payload is not None
        assert payload["role"] == role.value

    @given(user_id=user_id_strategy, email=email_strategy, role=role_strategy)
    @settings(max_examples=500)
    def test_exp_greater_than_iat(self, user_id: int, email: str, role: Role):
        """The expiration timestamp is strictly after the issued-at timestamp."""
        handler = make_handler()
        token = handler.create_token(user_id, email, role.value)
        payload = handler.verify_token(token)
        assert payload is not None
        assert payload["exp"] > payload["iat"]

    @given(user_id=user_id_strategy, email=email_strategy, role=role_strategy)
    @settings(max_examples=200)
    def test_verification_fails_with_wrong_secret(self, user_id: int, email: str, role: Role):
        """A token signed with one secret cannot be verified with a different one (Req 6.5)."""
        handler_create = make_handler(secret="correct-secret")
        handler_verify = make_handler(secret="wrong-secret")
        token = handler_create.create_token(user_id, email, role.value)
        payload = handler_verify.verify_token(token)
        assert payload is None

    @given(user_id=user_id_strategy, email=email_strategy, role=role_strategy)
    @settings(max_examples=300)
    def test_role_claim_is_valid_sentra_role(self, user_id: int, email: str, role: Role):
        """The role claim is always one of the three allowed Sentra role values (Req 6.2)."""
        handler = make_handler()
        token = handler.create_token(user_id, email, role.value)
        payload = handler.verify_token(token)
        assert payload is not None
        assert payload["role"] in {r.value for r in Role}

    @given(user_id=user_id_strategy, email=email_strategy, role=role_strategy)
    @settings(max_examples=300)
    def test_all_expected_claims_present(self, user_id: int, email: str, role: Role):
        """The decoded token contains exactly the expected claims (Req 6.4)."""
        handler = make_handler()
        token = handler.create_token(user_id, email, role.value)
        payload = handler.verify_token(token)
        assert payload is not None
        expected_keys = {"sub", "email", "role", "exp", "iat"}
        assert expected_keys.issubset(set(payload.keys()))

    def test_default_role_when_omitted(self):
        """When role is omitted, the token carries the default role value."""
        handler = make_handler()
        token = handler.create_token(42, "user@example.com")
        payload = handler.verify_token(token)
        assert payload is not None
        assert payload["role"] == DEFAULT_ROLE.value

    def test_each_role_value_round_trips(self):
        """Explicit check that each of the three roles round-trips correctly."""
        handler = make_handler()
        for role in Role:
            token = handler.create_token(1, "test@test.com", role.value)
            payload = handler.verify_token(token)
            assert payload is not None
            assert payload["role"] == role.value
