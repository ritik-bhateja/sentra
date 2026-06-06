"""Property-based tests for auth/rbac.py.

Property 4: Query visibility filtering by role
Property 5: Live and stored responses are filtered identically

Uses Hypothesis to generate arbitrary payloads and verify that filtering
behaves correctly for all roles and payload shapes.
"""

import sys
import os

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

# Ensure BackendAPI is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from auth.roles import Role, DEFAULT_ROLE
from auth.rbac import (
    QUERY_FIELD,
    filter_response_for_role,
    filter_messages_for_role,
)

# --------------------------------------------------------------------------
# Strategies
# --------------------------------------------------------------------------

# Arbitrary JSON-like values (not dicts, for testing passthrough)
non_dict_values = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False),
    st.text(max_size=50),
    st.lists(st.integers(), max_size=5),
)

# Arbitrary dict keys (excluding query_executed so we can control its presence)
safe_keys = st.text(min_size=1, max_size=20).filter(lambda k: k != QUERY_FIELD)

# Arbitrary JSON-serializable values for dict entries
json_values = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False),
    st.text(max_size=50),
    st.lists(st.integers(), max_size=3),
)

# A dict payload WITHOUT query_executed
payload_without_query = st.dictionaries(
    keys=safe_keys,
    values=json_values,
    min_size=0,
    max_size=10,
)

# A dict payload WITH query_executed
payload_with_query = st.builds(
    lambda base, qval: {**base, QUERY_FIELD: qval},
    base=payload_without_query,
    qval=st.text(min_size=1, max_size=100),  # SQL-like string
)

# Any dict payload (with or without query_executed)
any_payload = st.one_of(payload_without_query, payload_with_query)

# All role values
all_roles = st.sampled_from(list(Role))

# Roles that can view queries
privileged_roles = st.sampled_from([Role.ADMIN, Role.VIEWER_WITH_QUERY])

# The role that cannot view queries
restricted_role = st.just(Role.VIEWER_WITHOUT_QUERY)


# --------------------------------------------------------------------------
# Property 4: Query visibility filtering by role
# Validates: Requirements 8.1, 8.2, 8.3, 10.3
# --------------------------------------------------------------------------


class TestQueryVisibilityFiltering:
    """Property 4: filter_response_for_role correctly controls query_executed
    visibility based on the user's role."""

    @given(payload=payload_with_query, role=privileged_roles)
    @settings(max_examples=300)
    def test_privileged_roles_see_full_payload(self, payload: dict, role: Role):
        """Admin and viewer_with_query see the full payload including
        query_executed (Req 8.2, 8.3)."""
        result = filter_response_for_role(payload, role)
        assert QUERY_FIELD in result
        assert result[QUERY_FIELD] == payload[QUERY_FIELD]
        # All other fields preserved
        for key in payload:
            assert key in result
            assert result[key] == payload[key]

    @given(payload=payload_with_query, role=restricted_role)
    @settings(max_examples=300)
    def test_viewer_without_query_never_sees_query_executed(
        self, payload: dict, role: Role
    ):
        """viewer_without_query never sees query_executed (Req 8.1, 10.3)."""
        result = filter_response_for_role(payload, role)
        assert QUERY_FIELD not in result

    @given(payload=payload_with_query, role=restricted_role)
    @settings(max_examples=300)
    def test_other_fields_preserved_for_restricted_role(
        self, payload: dict, role: Role
    ):
        """All fields except query_executed are preserved for
        viewer_without_query."""
        result = filter_response_for_role(payload, role)
        for key, value in payload.items():
            if key == QUERY_FIELD:
                continue
            assert key in result
            assert result[key] == value

    @given(payload=payload_without_query, role=all_roles)
    @settings(max_examples=300)
    def test_no_query_field_passes_through_for_all_roles(
        self, payload: dict, role: Role
    ):
        """When query_executed is absent, all roles see the same payload."""
        result = filter_response_for_role(payload, role)
        assert QUERY_FIELD not in result
        assert result == payload

    @given(value=non_dict_values, role=all_roles)
    @settings(max_examples=200)
    def test_non_dict_inputs_pass_through(self, value, role: Role):
        """Non-dict inputs are returned unchanged regardless of role."""
        result = filter_response_for_role(value, role)
        assert result is value

    @given(payload=payload_with_query, role=restricted_role)
    @settings(max_examples=200)
    def test_input_not_mutated(self, payload: dict, role: Role):
        """Filtering never mutates the original payload."""
        original_keys = set(payload.keys())
        original_query_value = payload[QUERY_FIELD]
        filter_response_for_role(payload, role)
        # Original payload unchanged
        assert set(payload.keys()) == original_keys
        assert payload[QUERY_FIELD] == original_query_value

    def test_explicit_role_examples(self):
        """Concrete examples for each role."""
        payload = {
            "type": "text",
            "data": "42",
            "explanation": "count result",
            "query_executed": "SELECT COUNT(*) FROM policies",
        }

        # Admin sees everything
        result = filter_response_for_role(payload, Role.ADMIN)
        assert result == payload

        # viewer_with_query sees everything
        result = filter_response_for_role(payload, Role.VIEWER_WITH_QUERY)
        assert result == payload

        # viewer_without_query does not see query_executed
        result = filter_response_for_role(payload, Role.VIEWER_WITHOUT_QUERY)
        assert QUERY_FIELD not in result
        assert result["type"] == "text"
        assert result["data"] == "42"
        assert result["explanation"] == "count result"


