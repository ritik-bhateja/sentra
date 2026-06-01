from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import boto3
import json
import botocore
import uvicorn
from datetime import datetime

# Import database components
from database import get_db, test_connection
from models import ChatSession, ChatMessage

app = FastAPI(title="Sentra Insurance API", version="1.0.0")

# Test database connection on startup
@app.on_event("startup")
async def startup_event():
    if test_connection():
        print("✅ Database connected successfully")
    else:
        print("⚠️ Warning: Database connection failed")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Pydantic models for request validation
class QueryRequest(BaseModel):
    user_query: str
    user_id: str
    session_id: str

class SessionCreate(BaseModel):
    session_id: str
    user_id: str
    title: Optional[str] = "New Chat"

class SessionUpdate(BaseModel):
    title: str

class MessageCreate(BaseModel):
    message_id: str
    session_id: str
    message_type: str
    content: dict
    timestamp: int

# --------------------------------------------
#  QUERY ENDPOINT — BEDROCK AGENTCORE
# --------------------------------------------
@app.post("/query")
async def send_to_bknd(request: QueryRequest):
    config = botocore.config.Config(
        read_timeout=180,
        connect_timeout=10,
        retries={'max_attempts': 0}
    )

    print(f"Received request: {request.dict()}")
    
    # Validate user_id presence
    if not request.user_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "missing_actor_id",
                "message": "user_id is required"
            }
        )
    
    # Validate session_id presence
    if not request.session_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "missing_session_id",
                "message": "session_id is required"
            }
        )
    
    client = boto3.client('bedrock-agentcore', region_name='ap-south-1', config=config)
    
    bknd_payload = json.dumps({
        "user_query": request.user_query,
        "user_id": request.user_id,
        "session_id": request.session_id
    })

    try:
        # Use session_id as runtimeSessionId for proper session isolation
        # Frontend generates 33-character session IDs to meet AWS Bedrock requirement
        response = client.invoke_agent_runtime(
            agentRuntimeArn='arn:aws:bedrock-agentcore:ap-south-1:628897991744:runtime/Sentra_Agent-vtVCPEFWbx',
            runtimeSessionId=request.session_id,
            payload=bknd_payload,
            qualifier="DEFAULT"
        )
        response_body = response['response'].read()
        response_data = json.loads(response_body)
        print("Agent Response:", response_data)
        return response_data
    except Exception as e:
        print(f"Error calling Bedrock AgentCore: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "bedrock_error",
                "message": f"Failed to process request: {str(e)}"
            }
        )


# --------------------------------------------
#  HEALTH CHECK ENDPOINT
# --------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Sentra Insurance API"}


# ============================================
#  CHAT HISTORY API ENDPOINTS
# ============================================

# --------------------------------------------
#  CREATE NEW SESSION
# --------------------------------------------
@app.post("/api/sessions")
async def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    """Create a new chat session"""
    try:
        # Check if session already exists
        existing = db.query(ChatSession).filter(ChatSession.session_id == session.session_id).first()
        if existing:
            return existing.to_dict()
        
        # Create new session
        new_session = ChatSession(
            session_id=session.session_id,
            user_id=session.user_id,
            title=session.title
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return new_session.to_dict()
    except Exception as e:
        db.rollback()
        print(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


# --------------------------------------------
#  GET ALL SESSIONS FOR USER
# --------------------------------------------
@app.get("/api/sessions/{user_id}")
async def get_user_sessions(user_id: str, db: Session = Depends(get_db)):
    """Get all sessions for a specific user"""
    try:
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.updated_at.desc()).all()
        
        return [session.to_dict() for session in sessions]
    except Exception as e:
        print(f"Error fetching sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")


# --------------------------------------------
#  GET MESSAGES FOR SESSION
# --------------------------------------------
@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """Get all messages for a specific session"""
    try:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp).all()
        
        return [message.to_dict() for message in messages]
    except Exception as e:
        print(f"Error fetching messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")


# --------------------------------------------
#  SAVE MESSAGE TO SESSION
# --------------------------------------------
@app.post("/api/messages")
async def save_message(message: MessageCreate, db: Session = Depends(get_db)):
    """Save a new message to a session"""
    try:
        # Verify session exists
        session = db.query(ChatSession).filter(ChatSession.session_id == message.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if message already exists
        existing = db.query(ChatMessage).filter(ChatMessage.message_id == message.message_id).first()
        if existing:
            return existing.to_dict()
        
        # Create new message
        new_message = ChatMessage(
            message_id=message.message_id,
            session_id=message.session_id,
            message_type=message.message_type,
            content=message.content,
            timestamp=message.timestamp
        )
        db.add(new_message)
        
        # Update session's updated_at timestamp
        session.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(new_message)
        
        return new_message.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error saving message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save message: {str(e)}")


# --------------------------------------------
#  UPDATE SESSION (RENAME)
# --------------------------------------------
@app.put("/api/sessions/{session_id}")
async def update_session(session_id: str, update: SessionUpdate, db: Session = Depends(get_db)):
    """Update session title"""
    try:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.title = update.title
        session.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(session)
        
        return session.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error updating session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")


# --------------------------------------------
#  DELETE SESSION
# --------------------------------------------
@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a session and all its messages"""
    try:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        db.delete(session)
        db.commit()
        
        return {"message": "Session deleted successfully", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

# --------------------------------------------
#  RUN SERVER
# --------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
