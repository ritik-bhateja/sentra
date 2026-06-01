"""
SQLAlchemy models for chat sessions and messages
"""
from sqlalchemy import Column, String, BigInteger, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    session_id = Column(String(33), primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    title = Column(String(255), default="New Chat")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to messages
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    # Index for user sessions ordered by updated_at
    __table_args__ = (
        Index('idx_user_sessions', 'user_id', 'updated_at'),
    )
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.session_id,
            "title": self.title,
            "messages": [],  # Messages loaded separately for performance
            "createdAt": int(self.created_at.timestamp() * 1000),
            "updatedAt": int(self.updated_at.timestamp() * 1000)
        }

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    message_id = Column(String(50), primary_key=True, index=True)
    session_id = Column(String(33), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False)
    message_type = Column(String(10), nullable=False)
    content = Column(JSONB, nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationship to session
    session = relationship("ChatSession", back_populates="messages")
    
    # Check constraint for message_type
    __table_args__ = (
        CheckConstraint("message_type IN ('user', 'bot')", name="check_message_type"),
        Index('idx_session_messages', 'session_id', 'timestamp'),
        Index('idx_message_content', 'content', postgresql_using='gin'),
    )
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.message_id,
            "type": self.message_type,
            "content": self.content,
            "timestamp": self.timestamp
        }