# --------------------------------------------------------------------------
# Property 5: Live and stored responses are filtered identically
# Validates: Requirements 8.5
# --------------------------------------------------------------------------


class TestLiveStoredFilteringEquivalence:
    """Property 5: Applying filter_response_for_role directly produces the same
    query_executed visibility as going through filter_messages_for_role (the
    stored-history path)."""

    @given(payload=any_payload, role=all_roles)
    @settings(max_examples=500)
    def test_live_vs_stored_equivalence(self, payload: dict, role: Role):
        """The live filtering path and the stored-message filtering path
        produce identical query_executed visibility."""
        # Live path: filter_response_for_role directly
        live_result = filter_response_for_role(payload, role)

        # Stored path: wrap in a bot message and filter via filter_messages_for_role
        bot_message = {"type": "bot", "content": payload, "timestamp": 12345}
        stored_results = filter_messages_for_role([bot_message], role)
        stored_content = stored_results[0]["content"]

        # Same query_executed visibility
        assert (QUERY_FIELD in live_result) == (QUERY_FIELD in stored_content)

        # If query_executed is visible, values match
        if QUERY_FIELD in live_result:
            assert live_result[QUERY_FIELD] == stored_content[QUERY_FIELD]

    @given(payload=any_payload, role=all_roles)
    @settings(max_examples=300)
    def test_all_non_query_fields_match(self, payload: dict, role: Role):
        """All fields other than query_executed are identical between the
        live and stored filtering paths."""
        live_result = filter_response_for_role(payload, role)
        bot_message = {"type": "bot", "content": payload, "timestamp": 12345}
        stored_results = filter_messages_for_role([bot_message], role)
        stored_content = stored_results[0]["content"]

        # All non-query fields identical
        for key in payload:
            if key == QUERY_FIELD:
                continue
            assert key in live_result
            assert key in stored_content
            assert live_result[key] == stored_content[key]

    @given(role=all_roles)
    @settings(max_examples=50)
    def test_user_messages_pass_through_unfiltered(self, role: Role):
        """User messages (non-dict content) are never filtered."""
        messages = [
            {"type": "user", "content": "How many policies?", "timestamp": 1},
            {
                "type": "bot",
                "content": {
                    "type": "text",
                    "data": "150",
                    "query_executed": "SELECT COUNT(*)",
                },
                "timestamp": 2,
            },
            {"type": "user", "content": "Show by type", "timestamp": 3},
        ]
        result = filter_messages_for_role(messages, role)

        # User messages unchanged
        assert result[0] == messages[0]
        assert result[2] == messages[2]

    @given(role=all_roles)
    @settings(max_examples=50)
    def test_messages_list_not_mutated(self, role: Role):
        """filter_messages_for_role never mutates the input list."""
        original_msg = {
            "type": "bot",
            "content": {"data": "x", "query_executed": "SELECT 1"},
            "timestamp": 1,
        }
        messages = [original_msg]
        filter_messages_for_role(messages, role)

        # Original list and message unchanged
        assert len(messages) == 1
        assert messages[0] is original_msg
        assert "query_executed" in messages[0]["content"]

    def test_empty_messages_list(self):
        """An empty messages list returns an empty list."""
        for role in Role:
            assert filter_messages_for_role([], role) == []

    def test_mixed_message_types(self):
        """Mixed message list with various content types is handled correctly."""
        messages = [
            {"type": "user", "content": "hello", "timestamp": 1},
            {"type": "bot", "content": {"data": "hi"}, "timestamp": 2},
            {"type": "bot", "content": "plain string bot", "timestamp": 3},
            {
                "type": "bot",
                "content": {"data": "42", "query_executed": "SELECT 42"},
                "timestamp": 4,
            },
            {"type": "system", "content": None, "timestamp": 5},
        ]

        result = filter_messages_for_role(messages, Role.VIEWER_WITHOUT_QUERY)

        # User message unchanged
        assert result[0]["content"] == "hello"
        # Bot with dict but no query_executed unchanged
        assert result[1]["content"] == {"data": "hi"}
        # Bot with string content unchanged
        assert result[2]["content"] == "plain string bot"
        # Bot with query_executed has it stripped
        assert "query_executed" not in result[3]["content"]
        assert result[3]["content"]["data"] == "42"
        # System message unchanged
        assert result[4]["content"] is None
