# Design Document

## Overview

This design implements session and user-based memory isolation for the Sentra AI chatbot system. The solution modifies the request flow to pass user and session identifiers from the React frontend through the Flask API layer to the Bedrock AgentCore runtime, ensuring that the Memory Client uses these identifiers to maintain separate conversation contexts for each user and each chat session.

The design leverages the existing frontend session management (localStorage-based) and integrates it with the AWS Bedrock AgentCore Memory system, which already supports actor_id and session_id parameters for memory isolation.

## Architecture

### Current Architecture Issues

```
Frontend (React)
├─ Manages sessions in localStorage
├─ Generates unique session IDs per chat
└─ Sends only user_id to backend
    ↓
Flask API (Agent_Trigger.py)
├─ Receives user_id
└─ Passes only user_query and user_id
    ↓
AgentCore Runtime (main.py)
├─ HARDCODED: actor_id="harsh_kumar"
├─ HARDCODED: session_id="sentra_session"
└─ All users/sessions share same memory context ❌
```

### Proposed Architecture

```
Frontend (React)
├─ Manages sessions in localStorage
├─ Generates unique session IDs per chat
└─ Sends user_id AND session_id to backend ✓
    ↓
Flask API (Agent_Trigger.py)
├─ Receives user_id and session_id
└─ Passes user_query, user_id, AND session_id ✓
    ↓
AgentCore Runtime (main.py)
├─ Extracts user_id → actor_id
├─ Extracts session_id → session_id
└─ Passes to SQLQueryExecutor ✓
    ↓
SQLQueryExecutor (sql_agent.py)
├─ Initializes Agent with dynamic actor_id and session_id
└─ Memory hooks use these IDs for isolation ✓
    ↓
Memory System (memory_hook.py)
├─ Loads history: memory_client.get_last_k_turns(actor_id, session_id)
└─ Saves messages: memory_client.create_event(actor_id, session_id) ✓
```

## Components and Interfaces

### 1. Frontend Component (ChatInterface.jsx)

**Responsibility:** Send session context to backend

**Changes:**
- Modify `handleSubmit` function to include `currentSessionId` in API request
- Ensure `currentSessionId` is available when making requests

**Interface:**
```javascript
// API Request Payload
{
  user_query: string,      // The user's question
  user_id: string,         // User identifier (e.g., "kamaljeet.singh")
  session_id: string       // Session identifier (e.g., "1734012345678")
}
```

### 2. Flask API Layer (Agent_Trigger.py)

**Responsibility:** Extract and forward session identifiers

**Changes:**
- Extract `session_id` from incoming request payload
- Validate presence of both `user_id` and `session_id`
- Return 400 error if either is missing
- Include `session_id` in AgentCore invocation payload

**Interface:**
```python
# Input: Flask request.get_json()
{
  "user_query": str,
  "user_id": str,
  "session_id": str
}

# Output: AgentCore invocation payload
{
  "user_query": str,
  "user_id": str,
  "session_id": str
}

# Error Response (if validation fails)
{
  "error": str,
  "message": str
}
```

### 3. AgentCore Entrypoint (main.py)

**Responsibility:** Initialize SQLQueryExecutor with dynamic identifiers

**Changes:**
- Extract `user_id` and `session_id` from payload
- Validate presence of both identifiers
- Pass as `actor_id` and `session_id` to SQLQueryExecutor
- Return error response if validation fails

**Interface:**
```python
# Input: payload dict
{
  "user_query": str,
  "user_id": str,
  "session_id": str
}

# SQLQueryExecutor initialization
SQLQueryExecutor(
  actor_id=payload["user_id"],
  session_id=payload["session_id"],
  region="ap-south-1",
  model_id="apac.anthropic.claude-sonnet-4-20250514-v1:0"
)
```

### 4. SQLQueryExecutor (sql_agent.py)

**Responsibility:** Pass identifiers to Agent state

