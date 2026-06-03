"""
SQLAlchemy models for chat sessions and conversation turns (V3 - Production Ready)
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import uuid

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False, index=True)
    session_title = Column(String(500))
    status = Column(String(20), nullable=False, default='ACTIVE')
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_activity_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # Relationship to turns
    turns = relationship(
        "ConversationTurn", 
        back_populates="session", 
        cascade="all, delete-orphan",
        order_by="ConversationTurn.turn_number"
    )
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'ARCHIVED', 'DELETED')", name="chk_session_status"),
        Index('idx_user_sessions', 'user_id', 'last_activity_at'),
        Index('idx_session_status', 'status', 'updated_at'),
    )
    
    def to_dict(self, include_turns=False):
        """Convert model to dictionary"""
        result = {
            "id": str(self.session_id),
            "user_id": self.user_id,
            "title": self.session_title or "New Chat",
            "status": self.status,
            "createdAt": int(self.created_at.timestamp() * 1000),
            "updatedAt": int(self.updated_at.timestamp() * 1000),
            "lastActivityAt": int(self.last_activity_at.timestamp() * 1000),
        }
        
        if include_turns:
            result["turns"] = [turn.to_dict() for turn in self.turns]
            result["turnCount"] = len(self.turns)
        
        return result


class ConversationTurn(Base):
    __tablename__ = "conversation_turns"
    
    turn_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    user_query = Column(Text, nullable=False)
    assistant_response = Column(JSONB)  # Stores full response: {type, data, explanation, etc.}
    model_name = Column(String(100), default='moonshotai.kimi-k2.5')
    status = Column(String(20), nullable=False, default='COMPLETED')
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True))
    error_message = Column(Text)
    
    # Relationship to session
    session = relationship("ChatSession", back_populates="turns")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')", name="chk_turn_status"),
        UniqueConstraint('session_id', 'turn_number', name='uq_session_turn'),
        Index('idx_session_turns', 'session_id', 'turn_number'),
        Index('idx_turn_status', 'status', 'created_at'),
        Index('idx_assistant_response', 'assistant_response', postgresql_using='gin'),
    )
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "turn_id": str(self.turn_id),
            "turn_number": self.turn_number,
            "user_query": self.user_query,
            "assistant_response": self.assistant_response,
            "model_name": self.model_name,
            "status": self.status,
            "created_at": int(self.created_at.timestamp() * 1000),
            "completed_at": int(self.completed_at.timestamp() * 1000) if self.completed_at else None,
            "error_message": self.error_message
        }
    
    def to_message_format(self):
        """
        Convert to frontend message format for backward compatibility
        Returns two messages: user and bot
        """
        messages = []
        
        # User message
        messages.append({
            "id": f"{self.turn_id}_user",
            "type": "user",
            "content": self.user_query,
            "timestamp": int(self.created_at.timestamp() * 1000)
        })
        
        # Bot message
        if self.assistant_response:
            messages.append({
                "id": f"{self.turn_id}_bot",
                "type": "bot",
                "content": self.assistant_response,
                "timestamp": int((self.completed_at or self.created_at).timestamp() * 1000)
            })
        
        return messages
