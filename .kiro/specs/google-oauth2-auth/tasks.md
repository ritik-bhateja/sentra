# Google OAuth2 Authentication - Implementation Tasks

## 📋 Task Overview

**Total Tasks:** 20  
**Estimated Time:** 8-10 hours  
**Priority:** High

---

## 🎯 Phase 1: Setup & Configuration (Tasks 1-4)

### ✅ Task 1: Google Cloud Console Setup
**Priority:** Critical  
**Estimated Time:** 30 minutes  
**Dependencies:** None

**Steps:**
1. Create/select Google Cloud project
2. Enable Google+ API
3. Create OAuth 2.0 credentials
4. Configure OAuth consent screen
5. Add authorized redirect URIs:
   - Development: `http://localhost:5000/auth/google/callback`
   - Production: `https://yourdomain.com/auth/google/callback`
6. Copy Client ID and Client Secret

**Deliverables:**
- Google Client ID
- Google Client Secret
- OAuth consent screen configured

**Acceptance Criteria:**
- OAuth credentials created successfully
- Redirect URIs configured
- Test credentials available

---

### ✅ Task 2: Backend Dependencies Installation
**Priority:** Critical  
**Estimated Time:** 15 minutes  
**Dependencies:** Task 1

**Steps:**
1. Add dependencies to `BackendAPI/requirements.txt`
2. Install dependencies
3. Test imports

**Code Changes:**
```bash
# Add to requirements.txt
PyJWT==2.8.0
google-auth==2.25.2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
```

**Acceptance Criteria:**
- All dependencies installed without errors
- Imports work correctly

---

### ✅ Task 3: Environment Configuration
**Priority:** Critical  
**Estimated Time:** 15 minutes  
**Dependencies:** Task 1, Task 2

**Steps:**
1. Update `BackendAPI/.env` with OAuth and JWT config
2. Generate secure JWT secret key
3. Update `.env.example`

**Code Changes:**
```env
# Google OAuth2
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback

# JWT Configuration
JWT_SECRET_KEY=your-random-64-char-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=7

# Cookie Configuration
COOKIE_DOMAIN=localhost
COOKIE_SECURE=False
COOKIE_SAMESITE=Lax

# Frontend URL
FRONTEND_URL=http://localhost:5173
```

**Acceptance Criteria:**
- All config variables added
- JWT secret is 64+ characters
- `.env` file not committed to git

---

### ✅ Task 4: Database Schema Update
**Priority:** Critical  
**Estimated Time:** 30 minutes  
**Dependencies:** None

**Steps:**
1. Create `users` table SQL
2. Add migration script
3. Update `chat_sessions` table (optional foreign key)
4. Run migration

**Code Changes:**
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

**Deliverables:**
- `auth_schema.sql` file
- Migration script

**Acceptance Criteria:**
- Users table created successfully
- Index on email column exists
- Migration script runs without errors

---

## 🔧 Phase 2: Backend Implementation (Tasks 5-12)

### ✅ Task 5: Create User Model
**Priority:** High  
**Estimated Time:** 20 minutes  
**Dependencies:** Task 4

**Steps:**
1. Add User model to `BackendAPI/models.py`
2. Define relationships
3. Add helper methods

**Code Changes:**
```python
# File: BackendAPI/models.py
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_login = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "created_at": int(self.created_at.timestamp() * 1000),
            "last_login": int(self.last_login.timestamp() * 1000)
        }
```

**Acceptance Criteria:**
- User model defined
- to_dict() method works
- Email index created

---

### ✅ Task 6: Implement JWT Handler
**Priority:** Critical  
**Estimated Time:** 45 minutes  
**Dependencies:** Task 2, Task 3

**Steps:**
1. Create `BackendAPI/auth/` directory
2. Create `jwt_handler.py`
3. Implement token creation
4. Implement token verification
5. Add unit tests

