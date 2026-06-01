# 📡 API Endpoints Documentation

## Base URL
```
http://localhost:5000
```

---

## 🏥 Health Check

### `GET /health`
Check if the API server is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "Sentra Insurance API"
}
```

---

## 💬 Chat History Endpoints

### 1. Create Session

**`POST /api/sessions`**

Create a new chat session.

**Request Body:**
```json
{
  "session_id": "1234567890123_ABC1234567890123456",
  "user_id": "kamaljeet.singh",
  "title": "New Chat"
}
```

**Response:**
```json
{
  "id": "1234567890123_ABC1234567890123456",
  "title": "New Chat",
  "messages": [],
  "createdAt": 1703001234567,
  "updatedAt": 1703001234567
}
```

**Status Codes:**
- `200` - Success
- `500` - Server error

---

### 2. Get User Sessions

**`GET /api/sessions/{user_id}`**

Get all sessions for a specific user.

**Parameters:**
- `user_id` (path) - User identifier

**Response:**
```json
[
  {
    "id": "1234567890123_ABC1234567890123456",
    "title": "Insurance Query",
    "messages": [],
    "createdAt": 1703001234567,
    "updatedAt": 1703001234567
  },
  {
    "id": "1234567890124_DEF1234567890123456",
    "title": "Policy Information",
    "messages": [],
    "createdAt": 1703001234568,
    "updatedAt": 1703001234568
  }
]
```

**Status Codes:**
- `200` - Success
- `500` - Server error

---

### 3. Get Session Messages

**`GET /api/sessions/{session_id}/messages`**

Get all messages for a specific session.

**Parameters:**
- `session_id` (path) - Session identifier

**Response:**
```json
[
  {
    "id": "msg_1703001234567",
    "type": "user",
    "content": "Show me all insurance policies",
    "timestamp": 1703001234567
  },
  {
    "id": "msg_1703001234568",
    "type": "bot",
    "content": {
      "type": "bar",
      "data": [
        {"label": "Health", "value": 450},
        {"label": "Life", "value": 320}
      ],
      "explanation": "Policy distribution shows...",
      "query_executed": "SELECT ..."
    },
    "timestamp": 1703001234568
  }
]
```

**Status Codes:**
- `200` - Success
- `500` - Server error

---

### 4. Save Message

**`POST /api/messages`**

Save a new message to a session.

**Request Body:**
```json
{
  "message_id": "msg_1703001234567",
  "session_id": "1234567890123_ABC1234567890123456",
  "message_type": "user",
  "content": "Show me all insurance policies",
  "timestamp": 1703001234567
}
```

**Response:**
```json
{
  "id": "msg_1703001234567",
  "type": "user",
  "content": "Show me all insurance policies",
  "timestamp": 1703001234567
}
```

**Status Codes:**
- `200` - Success
- `404` - Session not found
- `500` - Server error

**Notes:**
- `message_type` must be either "user" or "bot"
- `content` can be string (user) or object (bot)
- Session's `updated_at` is automatically updated

---

### 5. Update Session

**`PUT /api/sessions/{session_id}`**

Update session title (rename).

**Parameters:**
- `session_id` (path) - Session identifier

**Request Body:**
```json
{
  "title": "Updated Session Title"
}
```

**Response:**
```json
{
  "id": "1234567890123_ABC1234567890123456",
  "title": "Updated Session Title",
  "messages": [],
  "createdAt": 1703001234567,
  "updatedAt": 1703001234999
}
```

**Status Codes:**
- `200` - Success
- `404` - Session not found
- `500` - Server error

---

### 6. Delete Session

**`DELETE /api/sessions/{session_id}`**

Delete a session and all its messages.

**Parameters:**
- `session_id` (path) - Session identifier

**Response:**
```json
{
  "message": "Session deleted successfully",
  "session_id": "1234567890123_ABC1234567890123456"
}
```

**Status Codes:**
- `200` - Success
- `404` - Session not found
- `500` - Server error

**Notes:**
- Cascade delete: All messages in the session are also deleted

---

## 🤖 Bedrock Agent Endpoint

### Query Agent

**`POST /query`**

Send a query to the Bedrock Agent (existing endpoint).

**Request Body:**
```json
{
  "user_query": "Show me all insurance policies",
  "user_id": "kamaljeet.singh",
  "session_id": "1234567890123_ABC1234567890123456"
}
```

**Response:**
```json
{
  "type": "bar",
  "data": [
    {"label": "Health", "value": 450},
    {"label": "Life", "value": 320},
    {"label": "Motor", "value": 280}
  ],
  "explanation": "Policy distribution shows Health insurance leading...",
  "customer_specific": "False",
  "query_executed": "SELECT policy_type, COUNT(*) FROM insurance_data GROUP BY policy_type"
}
```

**Status Codes:**
- `200` - Success
- `400` - Missing user_id or session_id
- `500` - Bedrock error

---

## 🔄 Request Flow

### Creating a Session and Sending a Message

```
1. POST /api/sessions
   → Create session in database
   → Return session object

