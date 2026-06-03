from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
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

# Import database components
from database import get_db, test_connection
from models_v3 import ChatSession, ConversationTurn

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
    allow_origins=["*"],
    allow_credentials=True,
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
async def send_to_bknd(request: QueryRequest, db: Session = Depends(get_db)):
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
        
        return response_data
        
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
async def create_session(session: SessionCreate, db: Session = Depends(get_db)):
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
async def get_user_sessions(user_id: str, db: Session = Depends(get_db)):
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
async def get_session_turns(session_id: str, db: Session = Depends(get_db)):
    """Get all turns for a session (converted to message format for frontend compatibility)"""
    try:
        turns = db.query(ConversationTurn).filter(
            ConversationTurn.session_id == uuid.UUID(session_id)
        ).order_by(ConversationTurn.turn_number).all()
        
        # Convert turns to message format for frontend
        messages = []
        for turn in turns:
            messages.extend(turn.to_message_format())
        
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch turns: {str(e)}")


@app.get("/api/sessions/{session_id}/turns/raw")
async def get_session_turns_raw(session_id: str, db: Session = Depends(get_db)):
    """Get all turns for a session in raw format"""
    try:
        turns = db.query(ConversationTurn).filter(
            ConversationTurn.session_id == uuid.UUID(session_id)
        ).order_by(ConversationTurn.turn_number).all()
        
        return [turn.to_dict() for turn in turns]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch turns: {str(e)}")


@app.put("/api/sessions/{session_id}")
async def update_session(session_id: str, update: SessionUpdate, db: Session = Depends(get_db)):
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
async def delete_session(session_id: str, db: Session = Depends(get_db)):
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
async def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """
    Backward compatibility endpoint - returns turns as messages
    Alias for /api/sessions/{session_id}/turns
    """
    return await get_session_turns(session_id, db)


# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Sentra Insurance API V3",
        "features": ["UUID sessions", "Conversation turns", "Auto-sequencing"]
    }


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