**Code Changes:**
```python
# File: BackendAPI/auth/jwt_handler.py
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import os

class JWTHandler:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.expiration_days = int(os.getenv("JWT_EXPIRATION_DAYS", 7))
    
    def create_token(self, user_id: int, email: str) -> str:
        """Generate JWT token"""
        expire = datetime.utcnow() + timedelta(days=self.expiration_days)
        payload = {
            "sub": str(user_id),
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

jwt_handler = JWTHandler()
```

**Deliverables:**
- `auth/jwt_handler.py`
- Unit tests

**Acceptance Criteria:**
- Token creation works
- Token verification works
- Expired tokens rejected
- Invalid tokens rejected

---

### ✅ Task 7: Implement OAuth Handler
**Priority:** Critical  
**Estimated Time:** 1 hour  
**Dependencies:** Task 2, Task 3

**Steps:**
1. Create `BackendAPI/auth/oauth.py`
2. Implement Google OAuth flow
3. Implement token exchange
4. Implement ID token verification

**Code Changes:**
```python
# File: BackendAPI/auth/oauth.py
from google.oauth2 import id_token
from google.auth.transport import requests
from google_auth_oauthlib.flow import Flow
import os
import secrets

class GoogleOAuthHandler:
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
        self.scopes = [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ]
    
    def get_authorization_url(self) -> tuple[str, str]:
        """Generate Google OAuth authorization URL and state"""
        state = secrets.token_urlsafe(32)
        flow = self._create_flow()
        flow.state = state
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='select_account'
        )
        return authorization_url, state
    
    def exchange_code(self, code: str, state: str) -> dict:
        """Exchange authorization code for user info"""
        flow = self._create_flow()
        flow.state = state
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            requests.Request(),
            self.client_id
        )
        
        return {
            "email": id_info.get("email"),
            "name": id_info.get("name"),
            "picture": id_info.get("picture"),
            "sub": id_info.get("sub")
        }
    
    def _create_flow(self) -> Flow:
        """Create OAuth flow"""
        return Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uris": [self.redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )

oauth_handler = GoogleOAuthHandler()
```

**Deliverables:**
- `auth/oauth.py`

**Acceptance Criteria:**
- Authorization URL generated
- Code exchange works
- ID token verified
- User info extracted

---

### ✅ Task 8: Implement Authentication Middleware
**Priority:** Critical  
**Estimated Time:** 45 minutes  
**Dependencies:** Task 5, Task 6

**Steps:**
1. Create `BackendAPI/auth/middleware.py`
2. Implement get_current_user dependency
3. Add error handling

**Code Changes:**
```python
# File: BackendAPI/auth/middleware.py
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth.jwt_handler import jwt_handler

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate JWT from cookie, return current user"""
    
    token = request.cookies.get("sentra_jwt_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    payload = jwt_handler.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user
```

**Deliverables:**
- `auth/middleware.py`

**Acceptance Criteria:**
- JWT extracted from cookie
- Token validated
- User loaded from database
- 401 error on invalid token

---

### ✅ Task 9: Create Auth Endpoints
**Priority:** Critical  
**Estimated Time:** 1.5 hours  
**Dependencies:** Task 6, Task 7, Task 8

**Steps:**
1. Add auth routes to `Agent_Trigger.py`
2. Implement `/auth/google` endpoint
3. Implement `/auth/google/callback` endpoint
4. Implement `/auth/logout` endpoint
5. Implement `/auth/me` endpoint
6. Implement `/auth/verify` endpoint

