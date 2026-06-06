from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import boto3
import json
import botocore
import uvicorn
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import uuid
import os

# Import database components
from database import get_db, test_connection
from models_v3 import ChatSession, ConversationTurn, User

# Import auth components
from auth.oauth import oauth_handler
from auth.jwt_handler import jwt_handler
from auth.middleware import get_current_user, require_admin
from auth.keycloak_client import KeycloakClient, resolve_role_for_email
from auth.rbac import filter_response_for_role, filter_messages_for_role
from role_sync import sync_users

# OAuth states storage (use Redis in production)
oauth_states = {}

# Keycloak client for RBAC role resolution
keycloak_client = KeycloakClient()

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if test_connection():
        print("✅ Database connected successfully")
    else:
        print("⚠️ Warning: Database connection failed")
    yield
    # Shutdown (if needed)

app = FastAPI(title="Sentra Insurance API V3", version="3.0.0", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,  # CRITICAL for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Pydantic Models
# ============================================

class QueryRequest(BaseModel):
    user_query: str
    user_id: str
    session_id: Optional[str] = None  # Optional: will create new if not provided
    user_email: Optional[str] = None

class SessionCreate(BaseModel):
    user_id: str
    session_title: Optional[str] = "New Chat"

class SessionUpdate(BaseModel):
    session_title: Optional[str] = None
    status: Optional[str] = None

class TurnCreate(BaseModel):
    session_id: str
    user_query: str
    assistant_response: Optional[dict] = None
    model_name: Optional[str] = "moonshotai.kimi-k2.5"
    status: Optional[str] = "COMPLETED"

# ============================================
# QUERY ENDPOINT — BEDROCK AGENTCORE
# ============================================

@app.post("/query")
async def send_to_bknd(request: QueryRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    config = botocore.config.Config(
        read_timeout=180,
        connect_timeout=10,
        retries={'max_attempts': 0}
    )

    print(f"Received request: {request.model_dump()}")
    
    # Validate user_id
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    # Get or create session
    try:
        if request.session_id:
            # Use existing session
            session = db.query(ChatSession).filter(
                ChatSession.session_id == uuid.UUID(request.session_id),
                ChatSession.status == 'ACTIVE'
            ).first()
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found or inactive")
            
            session_id_str = request.session_id
        else:
            # Create new session
            new_session = ChatSession(
                user_id=request.user_id,
                session_title="New Chat"
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            session_id_str = str(new_session.session_id)
            print(f"✅ Created new session: {session_id_str}")
        
        # Create pending turn
        new_turn = ConversationTurn(
            session_id=uuid.UUID(session_id_str),
            user_query=request.user_query,
            status='RUNNING'
        )
        db.add(new_turn)
        db.commit()
        db.refresh(new_turn)
        turn_id = str(new_turn.turn_id)
        turn_number = new_turn.turn_number
        
        print(f"✅ Created turn {turn_number} in session {session_id_str}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # Call Bedrock AgentCore
    client = boto3.client('bedrock-agentcore', region_name='ap-south-1', config=config)
    
    # Normalize user_email
    user_email = request.user_email
    if user_email and '@' not in user_email:
        user_email = f"{user_email}@sentra.com"
    elif not user_email:
        user_email = f"{request.user_id}@sentra.com" if '@' not in request.user_id else request.user_id
    
    bknd_payload = json.dumps({
        "user_query": request.user_query,
        "user_id": request.user_id,
        "session_id": session_id_str,
        "user_email": user_email
    })

    try:
        response = client.invoke_agent_runtime(
            agentRuntimeArn='arn:aws:bedrock-agentcore:ap-south-1:628897991744:runtime/Sentra_Agent-vtVCPEFWbx',
            runtimeSessionId=session_id_str,
            payload=bknd_payload,
            qualifier="DEFAULT"
        )
        response_body = response['response'].read()
        response_data = json.loads(response_body)
        print("Agent Response:", response_data)
        
        # Update turn with response
        try:
            turn = db.query(ConversationTurn).filter(
                ConversationTurn.turn_id == uuid.UUID(turn_id)
            ).first()
            
            if turn:
                turn.assistant_response = response_data
                turn.status = 'COMPLETED'
                turn.completed_at = datetime.now(timezone.utc)
                db.commit()
                print(f"✅ Updated turn {turn_number} with response")
        except Exception as e:
            db.rollback()
            print(f"⚠️ Failed to update turn: {str(e)}")
        
        # Add session_id to response for frontend
        response_data['session_id'] = session_id_str
        response_data['turn_number'] = turn_number
        
        # Filter response based on user's role (Req 8.1–8.4)
        # The full unfiltered response is already stored in DB above.
        # Filtering is read-time only.
        return filter_response_for_role(response_data, current_user.role)
        
    except Exception as e:
        # Mark turn as failed
        try:
            turn = db.query(ConversationTurn).filter(
                ConversationTurn.turn_id == uuid.UUID(turn_id)
            ).first()
            
            if turn:
                turn.status = 'FAILED'
                turn.error_message = str(e)
                turn.completed_at = datetime.now(timezone.utc)
                db.commit()
        except:
            db.rollback()
        
        print(f"Error calling Bedrock AgentCore: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process request: {str(e)}")


# ============================================
# SESSION ENDPOINTS
# ============================================

@app.post("/api/sessions")
async def create_session(session: SessionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new chat session"""
    try:
        new_session = ChatSession(
            user_id=session.user_id,
            session_title=session.session_title
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return new_session.to_dict()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@app.get("/api/sessions/{user_id}")
async def get_user_sessions(user_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all active sessions for a user"""
    try:
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.status == 'ACTIVE'
        ).order_by(ChatSession.last_activity_at.desc()).all()
        
        return [session.to_dict() for session in sessions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")


@app.get("/api/sessions/{session_id}/turns")
async def get_session_turns(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all turns for a session (converted to message format for frontend compatibility)"""
    try:
        turns = db.query(ConversationTurn).filter(
            ConversationTurn.session_id == uuid.UUID(session_id)
        ).order_by(ConversationTurn.turn_number).all()
        
        # Convert turns to message format for frontend
        messages = []
        for turn in turns:
            messages.extend(turn.to_message_format())
        
        # Filter stored responses by the requesting user's role (Req 8.5)
        return filter_messages_for_role(messages, current_user.role)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch turns: {str(e)}")


@app.get("/api/sessions/{session_id}/turns/raw")
async def get_session_turns_raw(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all turns for a session in raw format"""
    try:
        turns = db.query(ConversationTurn).filter(
            ConversationTurn.session_id == uuid.UUID(session_id)
        ).order_by(ConversationTurn.turn_number).all()
        
        # Filter each turn's assistant_response by role (Req 8.5)
        result = []
        for turn in turns:
            turn_dict = turn.to_dict()
            if isinstance(turn_dict.get("assistant_response"), dict):
                turn_dict["assistant_response"] = filter_response_for_role(
                    turn_dict["assistant_response"], current_user.role
                )
            result.append(turn_dict)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch turns: {str(e)}")


@app.put("/api/sessions/{session_id}")
async def update_session(session_id: str, update: SessionUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update session title or status"""
    try:
        session = db.query(ChatSession).filter(
            ChatSession.session_id == uuid.UUID(session_id)
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if update.session_title is not None:
            session.session_title = update.session_title
        
        if update.status is not None:
            if update.status not in ['ACTIVE', 'ARCHIVED', 'DELETED']:
                raise HTTPException(status_code=400, detail="Invalid status")
            session.status = update.status
        
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
        
        return session.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Soft delete a session (mark as DELETED)"""
    try:
        session = db.query(ChatSession).filter(
            ChatSession.session_id == uuid.UUID(session_id)
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.status = 'DELETED'
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        return {"message": "Session deleted successfully", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


# ============================================
# BACKWARD COMPATIBILITY ENDPOINT
# ============================================

@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Backward compatibility endpoint - returns turns as messages
    Alias for /api/sessions/{session_id}/turns
    """
    try:
        turns = db.query(ConversationTurn).filter(
            ConversationTurn.session_id == uuid.UUID(session_id)
        ).order_by(ConversationTurn.turn_number).all()
        
        messages = []
        for turn in turns:
            messages.extend(turn.to_message_format())
        
        # Filter stored responses by the requesting user's role (Req 8.5)
        return filter_messages_for_role(messages, current_user.role)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch turns: {str(e)}")


# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Sentra Insurance API V3",
        "features": ["UUID sessions", "Conversation turns", "Auto-sequencing", "Google OAuth"]
    }


# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@app.get("/auth/google")
async def auth_google():
    """Initiate Google OAuth flow"""
    authorization_url, state = oauth_handler.get_authorization_url()
    oauth_states[state] = True
    return RedirectResponse(url=authorization_url)


@app.get("/auth/google/callback")
async def auth_google_callback(code: str, state: str = None, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    # For development, skip strict state validation
    # In production, use Redis or database to store states
    if state and state in oauth_states:
        del oauth_states[state]
    
    try:
        user_info = oauth_handler.exchange_code(code, state or "")
        email = user_info["email"]
        
        # Check if user exists (only allow pre-registered users)
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # User not found - Access Denied
            print(f"Access denied for unauthorized email: {email}")
            # Redirect to frontend with error
            error_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/login?error=access_denied"
            return RedirectResponse(url=error_url)
        
        # User exists - update last login
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        
        # Resolve user's role from Keycloak (Req 5.1–5.5)
        role = resolve_role_for_email(user.email, keycloak_client)
        
        # Generate JWT token with role claim (Req 6.1)
        token = jwt_handler.create_token(user.id, user.email, role.value)
        
        # Redirect to frontend with cookie
        response = RedirectResponse(url=os.getenv("FRONTEND_URL", "http://localhost:5173"))
        response.set_cookie(
            key="sentra_jwt_token",
            value=token,
            httponly=True,
            secure=os.getenv("COOKIE_SECURE", "False") == "True",
            samesite=os.getenv("COOKIE_SAMESITE", "lax"),
            max_age=604800,
            domain=os.getenv("COOKIE_DOMAIN", "localhost"),
            path="/"
        )
        return response
    except Exception as e:
        print(f"OAuth callback error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@app.post("/auth/logout")
async def auth_logout(current_user: User = Depends(get_current_user)):
    """Logout user"""
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(key="sentra_jwt_token", path="/")
    return response


@app.get("/auth/me")
async def auth_me(current_user: User = Depends(get_current_user)):
    """Get current user info including role"""
    return {**current_user.to_dict(), "role": current_user.role.value}


@app.get("/auth/verify")
async def auth_verify(current_user: User = Depends(get_current_user)):
    """Verify JWT token"""
    return {"valid": True, "user_id": current_user.id}


# ============================================
# ADMIN ENDPOINTS
# ============================================

@app.get("/admin/users")
async def list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """List all authorized users. Admin-only (Req 9.1, 9.2)."""
    return [u.to_dict() for u in db.query(User).all()]


@app.post("/admin/keycloak/sync")
async def trigger_sync(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Trigger Keycloak user synchronization. Admin-only (Req 9.1, 9.2)."""
    return sync_users(keycloak_client, db)


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
