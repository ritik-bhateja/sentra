"""Response filtering based on user role (RBAC enforcement).

Provides server-side authoritative filtering of the `query_executed` field
from assistant responses. Filtering is applied at read-time — stored data is
never mutated. This ensures a role change takes effect immediately on existing
history without requiring a data migration.

The same filtering logic is applied to both live /query responses and stored
conversation history, guaranteeing identical query visibility regardless of
the response path (Requirements 8.5).

Requirements: 8.1, 8.2, 8.3, 8.5, 10.3
"""

from auth.roles import Role, can_view_query

QUERY_FIELD = "query_executed"


def filter_response_for_role(payload: dict, role: Role) -> dict:
    """Return a filtered copy of an assistant response based on the user's role.

    - For admin and viewer_with_query: returns the payload unchanged (including
      query_executed if present). Requirements 8.2, 8.3.
    - For viewer_without_query: returns a copy with query_executed removed.
      Requirement 8.1, 10.3.

    Non-dict inputs pass through unchanged. Missing query_executed fields are
    a no-op (the response simply doesn't have one).

    This function never mutates the input payload.
    """
    if not isinstance(payload, dict):
        return payload
    if can_view_query(role):
        return payload
    if QUERY_FIELD not in payload:
        return payload
    # Return a shallow copy without query_executed
    cleaned = {k: v for k, v in payload.items() if k != QUERY_FIELD}
    return cleaned


def filter_messages_for_role(messages: list, role: Role) -> list:
    """Apply query-visibility filtering to message-format outputs.

    Processes a list of messages (as returned by to_message_format or session
    endpoints). Only bot messages with dict content are filtered; all other
    messages pass through unchanged.

    This function never mutates the input list or any message dict within it.

    Requirements: 8.5
    """
    out = []
    for m in messages:
        if isinstance(m, dict) and isinstance(m.get("content"), dict):
            filtered_content = filter_response_for_role(m["content"], role)
            if filtered_content is not m["content"]:
                m = {**m, "content": filtered_content}
        out.append(m)
    return out
