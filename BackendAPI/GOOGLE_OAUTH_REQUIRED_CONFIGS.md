# 🔐 Google OAuth2 Setup - Required Configurations

## 📋 Overview

This document lists all required configurations for implementing Google OAuth2 authentication in the Sentra Insurance application.

---

## 🎯 Step 1: Google Cloud Console Setup

### A. Create/Select Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click project dropdown → **New Project**
3. **Project Name**: `Sentra Insurance`
4. Click **Create**

### B. Enable APIs

1. Go to **APIs & Services** → **Library**
2. Search for **Google+ API**
3. Click **Enable**

### C. Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type
3. Click **Create**

**Fill in the following:**

| Field | Value |
|-------|-------|
| **App name** | Sentra Insurance |
| **User support email** | your-email@example.com |
| **App logo** | (Optional) Upload logo |
| **Application home page** | http://localhost:5173 |
| **Authorized domains** | localhost (for development) |
| **Developer contact email** | your-email@example.com |

4. **Scopes**: Click **Add or Remove Scopes**
   - Select: `userinfo.email`
   - Select: `userinfo.profile`
   - Select: `openid`
5. Click **Save and Continue**
6. **Test users** (for development):
   - Add your Gmail address
   - Add team members' Gmail addresses
7. Click **Save and Continue**
8. Review and click **Back to Dashboard**

### D. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. **Application type**: `Web application`
4. **Name**: `Sentra Insurance Web Client`

**Authorized JavaScript origins:**
```
http://localhost:5173
http://localhost:5000
```

**Authorized redirect URIs:**
```
http://localhost:5000/auth/google/callback
```

5. Click **Create**
6. **IMPORTANT**: Copy the **Client ID** and **Client Secret**

**Example:**
```
Client ID: 123456789012-abcdefghijklmnop.apps.googleusercontent.com
Client Secret: GOCSPX-abcdefghijklmnop
```

---

## 🔧 Step 2: Backend Configuration

### A. Update `BackendAPI/.env`

Add these lines to your `.env` file:

```env
# ============================================
# Google OAuth2 Configuration
# ============================================
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback

# ============================================
# JWT Configuration
# ============================================
JWT_SECRET_KEY=your-random-64-character-secret-key-here-make-it-really-long
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=7

# ============================================
# Cookie Configuration
# ============================================
COOKIE_DOMAIN=localhost
COOKIE_SECURE=False
COOKIE_SAMESITE=Lax

# ============================================
# Frontend URL
# ============================================
FRONTEND_URL=http://localhost:5173

# ============================================
# Existing Database Configuration (keep as is)
# ============================================
DB_HOST=database-2-instance-1.crwu46wug6kx.ap-south-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=company_db
DB_USER=postgres
DB_PASSWORD=lumiq121
DB_SSLMODE=require

# ============================================
# API Configuration
# ============================================
API_PORT=5000
```

### B. Generate JWT Secret Key

Run this Python command to generate a secure secret key:

```python
import secrets
print(secrets.token_urlsafe(64))
```

Or use this bash command:
```bash
openssl rand -base64 64 | tr -d '\n'
```

**Copy the output and use it as `JWT_SECRET_KEY`**

---

## 🗄️ Step 3: Database Configuration

### A. Create Users Table

Run this SQL in your PostgreSQL database:

```sql
-- File: BackendAPI/auth_schema.sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

**How to run:**

```bash
# Option 1: Using psql
psql -h database-2-instance-1.crwu46wug6kx.ap-south-1.rds.amazonaws.com \
     -p 5432 \
     -U postgres \
     -d company_db \
     -f auth_schema.sql

# Option 2: Using Python script
python setup_auth_database.py
```

---

## 🎨 Step 4: Frontend Configuration

### A. Install Dependencies

```bash
cd Frontend
npm install react-cookie js-cookie react-router-dom
```

### B. Update `Frontend/.env`

Create or update `.env` file:

```env
VITE_API_URL=http://localhost:5000
```

---

## 🚀 Step 5: Production Configuration (Future)

### When deploying to production, update these:

#### Google Cloud Console:

**Authorized JavaScript origins:**
```
https://yourdomain.com
https://www.yourdomain.com
```

**Authorized redirect URIs:**
```
https://yourdomain.com/auth/google/callback
https://www.yourdomain.com/auth/google/callback
```

#### Backend `.env`:

```env
# Production OAuth
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/google/callback

# Production Cookie
COOKIE_DOMAIN=yourdomain.com
COOKIE_SECURE=True  # HTTPS only
COOKIE_SAMESITE=Lax

