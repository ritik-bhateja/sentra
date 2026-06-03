## V3 Schema Implementation Guide
# Production-Ready Chat System with Conversation Turns

## Overview

V3 introduces a **conversation turn-based** architecture that's more robust and production-ready:

- ✅ **UUID-based** primary keys (not timestamps)
- ✅ **Conversation turns** instead of individual messages
- ✅ **Auto-incrementing turn numbers** per session
- ✅ **Status tracking** for sessions and turns
- ✅ **Soft deletes** (ARCHIVED/DELETED status)
- ✅ **Activity tracking** (last_activity_at)
- ✅ **Error handling** (failed turns with error messages)

## Architecture Comparison

### V1/V2: Message-Based
```
Session
├── Message 1 (user)
├── Message 2 (bot)
├── Message 3 (user)
└── Message 4 (bot)
```
**Problem**: Messages are independent, hard to track conversation flow

### V3: Turn-Based
```
Session
├── Turn 1 (user_query + assistant_response)
├── Turn 2 (user_query + assistant_response)
└── Turn 3 (user_query + assistant_response)
```
**Benefit**: Each turn is atomic, easier to track, replay, and debug

## Database Schema

### Table 1: chat_sessions

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | UUID | Primary key (auto-generated) |
| `user_id` | VARCHAR(100) | User email (harsh.kumar@sentra.com) |
| `session_title` | VARCHAR(500) | Session title |
| `status` | VARCHAR(20) | ACTIVE, ARCHIVED, DELETED |
| `created_at` | TIMESTAMPTZ | When session was created |
| `updated_at` | TIMESTAMPTZ | Last update time |
| `last_activity_at` | TIMESTAMPTZ | Last user interaction |

### Table 2: conversation_turns

| Column | Type | Description |
|--------|------|-------------|
| `turn_id` | UUID | Primary key (auto-generated) |
| `session_id` | UUID | Foreign key to chat_sessions |
| `turn_number` | INTEGER | Auto-incremented per session (1, 2, 3...) |
| `user_query` | TEXT | User's question |
| `assistant_response` | JSONB | Full response object |
| `model_name` | VARCHAR(100) | Model used (moonshotai.kimi-k2.5) |
| `status` | VARCHAR(20) | PENDING, RUNNING, COMPLETED, FAILED |
| `created_at` | TIMESTAMPTZ | When turn started |
| `completed_at` | TIMESTAMPTZ | When turn finished |
| `error_message` | TEXT | Error if turn failed |

## Key Features

### 1. Auto-Incrementing Turn Numbers

```sql
-- Trigger automatically sets turn_number
INSERT INTO conversation_turns (session_id, user_query)
VALUES ('uuid-here', 'Show policies');
-- turn_number = 1 (auto-set)

INSERT INTO conversation_turns (session_id, user_query)
VALUES ('uuid-here', 'Show by zone');
-- turn_number = 2 (auto-set)
```

### 2. Status Tracking

**Session Status:**
- `ACTIVE` - Currently in use
- `ARCHIVED` - Old but kept for history
- `DELETED` - Soft-deleted (not shown to user)

**Turn Status:**
- `PENDING` - Created but not started
- `RUNNING` - Currently processing
- `COMPLETED` - Successfully finished
- `FAILED` - Error occurred

### 3. Activity Tracking

```sql
-- Automatically updates when turn is added
last_activity_at = NOW()
```

Enables:
- Sort sessions by recent activity
- Archive inactive sessions
- Show "last active" timestamps

### 4. Error Handling

```python
try:
    response = call_bedrock_agent()
    turn.status = 'COMPLETED'
    turn.assistant_response = response
except Exception as e:
    turn.status = 'FAILED'
    turn.error_message = str(e)
```

## API Endpoints

### Query Endpoint (Enhanced)