**Current State:**
- Already accepts `actor_id` and `session_id` parameters
- Already passes them to Agent state
- No changes required (already designed correctly)

**Interface:**
```python
def __init__(self, actor_id='actor_123', session_id='session_123', ...):
    self.agent = Agent(
        model=self.model,
        system_prompt=system_prompt,
        tools=[athena_query],
        hooks=[MemoryHookProvider(client, memory_id)],
        state={"actor_id": actor_id, "session_id": session_id}
    )
```

### 5. Memory Hook Provider (memory_hook.py)

**Responsibility:** Use identifiers for memory operations

**Current State:**
- Already extracts `actor_id` and `session_id` from agent state
- Already uses them in memory operations
- No changes required (already designed correctly)

**Interface:**
```python
# Load memory
recent_turns = self.memory_client.get_last_k_turns(
    memory_id=self.memory_id,
    actor_id=actor_id,        # From agent.state
    session_id=session_id,    # From agent.state
    k=5
)

# Save memory
self.memory_client.create_event(
    memory_id=self.memory_id,
    actor_id=actor_id,        # From agent.state
    session_id=session_id,    # From agent.state
    messages=[(text, role)]
)
```

## Data Models

### Session Identifier Format

**Frontend Session ID:**
- Format: Timestamp string (e.g., "1734012345678")
- Generated: `Date.now().toString()`
- Storage: localStorage per user (`sentra_sessions_${userId}`)
- Uniqueness: Guaranteed unique per chat creation time

**Backend Actor ID:**
- Format: User identifier string (e.g., "kamaljeet.singh")
- Source: User login selection
- Storage: localStorage (`sentra_user_id`)
- Uniqueness: One per user

### Memory Store Structure

```
AWS Bedrock AgentCore Memory
└─ Memory ID: "Sentra_Agent_Memory_V1"
    ├─ Actor: "kamaljeet.singh"
    │   ├─ Session: "1734012345678"
    │   │   └─ Messages: [turn1, turn2, turn3, ...]
    │   └─ Session: "1734012456789"
    │       └─ Messages: [turn1, turn2, ...]
    ├─ Actor: "vishal.saxena"
    │   ├─ Session: "1734012567890"
    │   │   └─ Messages: [turn1, turn2, ...]
    │   └─ Session: "1734012678901"
    │       └─ Messages: [turn1, turn2, ...]
    └─ Actor: "harsh.kumar"
        └─ Session: "1734012789012"
            └─ Messages: [turn1, turn2, ...]
```

### Request Flow Data

```
1. User sends message in chat
   ↓
2. Frontend prepares payload:
   {
     user_query: "Show me insurance policies",
     user_id: "kamaljeet.singh",
     session_id: "1734012345678"
   }
   ↓
3. Flask API validates and forwards:
   {
     user_query: "Show me insurance policies",
     user_id: "kamaljeet.singh",
     session_id: "1734012345678"
   }
   ↓
4. AgentCore extracts and initializes:
   SQLQueryExecutor(
     actor_id="kamaljeet.singh",
     session_id="1734012345678"
   )
   ↓
5. Agent state contains:
   {
     "actor_id": "kamaljeet.singh",
     "session_id": "1734012345678"
   }
   ↓
6. Memory operations use:
   get_last_k_turns(
     memory_id="Sentra_Agent_Memory_V1",
     actor_id="kamaljeet.singh",
     session_id="1734012345678",
     k=5
   )
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: User Memory Isolation

*For any* two different users (actor_id_1 ≠ actor_id_2), when loading conversation history, the messages returned for actor_id_1 should not contain any messages from actor_id_2

**Validates: Requirements 1.2, 1.3**

### Property 2: Session Memory Isolation

*For any* single user with two different sessions (session_id_1 ≠ session_id_2), when loading conversation history for session_id_1, the messages returned should not contain any messages from session_id_2

**Validates: Requirements 2.2, 2.3**

### Property 3: Message Storage Consistency

*For any* message stored with a specific (actor_id, session_id) pair, when retrieving messages with the same (actor_id, session_id) pair, the stored message should be present in the retrieved results

**Validates: Requirements 1.4, 2.4**

### Property 4: Session Persistence

*For any* session_id that exists in localStorage, when the page is refreshed and a query is sent, the backend should receive the same session_id value

**Validates: Requirements 5.1, 5.2**

### Property 5: Request Validation

*For any* API request missing either user_id or session_id, the system should return an error response and not proceed with query execution

**Validates: Requirements 4.1, 4.2**

### Property 6: Identifier Propagation

*For any* valid request with user_id and session_id, when the request flows through Flask API → AgentCore → SQLQueryExecutor → Memory Hooks, the same identifier values should be used at each layer

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Error Handling

### Missing Identifier Errors

**Location:** Flask API (`Agent_Trigger.py`)

**Validation:**
```python
if not payload.get("user_id"):
    return jsonify({
        "error": "missing_actor_id",
        "message": "user_id is required"
    }), 400