**Code Changes:**
```python
# File: BackendAPI/Agent_Trigger.py
from fastapi.responses import RedirectResponse
from auth.oauth import oauth_handler
from auth.jwt_handler import jwt_handler
from auth.middleware import get_current_user
from models import User
import os

# Store states temporarily (use Redis in production)
oauth_states = {}

@app.get("/auth/google")
async def auth_google():
    """Initiate Google OAuth flow"""
    authorization_url, state = oauth_handler.get_authorization_url()
    oauth_states[state] = True  # Store state
    return RedirectResponse(url=authorization_url)

@app.get("/auth/google/callback")
async def auth_google_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    # Validate state
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    del oauth_states[state]
    
    # Exchange code for user info
    user_info = oauth_handler.exchange_code(code, state)
    email = user_info["email"]
    
    # Create or update user
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.last_login = datetime.utcnow()
    else:
        user = User(email=email)
        db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate JWT
    token = jwt_handler.create_token(user.id, user.email)
    
    # Redirect to frontend with cookie
    response = RedirectResponse(url=os.getenv("FRONTEND_URL", "http://localhost:5173"))
    response.set_cookie(
        key="sentra_jwt_token",
        value=token,
        httponly=True,
        secure=os.getenv("COOKIE_SECURE", "False") == "True",
        samesite=os.getenv("COOKIE_SAMESITE", "lax"),
        max_age=604800,  # 7 days
        domain=os.getenv("COOKIE_DOMAIN", "localhost"),
        path="/"
    )
    return response

@app.post("/auth/logout")
async def auth_logout(current_user: User = Depends(get_current_user)):
    """Logout user"""
    response = {"message": "Logged out successfully"}
    response = JSONResponse(content=response)
    response.delete_cookie(key="sentra_jwt_token", path="/")
    return response

@app.get("/auth/me")
async def auth_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user.to_dict()

@app.get("/auth/verify")
async def auth_verify(current_user: User = Depends(get_current_user)):
    """Verify JWT token"""
    return {"valid": True, "user_id": current_user.id}
```

**Deliverables:**
- 5 new auth endpoints

**Acceptance Criteria:**
- OAuth flow works end-to-end
- JWT cookie set correctly
- Logout clears cookie
- /auth/me returns user data
- /auth/verify validates token

---

### ✅ Task 10: Update CORS Configuration
**Priority:** High  
**Estimated Time:** 15 minutes  
**Dependencies:** Task 9

**Steps:**
1. Update CORS middleware in `Agent_Trigger.py`
2. Enable credentials
3. Set specific origin

**Code Changes:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        os.getenv("FRONTEND_URL", "http://localhost:5173")
    ],
    allow_credentials=True,  # CRITICAL for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Acceptance Criteria:**
- CORS allows credentials
- Frontend origin whitelisted
- Cookies sent correctly

---

### ✅ Task 11: Protect Existing Endpoints
**Priority:** High  
**Estimated Time:** 45 minutes  
**Dependencies:** Task 8, Task 9

**Steps:**
1. Add `current_user` dependency to all protected endpoints
2. Update endpoints to use authenticated user
3. Test authentication requirement

**Code Changes:**
```python
# Update existing endpoints
@app.post("/api/sessions")
async def create_session(
    session: SessionCreate,
    current_user: User = Depends(get_current_user),  # Add this
    db: Session = Depends(get_db)
):
    # Use current_user.id instead of request.user_id
    ...

@app.get("/api/sessions/{user_id}")
async def get_user_sessions(
    user_id: str,
    current_user: User = Depends(get_current_user),  # Add this
    db: Session = Depends(get_db)
):
    # Verify user_id matches current_user
    ...
```

**Acceptance Criteria:**
- All protected endpoints require authentication
- Unauthenticated requests return 401
- User context available in all handlers

---

### ✅ Task 12: Backend Testing
**Priority:** High  
**Estimated Time:** 1 hour  
**Dependencies:** Tasks 5-11

**Steps:**
1. Test OAuth flow with Postman/browser
2. Test JWT generation and validation
3. Test protected endpoints
4. Test logout
5. Test error cases

**Test Cases:**
- OAuth initiation redirects to Google
- Callback creates user in database
- JWT cookie set correctly
- Protected endpoint works with cookie
- Protected endpoint fails without cookie
- Logout clears cookie

