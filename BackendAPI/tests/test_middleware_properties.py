"""Property-based tests for auth/middleware.py.

Property 9: Non-admin roles are denied admin operations

Tests the require_admin dependency function to verify that only admin-role
users pass through, while all other roles receive HTTP 403 Forbidden.
"""

import sys
import os
import asyncio
from unittest.mock import MagicMock
from types import SimpleNamespace

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Ensure BackendAPI is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from auth.roles import Role, DEFAULT_ROLE, coerce_role
from auth.middleware import require_admin
from fastapi import HTTPException


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _make_user_with_role(role: Role) -> MagicMock:
    """Create a mock User object with a role attribute set."""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    user.role = role
    return user


def _run_async(coro):
    """Run an async coroutine synchronously for testing."""
    return asyncio.get_event_loop().run_until_complete(coro)


# --------------------------------------------------------------------------
# Property 9: Non-admin roles are denied admin operations
# Validates: Requirements 9.2, 9.3, 9.5, 10.4
# --------------------------------------------------------------------------


class TestRequireAdminEnforcement:
    """Property 9: require_admin grants access only to admin role and denies
    all other roles with HTTP 403."""

    def test_admin_role_passes_through(self):
        """Admin users are returned without raising an exception (Req 9.2)."""
        admin_user = _make_user_with_role(Role.ADMIN)
        result = _run_async(require_admin(current_user=admin_user))
        assert result is admin_user
        assert result.role == Role.ADMIN

    def test_viewer_with_query_is_denied(self):
        """viewer_with_query receives HTTP 403 (Req 9.3)."""
        user = _make_user_with_role(Role.VIEWER_WITH_QUERY)
        with pytest.raises(HTTPException) as exc_info:
            _run_async(require_admin(current_user=user))
        assert exc_info.value.status_code == 403
        assert "Admin privileges required" in exc_info.value.detail

    def test_viewer_without_query_is_denied(self):
        """viewer_without_query receives HTTP 403 (Req 9.3, 10.4)."""
        user = _make_user_with_role(Role.VIEWER_WITHOUT_QUERY)
        with pytest.raises(HTTPException) as exc_info:
            _run_async(require_admin(current_user=user))
        assert exc_info.value.status_code == 403
        assert "Admin privileges required" in exc_info.value.detail

    def test_default_role_is_denied(self):
        """The default role (viewer_without_query) is denied (Req 10.4)."""
        user = _make_user_with_role(DEFAULT_ROLE)
        with pytest.raises(HTTPException) as exc_info:
            _run_async(require_admin(current_user=user))
        assert exc_info.value.status_code == 403

    @pytest.mark.parametrize("role", [r for r in Role if r != Role.ADMIN])
    def test_all_non_admin_roles_denied(self, role: Role):
        """Every non-admin Role enum value is denied with 403 (Req 9.3, 9.5)."""
        user = _make_user_with_role(role)
        with pytest.raises(HTTPException) as exc_info:
            _run_async(require_admin(current_user=user))
        assert exc_info.value.status_code == 403

    @pytest.mark.parametrize("role", list(Role))
    def test_admin_is_only_role_that_passes(self, role: Role):
        """Only admin passes; all others raise (exhaustive over enum)."""
        user = _make_user_with_role(role)
        if role == Role.ADMIN:
            result = _run_async(require_admin(current_user=user))
            assert result is user
        else:
            with pytest.raises(HTTPException) as exc_info:
                _run_async(require_admin(current_user=user))
            assert exc_info.value.status_code == 403

    @given(role_value=st.sampled_from([r.value for r in Role]))
    @settings(max_examples=50)
    def test_property_coerced_roles_enforce_correctly(self, role_value: str):
        """Property: for any valid role string, require_admin grants access
        only when the coerced role is admin."""
        role = coerce_role(role_value)
        user = _make_user_with_role(role)

        if role == Role.ADMIN:
            result = _run_async(require_admin(current_user=user))
            assert result is user
        else:
            with pytest.raises(HTTPException) as exc_info:
                _run_async(require_admin(current_user=user))
            assert exc_info.value.status_code == 403

    @given(role_value=st.text(min_size=0, max_size=50))
    @settings(max_examples=200)
    def test_property_arbitrary_strings_coerced_then_enforced(self, role_value: str):
        """Property: for any arbitrary string coerced to a role, only 'admin'
        passes the admin guard. All invalid strings default to
        viewer_without_query and are denied."""
        role = coerce_role(role_value)
        user = _make_user_with_role(role)

        if role == Role.ADMIN:
            result = _run_async(require_admin(current_user=user))
            assert result is user
        else:
            with pytest.raises(HTTPException) as exc_info:
                _run_async(require_admin(current_user=user))
            assert exc_info.value.status_code == 403

    def test_403_response_includes_descriptive_message(self):
        """The 403 response detail is descriptive (Req 9.4)."""
        user = _make_user_with_role(Role.VIEWER_WITH_QUERY)
        with pytest.raises(HTTPException) as exc_info:
            _run_async(require_admin(current_user=user))
        detail = exc_info.value.detail
        assert isinstance(detail, str)
        assert len(detail) > 0
        # Verify it communicates what went wrong
        assert "admin" in detail.lower() or "privilege" in detail.lower()