```http
POST /query
Content-Type: application/json

{
  "user_query": "Show policies by zone",
  "user_id": "harsh.kumar",
  "session_id": "optional-uuid",  // Creates new if not provided
  "user_email": "harsh.kumar@sentra.com"
}

Response:
{
  "type": "bar",
  "data": [...],
  "explanation": "...",
  "session_id": "uuid-here",  // NEW: Returns session_id
  "turn_number": 1            // NEW: Returns turn number
}
```

### Session Endpoints

```http
# Create session
POST /api/sessions
{
  "user_id": "harsh.kumar@sentra.com",
  "session_title": "Policy Analysis"
}

# Get user's sessions
GET /api/sessions/{user_id}

# Get session turns (as messages for frontend compatibility)
GET /api/sessions/{session_id}/turns

# Get session turns (raw format)
GET /api/sessions/{session_id}/turns/raw

# Update session
PUT /api/sessions/{session_id}
{
  "session_title": "New Title",
  "status": "ARCHIVED"
}

# Delete session (soft delete)
DELETE /api/sessions/{session_id}
```

### Backward Compatibility

```http
# Old endpoint still works
GET /api/sessions/{session_id}/messages
# Returns turns converted to message format
```

## Migration Steps

### Step 1: Backup Current Data

```bash
# Backup existing tables
pg_dump -h <host> -U postgres -d company_db \
  -t chat_sessions -t chat_messages \
  > backup_v2.sql
```

### Step 2: Create V3 Schema

```bash
# Run V3 schema
psql -h <host> -U postgres -d company_db \
  -f database_schema_v3.sql
```

### Step 3: Migrate Data (Optional)

```sql
-- Migrate sessions (if user_id format matches)
INSERT INTO chat_sessions (session_id, user_id, session_title, created_at, updated_at, last_activity_at)
SELECT 
    gen_random_uuid(),
    user_id,
    title,
    created_at,
    updated_at,
    updated_at
FROM old_chat_sessions;

-- Migrate messages to turns (group by pairs)
-- This is complex - recommend fresh start for development
```

### Step 4: Update Code

```bash
# Backup old files
cp models.py models_v2_backup.py
cp Agent_Trigger.py Agent_Trigger_v2_backup.py

# Use V3 files
cp models_v3.py models.py
cp Agent_Trigger_v3.py Agent_Trigger.py
```

### Step 5: Test

```bash
# Start server
python3 Agent_Trigger.py

# Test query endpoint
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Show policies",
    "user_id": "harsh.kumar"
  }'

# Check database
psql -h <host> -U postgres -d company_db \
  -c "SELECT * FROM v_active_sessions;"
```

## Frontend Changes

### Minimal Changes Required

The frontend can continue using the same API, but can now leverage new features:

```javascript
// Old way (still works)
const response = await fetch('/query', {
  method: 'POST',
  body: JSON.stringify({
    user_query: query,
    user_id: userId,
    session_id: sessionId
  })
});

// New way (with session tracking)
const response = await fetch('/query', {
  method: 'POST',
  body: JSON.stringify({
    user_query: query,
    user_id: userId,
    session_id: sessionId,  // Optional: creates new if not provided
    user_email: userEmail
  })
});

const data = await response.json();
console.log('Session ID:', data.session_id);  // NEW
console.log('Turn number:', data.turn_number);  // NEW
```

### Enhanced Features

```javascript
// Get session with turn count
const sessions = await fetch(`/api/sessions/${userId}`);
// Returns: [{ id, title, turnCount, lastActivityAt, ... }]

// Get conversation history (as messages)
const messages = await fetch(`/api/sessions/${sessionId}/turns`);
// Returns: [{ id, type: 'user', content, timestamp }, ...]

// Get raw turn data (for debugging)
const turns = await fetch(`/api/sessions/${sessionId}/turns/raw`);
// Returns: [{ turn_id, turn_number, user_query, assistant_response, status, ... }]

// Archive old session
await fetch(`/api/sessions/${sessionId}`, {
  method: 'PUT',
  body: JSON.stringify({ status: 'ARCHIVED' })
});
```

## Benefits

### 1. Better Conversation Tracking