if not payload.get("session_id"):
    return jsonify({
        "error": "missing_session_id", 
        "message": "session_id is required"
    }), 400
```

**Location:** AgentCore Entrypoint (`main.py`)

**Validation:**
```python
if not payload.get("user_id"):
    return {
        "type": "text",
        "data": "",
        "explanation": "Error: user_id is required for memory isolation",
        "customer_specific": "False",
        "query_executed": ""
    }

if not payload.get("session_id"):
    return {
        "type": "text",
        "data": "",
        "explanation": "Error: session_id is required for memory isolation",
        "customer_specific": "False",
        "query_executed": ""
    }
```

### Memory Load Failures

**Location:** Memory Hook (`memory_hook.py`)

**Current Handling:**
```python
try:
    recent_turns = self.memory_client.get_last_k_turns(...)
    # Process turns
except Exception as e:
    logger.error(f"Memory load error: {e}")
    # Agent continues with empty context
```

**Behavior:** Non-blocking - agent initializes with empty conversation context

### Memory Save Failures

**Location:** Memory Hook (`memory_hook.py`)

**Current Handling:**
```python
try:
    self.memory_client.create_event(...)
except Exception as e:
    logger.error(f"Memory save error: {e}")
    # Query result still returns to user
```

**Behavior:** Non-blocking - query execution continues, but message not persisted

### Invalid Session ID Format

**Handling:** No format validation required
- Session IDs are opaque strings
- AWS Memory Client accepts any string format
- Frontend generates timestamp-based strings (guaranteed valid)

## Testing Strategy

### Unit Tests

**Test File:** `Backend/tests/test_session_isolation.py`

**Test Cases:**

1. **test_frontend_includes_session_id**
   - Mock fetch request from frontend
   - Verify payload contains user_id and session_id
   - **Validates:** Requirements 3.1

2. **test_flask_api_validation_missing_user_id**
   - Send request without user_id
   - Verify 400 error response with "missing_actor_id"
   - **Validates:** Requirements 4.1

3. **test_flask_api_validation_missing_session_id**
   - Send request without session_id
   - Verify 400 error response with "missing_session_id"
   - **Validates:** Requirements 4.2

4. **test_flask_api_forwards_identifiers**
   - Send request with both identifiers
   - Mock AgentCore invocation
   - Verify both identifiers in invocation payload
   - **Validates:** Requirements 3.2, 3.3

5. **test_agentcore_extracts_identifiers**
   - Call main() with payload containing identifiers
   - Mock SQLQueryExecutor initialization
   - Verify actor_id and session_id passed correctly
   - **Validates:** Requirements 3.4

6. **test_memory_hook_uses_agent_state**
   - Create agent with specific actor_id and session_id
   - Trigger on_agent_initialized event
   - Verify memory_client.get_last_k_turns called with correct IDs
   - **Validates:** Requirements 1.2, 2.2

### Property-Based Tests

**Test File:** `Backend/tests/test_memory_isolation_properties.py`

**Property Tests:**

1. **test_property_user_isolation**
   - Generate random user IDs and messages
   - Store messages for different users
   - Verify each user only retrieves their own messages
   - **Validates:** Property 1 (Requirements 1.2, 1.3)

2. **test_property_session_isolation**
   - Generate random session IDs for same user
   - Store messages in different sessions
   - Verify each session only retrieves its own messages
   - **Validates:** Property 2 (Requirements 2.2, 2.3)

3. **test_property_storage_consistency**
   - Generate random (actor_id, session_id, message) tuples
   - Store each message
   - Retrieve with same identifiers
   - Verify stored message appears in results
   - **Validates:** Property 3 (Requirements 1.4, 2.4)

4. **test_property_identifier_propagation**
   - Generate random user_id and session_id
   - Send through full request flow
   - Verify same values at each layer
   - **Validates:** Property 6 (Requirements 3.1-3.4)

### Integration Tests

**Test File:** `Backend/tests/test_end_to_end_isolation.py`

**Test Scenarios:**

1. **test_multiple_users_different_contexts**
   - Simulate 3 different users
   - Each sends queries in their own session
   - Verify each user gets isolated conversation history
   - **Validates:** Requirements 1.1, 1.2, 1.3

2. **test_same_user_multiple_sessions**
   - Simulate 1 user with 3 different chat sessions
   - Send queries in each session
   - Switch between sessions
   - Verify each session loads correct history
   - **Validates:** Requirements 2.1, 2.2, 2.3, 2.5

3. **test_session_persistence_after_refresh**
   - Simulate user sending messages
   - Simulate page refresh (same session_id)
   - Send new message
   - Verify conversation history includes pre-refresh messages
   - **Validates:** Requirements 5.1, 5.2, 5.3

### Manual Testing Checklist

1. **User Isolation Test**
   - Login as user A, send messages
   - Logout, login as user B
   - Verify user B doesn't see user A's messages

2. **Session Isolation Test**
   - Login as user A, send messages in Chat 1
   - Create new chat (Chat 2), send different messages
   - Switch back to Chat 1
   - Verify Chat 1 shows original messages, not Chat 2 messages

3. **Persistence Test**
   - Send messages in a chat
   - Refresh browser
   - Send new message
   - Verify agent references previous messages correctly

4. **Error Handling Test**
   - Manually call API without user_id
   - Verify error response
   - Manually call API without session_id
   - Verify error response

## Implementation Notes

### Minimal Changes Required

The existing codebase is already well-designed for this feature:
- SQLQueryExecutor already accepts actor_id and session_id parameters
- Memory hooks already extract and use these from agent state
- Frontend already manages unique session IDs

**Only 3 files need modification:**
1. `Frontend/src/components/ChatInterface.jsx` - Add session_id to request
2. `Backend/Agent_Trigger.py` - Extract and validate session_id
3. `Backend/main.py` - Use dynamic identifiers instead of hardcoded values

### Backward Compatibility

**Not Required:** This is a bug fix, not a feature addition
- Current behavior (shared memory) is incorrect
- No existing functionality depends on shared memory
- All users will benefit from proper isolation

### Performance Considerations

**No Performance Impact:**
- Memory operations already use actor_id and session_id
- No additional database queries
- No additional network calls
- Same memory retrieval pattern (last 5 turns)

### Security Considerations

**Improved Security:**
- Users cannot access other users' conversation history
- Session isolation prevents cross-session data leakage
- Validation prevents requests without proper identification

**No New Vulnerabilities:**
- Session IDs are not security tokens (just identifiers)
- RBAC still enforced at query level (existing mechanism)
- No sensitive data in session IDs (just timestamps)
