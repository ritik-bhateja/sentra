"""Property-based tests for auth/roles.py.

Property 1: Most-privileged role resolution
Property 2: Missing or invalid role claim defaulting

Uses Hypothesis to generate arbitrary inputs and verify universal correctness
properties hold across all valid (and invalid) inputs.
"""

import sys
import os
from random import shuffle

import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st

# Ensure BackendAPI is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from auth.roles import (
    Role,
    DEFAULT_ROLE,
    ROLE_PRIORITY,
    select_most_privileged,
    coerce_role,
)

# --------------------------------------------------------------------------
# Strategies
# --------------------------------------------------------------------------

VALID_ROLE_NAMES = [r.value for r in Role]

# Arbitrary strings that are NOT valid Sentra role names (noise)
noise_strategy = st.text(min_size=0, max_size=50).filter(
    lambda s: s not in VALID_ROLE_NAMES
)

# A list mixing valid role names, noise, duplicates, and empty strings
role_name_list_strategy = st.lists(
    st.one_of(
        st.sampled_from(VALID_ROLE_NAMES),
        noise_strategy,
        st.just(""),
    ),
    min_size=0,
    max_size=30,
)


# --------------------------------------------------------------------------
# Property 1: Most-privileged role resolution
# Validates: Requirements 3.3, 5.2, 5.3, 5.5, 10.2
# --------------------------------------------------------------------------


class TestMostPrivilegedRoleResolution:
    """Property 1: select_most_privileged returns the correct role for any
    combination of role-name strings, and the result is invariant under
    permutation of the input list."""

    @given(role_names=role_name_list_strategy)
    @settings(max_examples=500)
    def test_returns_admin_if_present(self, role_names: list[str]):
        """If 'admin' is anywhere in the list, result must be admin."""
        if "admin" in role_names:
            assert select_most_privileged(role_names) == Role.ADMIN

    @given(role_names=role_name_list_strategy)
    @settings(max_examples=500)
    def test_returns_viewer_with_query_if_no_admin(self, role_names: list[str]):
        """If 'admin' is absent but 'viewer_with_query' is present, result
        must be viewer_with_query."""
        assume("admin" not in role_names)
        if "viewer_with_query" in role_names:
            assert select_most_privileged(role_names) == Role.VIEWER_WITH_QUERY

    @given(role_names=role_name_list_strategy)
    @settings(max_examples=500)
    def test_returns_default_if_no_sentra_roles(self, role_names: list[str]):
        """If no valid Sentra role names are present, result is DEFAULT_ROLE."""
        assume(not any(name in VALID_ROLE_NAMES for name in role_names))
        assert select_most_privileged(role_names) == DEFAULT_ROLE

    @given(role_names=role_name_list_strategy)
    @settings(max_examples=500)
    def test_invariant_under_permutation(self, role_names: list[str]):
        """Result does not depend on the order of the input list."""
        result_original = select_most_privileged(role_names)
        shuffled = role_names.copy()
        shuffle(shuffled)
        result_shuffled = select_most_privileged(shuffled)
        assert result_original == result_shuffled

    def test_empty_list_returns_default(self):
        """An empty list must return the default role."""
        assert select_most_privileged([]) == DEFAULT_ROLE

    def test_only_noise_returns_default(self):
        """A list with only non-Sentra strings returns default."""
        noise = ["manager", "superuser", "readonly", "", "ADMIN", "Admin"]
        assert select_most_privileged(noise) == DEFAULT_ROLE

    def test_priority_order_respected(self):
        """All three roles present → admin wins."""
        all_roles = ["viewer_without_query", "viewer_with_query", "admin"]
        assert select_most_privileged(all_roles) == Role.ADMIN

    def test_duplicates_do_not_affect_result(self):
        """Duplicates don't change the outcome."""
        duped = ["viewer_with_query"] * 10
        assert select_most_privileged(duped) == Role.VIEWER_WITH_QUERY


# --------------------------------------------------------------------------
# Property 2: Missing or invalid role claim resolves to the default role
# Validates: Requirements 6.3, 7.1, 7.4, 12.2
# --------------------------------------------------------------------------


class TestCoerceRoleDefaulting:
    """Property 2: coerce_role returns DEFAULT_ROLE for invalid/missing inputs
    and the exact Role for valid inputs."""

    @given(value=noise_strategy)
    @settings(max_examples=500)
    def test_invalid_string_returns_default(self, value: str):
        """Any string that is not a valid Sentra role name resolves to default."""
        assert coerce_role(value) == DEFAULT_ROLE

    def test_none_returns_default(self):
        """None (missing claim) resolves to default."""
        assert coerce_role(None) == DEFAULT_ROLE

    def test_empty_string_returns_default(self):
        """Empty string resolves to default."""
        assert coerce_role("") == DEFAULT_ROLE

    @given(role=st.sampled_from(VALID_ROLE_NAMES))
    @settings(max_examples=100)
    def test_valid_role_string_returns_exact_role(self, role: str):
        """A valid Sentra role string returns the exact matching Role enum."""
        result = coerce_role(role)
        assert result == Role(role)
        assert result.value == role

    def test_all_valid_roles_round_trip(self):
        """Each valid role value coerces to itself."""
        for role in Role:
            assert coerce_role(role.value) == role

    @given(value=st.one_of(st.integers(), st.floats(), st.binary()))
    @settings(max_examples=200)
    def test_non_string_types_return_default(self, value):
        """Non-string types (int, float, bytes) resolve to default."""
        assert coerce_role(value) == DEFAULT_ROLE

    def test_case_sensitive_mismatch_returns_default(self):
        """Role matching is case-sensitive — 'Admin' != 'admin'."""
        assert coerce_role("Admin") == DEFAULT_ROLE
        assert coerce_role("ADMIN") == DEFAULT_ROLE
        assert coerce_role("Viewer_With_Query") == DEFAULT_ROLE

    def test_whitespace_variations_return_default(self):
        """Roles with extra whitespace are invalid."""
        assert coerce_role(" admin") == DEFAULT_ROLE
        assert coerce_role("admin ") == DEFAULT_ROLE
        assert coerce_role(" admin ") == DEFAULT_ROLE
