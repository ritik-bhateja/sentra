# 🚀 RDS Chat History Setup Guide

This guide will help you set up PostgreSQL RDS for storing chat history.

---

## 📋 Prerequisites

✅ PostgreSQL RDS instance created  
✅ Database name: `company_db`  
✅ Username: `postgres`  
✅ Password: `lumiq121`  
✅ Endpoint: `database-2-instance-1.crwu46wug6kx.ap-south-1.rds.amazonaws.com`  
✅ Port: `5432`  
✅ Public accessibility: Yes  
✅ SSL: Required  

---

## 🔧 Step 1: Install Backend Dependencies

```bash
cd BackendAPI
pip install -r requirements.txt
```

**New dependencies added:**
- `sqlalchemy` - ORM for database operations
- `psycopg2-binary` - PostgreSQL driver
- `python-dotenv` - Environment variable management

---

## 🗄️ Step 2: Create Database Schema

Run the setup script to create tables and indexes:

```bash
cd BackendAPI
python setup_database.py
```

**Expected output:**
```
============================================================
Sentra Chat History - Database Setup
============================================================

Connecting to database-2-instance-1.crwu46wug6kx.ap-south-1.rds.amazonaws.com:5432/company_db...
✅ Connected successfully!

Executing database schema...
✅ Database schema created successfully!

📊 Tables created:
  - chat_sessions
  - chat_messages

🔍 Indexes created:
  - idx_user_sessions
  - idx_session_messages
  - idx_message_content

✅ Database setup complete!
```

**What gets created:**

### Table 1: `chat_sessions`
| Column | Type | Description |
|--------|------|-------------|
| session_id | VARCHAR(33) | Primary key, 33-char session ID |
| user_id | VARCHAR(100) | User identifier |
| title | VARCHAR(255) | Session title (default: "New Chat") |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### Table 2: `chat_messages`
| Column | Type | Description |
|--------|------|-------------|
| message_id | VARCHAR(50) | Primary key |
| session_id | VARCHAR(33) | Foreign key to chat_sessions |
| message_type | VARCHAR(10) | 'user' or 'bot' |
| content | JSONB | Message content (JSON) |
| timestamp | BIGINT | Unix timestamp in milliseconds |
| created_at | TIMESTAMP | Creation timestamp |

---

## 🧪 Step 3: Test Database Connection

```bash
cd BackendAPI
python database.py
```

**Expected output:**
```
Testing database connection...
✅ Database connection successful!
✅ Connection successful!
```

---

## 🚀 Step 4: Start Backend API

```bash
cd BackendAPI
python Agent_Trigger.py
```

**Expected output:**
```
✅ Database connected successfully
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000
```

---

## 🌐 Step 5: Start Frontend

```bash
cd Frontend
npm run dev
```

**Expected output:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

---

## 🔄 Step 6: Automatic Migration

When you first log in to the frontend:

1. **Frontend checks localStorage** for existing sessions
2. **If sessions exist**, they are automatically migrated to RDS
3. **Migration happens once** per user
4. **localStorage is cleared** after successful migration
5. **All future sessions** are stored in RDS

**You'll see a brief message:**
```
"Migrating chat history to database..."
```

---

## 📡 API Endpoints Created

### Session Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sessions` | Create new session |
| GET | `/api/sessions/{user_id}` | Get all sessions for user |
| PUT | `/api/sessions/{session_id}` | Update session title |
| DELETE | `/api/sessions/{session_id}` | Delete session |

### Message Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions/{session_id}/messages` | Get messages for session |
| POST | `/api/messages` | Save message to session |

### Existing Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/query` | Send query to Bedrock Agent |
| GET | `/health` | Health check |

---

## 🧪 Testing the API

### Test with curl:

```bash
# Health check
curl http://localhost:5000/health

# Create session
curl -X POST http://localhost:5000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "1234567890123_ABC1234567890123456",
    "user_id": "kamaljeet.singh",
    "title": "Test Session"
  }'

# Get user sessions
curl http://localhost:5000/api/sessions/kamaljeet.singh

# Save message
curl -X POST http://localhost:5000/api/messages \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "msg_123",
    "session_id": "1234567890123_ABC1234567890123456",
    "message_type": "user",
    "content": "Hello",
    "timestamp": 1234567890000
  }'

# Get session messages
curl http://localhost:5000/api/sessions/1234567890123_ABC1234567890123456/messages
```

---

