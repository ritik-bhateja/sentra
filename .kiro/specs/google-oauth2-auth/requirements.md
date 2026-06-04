# Google OAuth2 Authentication - Requirements

## 📋 Overview

Implement Google OAuth2 authentication for the Sentra Insurance chatbot application with JWT tokens stored in HTTP-only cookies for secure session management.

---

## 🎯 Goals

1. Replace current localStorage-based authentication with Google OAuth2
2. Store JWT tokens in secure HTTP-only cookies
3. Create users table in RDS to store authenticated users
4. Implement protected routes on both frontend and backend
5. Maintain user session across page refreshes

---

## 👥 User Stories

### US-1: User Login with Google
**As a** user  
**I want to** login using my Google account  
**So that** I can securely access the insurance chatbot without managing passwords

**Acceptance Criteria:**
- User sees "Sign in with Google" button on login page
- Clicking button redirects to Google OAuth consent screen
- After successful authentication, user is redirected back to app
- User's email is stored in database
- JWT token is stored in HTTP-only cookie
- User is redirected to chat interface

---

### US-2: Automatic Session Restoration
**As a** returning user  
**I want to** stay logged in across page refreshes  
**So that** I don't have to login every time

**Acceptance Criteria:**
- JWT token is validated on page load
- If valid, user is automatically logged in
- If invalid/expired, user is redirected to login
- Token expiry is set to 7 days

---

### US-3: User Logout
**As a** logged-in user  
**I want to** logout from the application  
**So that** I can secure my account on shared devices

**Acceptance Criteria:**
- Logout button clears JWT cookie
- User is redirected to login page
- Subsequent API calls fail authentication

---

### US-4: Protected API Routes
**As a** system administrator  
**I want to** protect API endpoints with authentication  
**So that** only authenticated users can access chat and session data

**Acceptance Criteria:**
- All `/api/*` and `/query` endpoints require valid JWT
- Requests without valid JWT return 401 Unauthorized
- JWT contains user ID and email
- Token expiration is validated on each request

---

## 🏗️ Technical Requirements

### Backend Requirements

#### 1. Database Schema
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. Environment Variables
```env
# Google OAuth2
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback

# JWT Configuration
JWT_SECRET_KEY=your-random-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=7

# Cookie Configuration
COOKIE_DOMAIN=localhost
COOKIE_SECURE=False  # True in production with HTTPS
COOKIE_SAMESITE=Lax
```

#### 3. New Dependencies
- `PyJWT` - JWT token generation and validation
- `google-auth` - Google OAuth2 client
- `google-auth-oauthlib` - OAuth2 flow helpers
- `google-auth-httplib2` - HTTP transport for Google APIs

#### 4. New API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/auth/google` | Initiates Google OAuth flow | No |
| GET | `/auth/google/callback` | Handles OAuth callback | No |
| POST | `/auth/logout` | Clears JWT cookie | Yes |
| GET | `/auth/me` | Returns current user info | Yes |
| GET | `/auth/verify` | Verifies JWT token | Yes |

#### 5. Authentication Middleware
- Dependency function `get_current_user()` for FastAPI
- Validates JWT from cookie
- Extracts user_id and email from token
- Raises 401 if token invalid/missing

---

### Frontend Requirements

#### 1. New Dependencies
```json
{
  "react-cookie": "^7.0.0",
  "js-cookie": "^3.0.5",
  "@react-oauth/google": "^0.12.1"
}
```

#### 2. New Components
- `Login.jsx` - Replace with Google OAuth button
- `ProtectedRoute.jsx` - Wrapper for authenticated routes
- `AuthContext.jsx` - Global authentication state

#### 3. Cookie Management
- Use `js-cookie` for reading JWT token
- Use `react-cookie` for React integration
- Token name: `sentra_jwt_token`
- HTTP-only flag for security
- Secure flag in production
- SameSite=Lax for CSRF protection

#### 4. API Client Updates
- Include credentials in all fetch requests
- Handle 401 responses (redirect to login)
- Automatic token refresh (optional)

---

## 🔐 Security Requirements

### 1. JWT Token Security
- ✅ Minimum 32-character secret key
- ✅ HS256 algorithm
- ✅ Short expiration (7 days)
- ✅ Include user_id and email in payload
- ✅ Validate on every request

### 2. Cookie Security
- ✅ HTTP-only flag (prevent XSS)
- ✅ Secure flag in production (HTTPS only)
- ✅ SameSite=Lax (CSRF protection)
- ✅ Domain-specific
- ✅ Path=/ for all routes

### 3. OAuth Security
- ✅ Use state parameter to prevent CSRF
- ✅ Validate redirect URI
- ✅ Store credentials in environment variables
- ✅ Use HTTPS in production
- ✅ Verify Google ID token

### 4. API Security
- ✅ Validate JWT signature
- ✅ Check token expiration
- ✅ Verify user exists in database
- ✅ Rate limiting (optional)
- ✅ CORS configuration

---

## 📊 Data Flow