2. POST /api/messages (user message)
   → Save user message to database
   → Update session timestamp

3. POST /query
   → Send to Bedrock Agent
   → Get AI response

4. POST /api/messages (bot message)
   → Save bot response to database
   → Update session timestamp

5. GET /api/sessions/{session_id}/messages
   → Retrieve all messages
   → Display in UI
```

---

## 📊 Data Models

### Session Object
```typescript
{
  id: string,           // 33-character session ID
  title: string,        // Session title
  messages: [],         // Empty array (messages loaded separately)
  createdAt: number,    // Unix timestamp (milliseconds)
  updatedAt: number     // Unix timestamp (milliseconds)
}
```

### Message Object
```typescript
{
  id: string,           // Message ID
  type: "user" | "bot", // Message type
  content: string | object, // Message content
  timestamp: number     // Unix timestamp (milliseconds)
}
```

### Bot Response Content
```typescript
{
  type: "text" | "bar" | "line" | "pie" | "scatter",
  data: string | Array<{label: string, value: number}>,
  explanation: string,
  customer_specific: "True" | "False",
  query_executed: string
}
```

---

## 🧪 Testing with curl

### Create Session
```bash
curl -X POST http://localhost:5000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "1234567890123_ABC1234567890123456",
    "user_id": "test_user",
    "title": "Test Session"
  }'
```

### Get Sessions
```bash
curl http://localhost:5000/api/sessions/test_user
```

### Save Message
```bash
curl -X POST http://localhost:5000/api/messages \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "msg_123",
    "session_id": "1234567890123_ABC1234567890123456",
    "message_type": "user",
    "content": "Hello",
    "timestamp": 1703001234567
  }'
```

### Get Messages
```bash
curl http://localhost:5000/api/sessions/1234567890123_ABC1234567890123456/messages
```

### Update Session
```bash
curl -X PUT http://localhost:5000/api/sessions/1234567890123_ABC1234567890123456 \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}'
```

### Delete Session
```bash
curl -X DELETE http://localhost:5000/api/sessions/1234567890123_ABC1234567890123456
```

### Query Agent
```bash
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Show me all policies",
    "user_id": "test_user",
    "session_id": "1234567890123_ABC1234567890123456"
  }'
```

---

## 🔒 Security Notes

- All endpoints accept JSON payloads
- CORS enabled for all origins (configure for production)
- No authentication implemented (add JWT for production)
- Database credentials in environment variables
- SSL/TLS connection to RDS

---

## 📈 Performance

- Connection pooling: 10 connections, 20 overflow
- Database indexes on frequently queried fields
- JSONB for fast JSON queries
- Pre-ping to verify connections
- Transaction support for data integrity

---

## 🐛 Error Handling

All endpoints return consistent error format:

```json
{
  "detail": "Error message description"
}
```

Common errors:
- `400` - Bad request (missing parameters)
- `404` - Resource not found
- `500` - Internal server error

---

## 📚 Related Documentation

- **Setup Guide**: `RDS_SETUP_GUIDE.md`
- **Implementation Summary**: `IMPLEMENTATION_SUMMARY.md`
- **Database Schema**: `database_schema.sql`
- **Quick Start**: `../QUICKSTART_RDS.md`

---

**Last Updated:** December 2025  
**API Version:** 1.0.0  
**Base URL:** http://localhost:5000