**Acceptance Criteria:**
- All tests pass
- No errors in logs
- Cookies set correctly

---

## 🎨 Phase 3: Frontend Implementation (Tasks 13-18)

### ✅ Task 13: Install Frontend Dependencies
**Priority:** Critical  
**Estimated Time:** 15 minutes  
**Dependencies:** None

**Steps:**
1. Add dependencies to `Frontend/package.json`
2. Install dependencies

**Code Changes:**
```bash
cd Frontend
npm install react-cookie js-cookie
```

**Acceptance Criteria:**
- Dependencies installed
- No version conflicts

---

### ✅ Task 14: Create Auth API Service
**Priority:** High  
**Estimated Time:** 30 minutes  
**Dependencies:** Task 13

**Steps:**
1. Create `Frontend/src/services/authApi.js`
2. Implement auth API calls

**Code Changes:**
```javascript
// File: Frontend/src/services/authApi.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export async function getCurrentUser() {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    credentials: 'include',  // CRITICAL: Include cookies
  });
  if (!response.ok) throw new Error('Not authenticated');
  return await response.json();
}

export async function logout() {
  const response = await fetch(`${API_BASE_URL}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!response.ok) throw new Error('Logout failed');
  return await response.json();
}

export async function verifyToken() {
  const response = await fetch(`${API_BASE_URL}/auth/verify`, {
    credentials: 'include',
  });
  return response.ok;
}
```

**Deliverables:**
- `authApi.js` file

**Acceptance Criteria:**
- All auth API calls implemented
- Credentials included in requests

---

### ✅ Task 15: Create AuthContext
**Priority:** Critical  
**Estimated Time:** 1 hour  
**Dependencies:** Task 13, Task 14

**Steps:**
1. Create `Frontend/src/contexts/` directory
2. Create `AuthContext.jsx`
3. Implement auth state management
4. Add login, logout, checkAuth methods

**Code Changes:**
```javascript
// File: Frontend/src/contexts/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';
import Cookies from 'js-cookie';
import * as authApi from '../services/authApi';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = Cookies.get('sentra_jwt_token');
      if (token) {
        const userData = await authApi.getCurrentUser();
        setUser(userData);
        setIsAuthenticated(true);
      }
    } catch (error) {
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const login = () => {
    window.location.href = `${import.meta.env.VITE_API_URL}/auth/google`;
  };

  const logout = async () => {
    try {
      await authApi.logout();
      setUser(null);
      setIsAuthenticated(false);
      Cookies.remove('sentra_jwt_token');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, isAuthenticated, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

**Deliverables:**
- `AuthContext.jsx`

**Acceptance Criteria:**
- Auth state managed globally
- Check auth on mount
- Login redirects to OAuth
- Logout clears state

---

### ✅ Task 16: Create Protected Route Component
**Priority:** High  
**Estimated Time:** 30 minutes  
**Dependencies:** Task 15

**Steps:**
1. Create `Frontend/src/components/ProtectedRoute.jsx`
2. Implement route protection logic

**Code Changes:**
```javascript
// File: Frontend/src/components/ProtectedRoute.jsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        <p>Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default ProtectedRoute;
```

**Deliverables:**
- `ProtectedRoute.jsx`

**Acceptance Criteria:**
- Unauthenticated users redirected to login
- Loading state shown during auth check

---

### ✅ Task 17: Update Login Component
**Priority:** High  
**Estimated Time:** 45 minutes  
**Dependencies:** Task 15

**Steps:**
1. Update `Frontend/src/components/Login.jsx`
2. Replace with Google sign-in button
3. Update styling

**Code Changes:**
```javascript
// File: Frontend/src/components/Login.jsx
import { useAuth } from '../contexts/AuthContext';
import './Login.css';

function Login() {
  const { login } = useAuth();

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>Sentra Insurance</h1>
          <p>Your AI-powered insurance assistant</p>
        </div>
        
        <button onClick={login} className="google-signin-button">
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Sign in with Google
        </button>
        
        <div className="login-footer">
          <p>Secure authentication powered by Google</p>
        </div>
      </div>
    </div>
  );
}

export default Login;
```

**Deliverables:**
- Updated `Login.jsx`
- Updated `Login.css`

**Acceptance Criteria:**
- Google button displayed
- Click redirects to OAuth
- Clean, modern design

---

### ✅ Task 18: Update App.jsx with Auth
**Priority:** High  
**Estimated Time:** 45 minutes  
**Dependencies:** Tasks 15, 16, 17

**Steps:**
1. Wrap app with AuthProvider
2. Add protected routes
3. Remove localStorage authentication
4. Update routing

**Code Changes:**
```javascript
// File: Frontend/src/App.jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Login from './components/Login';
import ChatInterface from './components/ChatInterface';
import ProtectedRoute from './components/ProtectedRoute';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <ChatInterface />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
```

**Deliverables:**
- Updated `App.jsx`

**Acceptance Criteria:**
- Auth provider wraps entire app
- Protected routes work
- Login route accessible
- Invalid routes redirect to home

---

## 🧪 Phase 4: Testing & Documentation (Tasks 19-20)

### ✅ Task 19: Integration Testing
**Priority:** High  
**Estimated Time:** 1.5 hours  
**Dependencies:** All previous tasks

**Test Cases:**
1. **Login Flow**
   - Click "Sign in with Google"
   - Complete OAuth flow
   - Redirect to chat interface
   - User data loaded

2. **Session Persistence**
   - Login successfully
   - Refresh page
   - Still logged in
   - User data persists

3. **Protected Routes**
   - Try accessing chat without login
   - Redirected to login page
   - After login, can access chat

4. **Logout**
   - Click logout
   - Cookie cleared
   - Redirected to login
   - Cannot access protected routes

5. **API Authentication**
   - Send message in chat
   - Request includes JWT cookie
   - Response successful
   - Without cookie, 401 error

**Acceptance Criteria:**
- All test cases pass
- No console errors
- Smooth user experience

---

### ✅ Task 20: Documentation
**Priority:** Medium  
**Estimated Time:** 1 hour  
**Dependencies:** All previous tasks

**Deliverables:**
1. `GOOGLE_OAUTH_SETUP.md` - Google Cloud Console setup guide
2. `AUTH_API_DOCS.md` - API endpoint documentation
3. Update `README.md` with auth instructions
4. Add troubleshooting guide

**Contents:**
- Google Cloud Console setup steps (with screenshots)
- Environment variable configuration
- Local development setup
- Production deployment checklist
- Common issues and solutions
- Security best practices

**Acceptance Criteria:**
- Complete setup documentation
- API documentation with examples
- Troubleshooting guide
- Security notes included

---

## 📊 Task Summary

### By Phase

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Setup | 4 | 1.5 hours |
| Phase 2: Backend | 8 | 6 hours |
| Phase 3: Frontend | 6 | 4.5 hours |
| Phase 4: Testing | 2 | 2.5 hours |
| **Total** | **20** | **14.5 hours** |

### By Priority

| Priority | Tasks | Estimated Time |
|----------|-------|----------------|
| Critical | 9 | 7 hours |
| High | 10 | 6.5 hours |
| Medium | 1 | 1 hour |

---

## 🎯 Success Criteria

- [ ] All 20 tasks completed
- [ ] Google OAuth login works
- [ ] JWT tokens in HTTP-only cookies
- [ ] Users table populated
- [ ] All endpoints protected
- [ ] Session persists across refresh
- [ ] Logout works correctly
- [ ] No security vulnerabilities
- [ ] Documentation complete
- [ ] All tests passing

---

**Status:** ✅ Tasks Defined - Ready for Implementation  
**Created:** December 2025  
**Version:** 1.0
