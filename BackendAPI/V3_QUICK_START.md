# V3 Quick Start Guide

## What's New in V3?

✅ **UUID-based sessions** (not timestamp strings)
✅ **Conversation turns** (user_query + assistant_response together)
✅ **Auto-incrementing turn numbers** (1, 2, 3...)
✅ **Status tracking** (ACTIVE, ARCHIVED, DELETED)
✅ **Error handling** (FAILED turns with error messages)
✅ **Activity tracking** (last_activity_at for sorting)

## Quick Setup

### 1. Create Database Schema

```bash
psql -h database-2-instance-1.crwu46wug6kx.ap-south-1.rds.amazonaws.com \
  -U postgres -d company_db \
  -f database_schema_v3.sql
```

### 2. Update Code

```bash
# Backup current files
cp models.py models_backup.py
cp Agent_Trigger.py Agent_Trigger_backup.py

# Use V3 files
cp models_v3.py models.py
cp Agent_Trigger_v3.py Agent_Trigger.py
```

### 3. Start Server

```bash
python3 Agent_Trigger.py
```

## API Changes

### Query Endpoint (Enhanced)

**Before (V2):**
```json
POST /query
{
  "user_query": "Show policies",
  "user_id": "harsh.kumar",
  "session_id": "1780317569105_xxx"
}
```

**After (V3):**
```json
POST /query
{
  "user_query": "Show policies",
  "user_id": "harsh.kumar",
  "session_id": "optional-uuid",  // Creates new if omitted
  "user_email": "harsh.kumar@sentra.com"
}

Response includes:
{
  ...response data...,
  "session_id": "uuid-here",  // NEW
  "turn_number": 1            // NEW
}
```

### New Endpoints

```bash
# Get user sessions
GET /api/sessions/{user_id}

# Get session turns (as messages)
GET /api/sessions/{session_id}/turns

# Get raw turn data
GET /api/sessions/{session_id}/turns/raw

# Update session
PUT /api/sessions/{session_id}
{"session_title": "New Title", "status": "ARCHIVED"}

# Delete session
DELETE /api/sessions/{session_id}
```

## Database Structure

### chat_sessions
```
session_id (UUID) | user_id | session_title | status | created_at | updated_at | last_activity_at
```

### conversation_turns
```
turn_id (UUID) | session_id | turn_number | user_query | assistant_response (JSONB) | status | created_at | completed_at
```

## Key Features

### 1. Auto-Incrementing Turns
```sql
-- Turn numbers auto-increment per session
Session A: turn 1, 2, 3, 4
Session B: turn 1, 2, 3
```

### 2. Status Tracking
```python
# Session status
'ACTIVE'    # Currently in use
'ARCHIVED'  # Old but kept
'DELETED'   # Soft-deleted

# Turn status
'PENDING'   # Created but not started
'RUNNING'   # Currently processing
'COMPLETED' # Successfully finished
'FAILED'    # Error occurred
```

### 3. Error Handling
```python
# Failed turns store error message
turn.status = 'FAILED'
turn.error_message = "Connection timeout"
```

## Testing

```bash
# Test 1: Create new session
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{"user_query": "Show policies", "user_id": "harsh.kumar"}'

# Test 2: Continue session
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{"user_query": "Show by zone", "user_id": "harsh.kumar", "session_id": "uuid-from-test-1"}'

# Test 3: Get sessions
curl http://localhost:5000/api/sessions/harsh.kumar@sentra.com

# Test 4: Get turns
curl http://localhost:5000/api/sessions/{uuid}/turns
```

## Useful Queries

```sql
-- View active sessions
SELECT * FROM v_active_sessions;

-- View conversation
SELECT turn_number, user_query, assistant_response->>'explanation'
FROM conversation_turns
WHERE session_id = 'uuid-here'
ORDER BY turn_number;

-- Find failed turns
SELECT * FROM conversation_turns WHERE status = 'FAILED';

-- Archive old sessions
SELECT archive_old_sessions(30);  -- Archive sessions older than 30 days
```

## Frontend Compatibility

**No changes required!** The frontend can continue using existing endpoints.

New features available:
- `session_id` returned in query response
- `turn_number` returned in query response
- `/api/sessions/{session_id}/turns` returns messages in same format

## Benefits

| Feature | V2 | V3 |
|---------|----|----|
| Primary Key | Timestamp string | UUID |
| Message Grouping | Individual messages | Conversation turns |
| Sequencing | Timestamp-based | Auto-incrementing |
| Error Tracking | ❌ No | ✅ Yes |
| Status Management | ❌ No | ✅ Yes |
| Activity Tracking | ❌ No | ✅ Yes |
| Soft Deletes | ❌ No | ✅ Yes |

## Migration Time

- **Schema creation**: 2 minutes
- **Code update**: 1 minute
- **Testing**: 5 minutes
- **Total**: 8 minutes

## Rollback

```bash
# Restore V2
cp models_backup.py models.py
cp Agent_Trigger_backup.py Agent_Trigger.py
python3 Agent_Trigger.py
```

## Next Steps

1. ✅ Create V3 schema
2. ✅ Update code files
3. ✅ Test endpoints
4. ✅ Update frontend (optional - for new features)
5. ✅ Monitor with SQL queries

**Ready to go! 🚀**