### Login Flow
```
1. User clicks "Sign in with Google"
   ↓
2. Frontend redirects to /auth/google
   ↓
3. Backend generates OAuth URL with state parameter
   ↓
4. User redirects to Google consent screen
   ↓
5. User approves permissions
   ↓
6. Google redirects to /auth/google/callback?code=...
   ↓
7. Backend exchanges code for Google tokens
   ↓
8. Backend verifies Google ID token
   ↓
9. Backend creates/updates user in database
   ↓
10. Backend generates JWT token
   ↓
11. Backend sets JWT in HTTP-only cookie
   ↓
12. Backend redirects to frontend (http://localhost:5173)
   ↓
13. Frontend detects cookie and loads user data
   ↓
14. User lands on chat interface
```

### Protected Request Flow
```
1. Frontend makes API request
   ↓
2. Browser automatically includes JWT cookie
   ↓
3. Backend middleware extracts JWT from cookie
   ↓
4. Backend validates JWT signature and expiration
   ↓
5. Backend extracts user_id from JWT
   ↓
6. Backend attaches user to request context
   ↓
7. Route handler processes request with user context
   ↓
8. Response sent back to frontend
```

### Logout Flow
```
1. User clicks logout button
   ↓
2. Frontend calls POST /auth/logout
   ↓
3. Backend clears JWT cookie (sets Max-Age=0)
   ↓
4. Frontend redirects to login page
   ↓
5. Frontend clears any local auth state
```

---

## 🧪 Testing Requirements

### Backend Tests
- [ ] OAuth callback with valid code
- [ ] OAuth callback with invalid code
- [ ] JWT generation and validation
- [ ] User creation on first login
- [ ] User update on subsequent logins
- [ ] Protected endpoint with valid token
- [ ] Protected endpoint with invalid token
- [ ] Protected endpoint with expired token
- [ ] Protected endpoint without token
- [ ] Logout clears cookie

### Frontend Tests
- [ ] Login button redirects to OAuth
- [ ] Successful login redirects to chat
- [ ] Token persists across page refresh
- [ ] Logout clears token and redirects
- [ ] Protected routes redirect if not authenticated
- [ ] API calls include credentials
- [ ] 401 response redirects to login

### Integration Tests
- [ ] Full login flow end-to-end
- [ ] Session restoration on page refresh
- [ ] Multiple users can login simultaneously
- [ ] Token expiration after 7 days
- [ ] Logout from one tab affects other tabs

---

## 🚀 Migration Strategy

### Phase 1: Backend Implementation
1. Add users table to database
2. Install OAuth and JWT dependencies
3. Create auth endpoints
4. Implement authentication middleware
5. Protect existing API endpoints
6. Test with Postman/curl

### Phase 2: Frontend Implementation
1. Install cookie and OAuth dependencies
2. Update Login component with Google button
3. Create AuthContext for global state
4. Update API client to include credentials
5. Add protected route wrapper
6. Update ChatInterface to use auth context

### Phase 3: Migration
1. Deploy backend with auth endpoints
2. Deploy frontend with OAuth
3. Existing users login with Google
4. Email mapping: Google email → user_id
5. Migrate chat sessions to new user IDs
6. Remove localStorage user_id after migration

---

## 📋 Configuration Checklist

### Google Cloud Console Setup
- [ ] Create new project (or use existing)
- [ ] Enable Google+ API
- [ ] Create OAuth 2.0 credentials
- [ ] Add authorized redirect URI: `http://localhost:5000/auth/google/callback`
- [ ] Add production redirect URI (when deploying)
- [ ] Copy Client ID and Client Secret
- [ ] Configure OAuth consent screen

### Backend Configuration
- [ ] Add environment variables to `.env`
- [ ] Generate secure JWT secret (32+ characters)
- [ ] Update CORS to allow credentials
- [ ] Create users table in RDS
- [ ] Test OAuth callback locally

### Frontend Configuration
- [ ] Install dependencies
- [ ] Configure API base URL with credentials
- [ ] Set cookie domain correctly
- [ ] Test login flow locally

---

## 🎯 Success Criteria

1. ✅ Users can login with Google account
2. ✅ JWT token stored in HTTP-only cookie
3. ✅ User data stored in PostgreSQL users table
4. ✅ All API endpoints protected with authentication
5. ✅ Session persists across page refreshes
6. ✅ Users can logout and login again
7. ✅ No authentication data in localStorage
8. ✅ Secure cookie configuration
9. ✅ Working on localhost (development)
10. ✅ Ready for production deployment

---

## 📚 References

- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [HTTP Cookie Security](https://owasp.org/www-community/controls/SecureCookieAttribute)

---

## 🔄 Future Enhancements

- [ ] Refresh token mechanism
- [ ] Multiple OAuth providers (GitHub, Microsoft)
- [ ] Two-factor authentication
- [ ] Session management dashboard
- [ ] Automatic session renewal
- [ ] Device tracking
- [ ] Login notifications

---

**Status:** ✅ Requirements Complete - Ready for Design Phase  
**Created:** December 2025  
**Version:** 1.0