```sql
-- Get complete conversation
SELECT turn_number, user_query, assistant_response
FROM conversation_turns
WHERE session_id = 'xxx'
ORDER BY turn_number;
```

### 2. Replay Conversations

```python
# Replay a conversation for debugging
turns = db.query(ConversationTurn).filter(
    ConversationTurn.session_id == session_id
).order_by(ConversationTurn.turn_number).all()

for turn in turns:
    print(f"Turn {turn.turn_number}:")
    print(f"  User: {turn.user_query}")
    print(f"  Bot: {turn.assistant_response}")
```

### 3. Error Analysis

```sql
-- Find failed turns
SELECT session_id, turn_number, user_query, error_message
FROM conversation_turns
WHERE status = 'FAILED'
ORDER BY created_at DESC;
```

### 4. Performance Metrics

```sql
-- Average response time per turn
SELECT 
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_seconds
FROM conversation_turns
WHERE status = 'COMPLETED';

-- Turns per session
SELECT 
    session_id,
    COUNT(*) as turn_count,
    MAX(turn_number) as last_turn
FROM conversation_turns
GROUP BY session_id;
```

### 5. Session Management

```sql
-- Archive sessions older than 30 days
SELECT archive_old_sessions(30);

-- Get active sessions with turn count
SELECT * FROM v_active_sessions
WHERE user_id = 'harsh.kumar@sentra.com';
```

## Testing

### Test 1: Create Session and Turns

```bash
# Send query without session_id (creates new session)
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Show policies",
    "user_id": "harsh.kumar"
  }'

# Response includes session_id
# Use that session_id for next query

curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Show by zone",
    "user_id": "harsh.kumar",
    "session_id": "uuid-from-previous-response"
  }'
```

### Test 2: Verify Turn Sequencing

```sql
SELECT session_id, turn_number, user_query, status
FROM conversation_turns
WHERE session_id = 'uuid-here'
ORDER BY turn_number;

-- Should show:
-- turn_number | user_query           | status
-- 1           | Show policies        | COMPLETED
-- 2           | Show by zone         | COMPLETED
```

### Test 3: Test Error Handling

```python
# Simulate error in agent
# Turn should be marked as FAILED with error_message
```

### Test 4: Test Session Management

```bash
# Get user sessions
curl http://localhost:5000/api/sessions/harsh.kumar@sentra.com

# Archive session
curl -X PUT http://localhost:5000/api/sessions/{uuid} \
  -H "Content-Type: application/json" \
  -d '{"status": "ARCHIVED"}'

# Verify archived session not in active list
curl http://localhost:5000/api/sessions/harsh.kumar@sentra.com
```

## Monitoring Queries

```sql
-- Active sessions count
SELECT COUNT(*) FROM chat_sessions WHERE status = 'ACTIVE';

-- Total turns today
SELECT COUNT(*) FROM conversation_turns 
WHERE created_at >= CURRENT_DATE;

-- Failed turns today
SELECT COUNT(*) FROM conversation_turns 
WHERE status = 'FAILED' AND created_at >= CURRENT_DATE;

-- Average turns per session
SELECT AVG(turn_count) FROM v_active_sessions;

-- Most active users
SELECT user_id, COUNT(*) as session_count, SUM(turn_count) as total_turns
FROM v_active_sessions
GROUP BY user_id
ORDER BY total_turns DESC;
```

## Rollback Plan

```bash
# 1. Stop application
# 2. Restore V2 code
cp models_v2_backup.py models.py
cp Agent_Trigger_v2_backup.py Agent_Trigger.py

# 3. Restore V2 database (if needed)
psql -h <host> -U postgres -d company_db < backup_v2.sql

# 4. Restart application
python3 Agent_Trigger.py
```

## Recommendation

**For Development**: Use V3 immediately (fresh start)
**For Production**: Plan migration during maintenance window

V3 provides:
- ✅ Better conversation tracking
- ✅ Easier debugging and replay
- ✅ Production-ready error handling
- ✅ Session lifecycle management
- ✅ Performance metrics and analytics

**Verdict**: Migrate to V3! 🚀