## 🔍 Verify Data in Database

### Using psql:

```bash
psql -h database-2-instance-1.crwu46wug6kx.ap-south-1.rds.amazonaws.com \
     -p 5432 \
     -U postgres \
     -d company_db
```

### SQL Queries:

```sql
-- View all sessions
SELECT * FROM chat_sessions ORDER BY updated_at DESC;

-- View all messages for a session
SELECT * FROM chat_messages WHERE session_id = 'YOUR_SESSION_ID' ORDER BY timestamp;

-- Count sessions per user
SELECT user_id, COUNT(*) as session_count FROM chat_sessions GROUP BY user_id;

-- Count messages per session
SELECT session_id, COUNT(*) as message_count FROM chat_messages GROUP BY session_id;

-- View recent bot responses
SELECT content->>'type' as response_type, COUNT(*) 
FROM chat_messages 
WHERE message_type = 'bot' 
GROUP BY content->>'type';
```

---

## 🐛 Troubleshooting

### Issue: Connection timeout

**Solution:**
- Check RDS security group allows inbound traffic on port 5432
- Verify your IP is whitelisted
- Check VPC settings

### Issue: SSL certificate error

**Solution:**
- Download RDS certificate: https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem
- Update `.env`: `DB_SSLMODE=require`

### Issue: Authentication failed

**Solution:**
- Verify username and password in `.env`
- Check RDS master credentials

### Issue: Database does not exist

**Solution:**
```bash
# Connect to default postgres database
psql -h database-2-instance-1.crwu46wug6kx.ap-south-1.rds.amazonaws.com \
     -p 5432 \
     -U postgres \
     -d postgres

# Create database
CREATE DATABASE company_db;
```

### Issue: Frontend shows old localStorage data

**Solution:**
- Clear browser localStorage: `localStorage.clear()`
- Refresh page
- Migration will run automatically

---

## 📊 Architecture Flow

```
User Login
    ↓
Frontend checks localStorage
    ↓
[Has sessions?] → Yes → Migrate to RDS → Clear localStorage
    ↓                                           ↓
    No                                    Load from RDS
    ↓                                           ↓
Create new session in RDS ←──────────────────────┘
    ↓
User sends message
    ↓
Save to RDS (user message)
    ↓
Call Bedrock Agent (/query)
    ↓
Save to RDS (bot response)
    ↓
Display in UI
```

---

## 🎯 Key Features

✅ **Automatic Migration**: localStorage → RDS on first login  
✅ **Real-time Sync**: All messages saved to RDS immediately  
✅ **Fallback Support**: Falls back to localStorage if RDS fails  
✅ **Connection Pooling**: Efficient database connections  
✅ **JSONB Storage**: Fast queries on message content  
✅ **Cascade Delete**: Deleting session removes all messages  
✅ **Auto-update Timestamps**: `updated_at` updates automatically  

---

## 📝 Environment Variables

File: `BackendAPI/.env`

```env
# Database Configuration
DB_HOST=database-2-instance-1.crwu46wug6kx.ap-south-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=company_db
DB_USER=postgres
DB_PASSWORD=lumiq121
DB_SSLMODE=require

# API Configuration
API_PORT=5000
```

---

## 🔒 Security Notes

⚠️ **Important:**
- Never commit `.env` file to git
- Use IAM authentication for production
- Rotate database passwords regularly
- Use VPC for private RDS access
- Enable encryption at rest
- Enable automated backups

---

## ✅ Checklist

- [ ] Install backend dependencies
- [ ] Create `.env` file with RDS credentials
- [ ] Run `setup_database.py` to create schema
- [ ] Test database connection with `database.py`
- [ ] Start backend API
- [ ] Start frontend
- [ ] Log in and verify migration
- [ ] Send test message
- [ ] Verify data in RDS

---

## 🎉 Success!

Your chat history is now stored in PostgreSQL RDS!

**Benefits:**
- ✅ Persistent across devices
- ✅ Scalable for multiple users
- ✅ Fast JSONB queries
- ✅ Automatic backups
- ✅ Production-ready

---

## 📞 Support

If you encounter issues:
1. Check logs in terminal
2. Verify `.env` configuration
3. Test database connection
4. Check RDS security groups
5. Review API endpoint responses

---

**Last Updated:** December 2025  
**Database:** PostgreSQL 13+ on AWS RDS  
**Region:** ap-south-1 (Mumbai)
