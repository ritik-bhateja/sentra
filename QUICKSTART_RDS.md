# 🚀 Quick Start Guide - RDS Chat History

## ⚡ 5-Minute Setup

### **Step 1: Install Backend Dependencies** (1 min)
```bash
cd BackendAPI
pip install -r requirements.txt
```

### **Step 2: Verify .env File** (30 sec)
File: `BackendAPI/.env` (already created)
```env
DB_HOST=database-2-instance-1.crwu46wug6kx.ap-south-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=company_db
DB_USER=postgres
DB_PASSWORD=lumiq121
DB_SSLMODE=require
```

### **Step 3: Create Database Tables** (1 min)
```bash
cd BackendAPI
python setup_database.py
```

**Expected output:**
```
✅ Connected successfully!
✅ Database schema created successfully!
📊 Tables created: chat_sessions, chat_messages
```

### **Step 4: Start Backend** (30 sec)
```bash
python Agent_Trigger.py
```

**Expected output:**
```
✅ Database connected successfully
INFO: Uvicorn running on http://0.0.0.0:5000
```

### **Step 5: Start Frontend** (1 min)
```bash
cd Frontend
npm run dev
```

### **Step 6: Test** (1 min)
1. Open http://localhost:5173
2. Login with any user
3. Send a message
4. Refresh page - message should persist ✅

---

## 🧪 Optional: Test API

```bash
cd BackendAPI
python test_rds_connection.py
```

---

## ✅ What Changed?

### **Backend**
- ✅ 6 new API endpoints for chat history
- ✅ PostgreSQL RDS integration
- ✅ Automatic database connection on startup

### **Frontend**
- ✅ Automatic migration from localStorage to RDS
- ✅ All chat history now stored in database
- ✅ Messages persist across devices

---

## 📊 Architecture

```
Before: localStorage (browser only)
After:  PostgreSQL RDS (persistent, multi-device)
```

---

## 🔍 Verify Data in Database

```bash
# Connect to RDS
psql -h database-2-instance-1.crwu46wug6kx.ap-south-1.rds.amazonaws.com \
     -p 5432 -U postgres -d company_db

# View sessions
SELECT * FROM chat_sessions;

# View messages
SELECT * FROM chat_messages;
```

---

## 📚 Full Documentation

- **Setup Guide**: `BackendAPI/RDS_SETUP_GUIDE.md`
- **Implementation Details**: `BackendAPI/IMPLEMENTATION_SUMMARY.md`
- **Database Schema**: `BackendAPI/database_schema.sql`

---

## 🎯 Key Features

✅ **Automatic Migration**: localStorage → RDS on first login  
✅ **Persistent Storage**: Chat history saved in PostgreSQL  
✅ **Multi-Device**: Access chats from any device  
✅ **Fast Queries**: Optimized with indexes  
✅ **Fallback Support**: Works offline with localStorage  

---

## 🐛 Troubleshooting

**Backend won't start?**
- Check `.env` file exists
- Verify RDS credentials
- Run `python database.py` to test connection

**Frontend shows old data?**
- Clear browser localStorage
- Refresh page
- Migration will run automatically

**Database connection fails?**
- Check RDS security group allows port 5432
- Verify your IP is whitelisted
- Check RDS is publicly accessible

---

## ✅ Success!

Your chat history is now stored in PostgreSQL RDS! 🎉

**Next Steps:**
- Test with multiple users
- Monitor database performance
- Set up automated backups
- Review security settings

---

**Need Help?** Check `BackendAPI/RDS_SETUP_GUIDE.md` for detailed troubleshooting.