# Production Frontend
FRONTEND_URL=https://yourdomain.com
```

#### Frontend `.env`:

```env
VITE_API_URL=https://yourdomain.com
```

---

## ✅ Configuration Checklist

### Google Cloud Console
- [ ] Project created
- [ ] Google+ API enabled
- [ ] OAuth consent screen configured
- [ ] Test users added
- [ ] OAuth 2.0 credentials created
- [ ] Authorized redirect URIs added
- [ ] Client ID copied
- [ ] Client Secret copied

### Backend Configuration
- [ ] `.env` file updated with Google credentials
- [ ] JWT secret key generated (64+ characters)
- [ ] Cookie configuration set
- [ ] Frontend URL configured
- [ ] Database credentials verified

### Database Setup
- [ ] Users table created
- [ ] Email index created
- [ ] Connection tested

### Frontend Configuration
- [ ] Dependencies installed
- [ ] `.env` file created
- [ ] API URL configured

---

## 🧪 Test Configuration

### Test Backend Configuration

```bash
cd BackendAPI
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('✅ Checking configuration...')
print(f'Google Client ID: {os.getenv(\"GOOGLE_CLIENT_ID\")[:20]}...')
print(f'Google Secret: {\"✅ Set\" if os.getenv(\"GOOGLE_CLIENT_SECRET\") else \"❌ Missing\"}')
print(f'JWT Secret: {\"✅ Set\" if os.getenv(\"JWT_SECRET_KEY\") else \"❌ Missing\"}')
print(f'Redirect URI: {os.getenv(\"GOOGLE_REDIRECT_URI\")}')
print(f'Frontend URL: {os.getenv(\"FRONTEND_URL\")}')
"
```

### Test Frontend Configuration

```bash
cd Frontend
cat .env
```

Expected output:
```
VITE_API_URL=http://localhost:5000
```

---

## 📝 Environment Variables Reference

### Required Backend Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `GOOGLE_CLIENT_ID` | `123...xyz.apps.googleusercontent.com` | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | `GOCSPX-abcdef...` | From Google Cloud Console |
| `GOOGLE_REDIRECT_URI` | `http://localhost:5000/auth/google/callback` | OAuth callback URL |
| `JWT_SECRET_KEY` | `your-64-char-secret...` | Generated secure random string |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRATION_DAYS` | `7` | Token expiration in days |
| `COOKIE_DOMAIN` | `localhost` | Cookie domain |
| `COOKIE_SECURE` | `False` | HTTPS only (True in production) |
| `COOKIE_SAMESITE` | `Lax` | CSRF protection |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend redirect URL |

### Required Frontend Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:5000` | Backend API URL |

---

## 🐛 Troubleshooting

### Issue: "redirect_uri_mismatch" error

**Solution:**
1. Check `GOOGLE_REDIRECT_URI` in `.env` matches exactly
2. Verify redirect URI in Google Cloud Console
3. Must be exactly: `http://localhost:5000/auth/google/callback`
4. No trailing slashes
5. Check protocol (http vs https)

### Issue: "Invalid client" error

**Solution:**
1. Verify `GOOGLE_CLIENT_ID` is correct
2. Verify `GOOGLE_CLIENT_SECRET` is correct
3. Check for extra spaces in `.env` file
4. Restart backend after changing `.env`

### Issue: JWT cookie not set

**Solution:**
1. Check `COOKIE_DOMAIN` matches your domain
2. For localhost, use `localhost` (not `127.0.0.1`)
3. Verify CORS allows credentials
4. Check browser cookie settings

### Issue: "Not authenticated" after login

**Solution:**
1. Check browser receives cookie (DevTools → Application → Cookies)
2. Verify cookie name is `sentra_jwt_token`
3. Check `credentials: 'include'` in fetch requests
4. Verify CORS allows credentials

---

## 🔒 Security Best Practices

### Development

- ✅ Use `COOKIE_SECURE=False` for localhost
- ✅ Add only trusted test users in OAuth consent
- ✅ Keep credentials in `.env` (never commit)
- ✅ Use localhost domains only

### Production

- ✅ Set `COOKIE_SECURE=True` (requires HTTPS)
- ✅ Use strong JWT secret (64+ characters)
- ✅ Set specific `COOKIE_DOMAIN`
- ✅ Use `SameSite=Lax` or `Strict`
- ✅ Enable OAuth consent screen review
- ✅ Limit authorized domains
- ✅ Rotate secrets regularly
- ✅ Use environment-specific credentials

---

## 📞 Support

If you encounter issues:

1. Check all configurations match this guide
2. Verify `.env` file has no syntax errors
3. Restart both backend and frontend
4. Check browser console for errors
5. Check backend logs for detailed errors
6. Verify database connection works
7. Test with a fresh browser session (incognito)

---

## 🎯 Next Steps

After completing all configurations:

1. ✅ Verify all checkboxes above
2. ✅ Test configuration scripts
3. ✅ Start implementation (see `tasks.md`)
4. ✅ Run integration tests
5. ✅ Deploy to production

---

**Last Updated:** December 2025  
**Version:** 1.0  
**Status:** ✅ Ready for Implementation
