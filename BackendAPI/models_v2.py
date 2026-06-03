"""
SQLAlchemy models for chat sessions and messages (V2 - Improved Sequencing)
"""
from sqlalchemy import Column, String, BigInteger, Integer, ForeignKey, CheckConstraint, Index, UniqueConstraint
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
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.sequence_number")
    
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
    
    # Primary key: Auto-incrementing for guaranteed uniqueness
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Message identification
    message_id = Column(String(50), nullable=False, unique=True, index=True)
    session_id = Column(String(33), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False)
    
    # Sequence number within session (auto-incremented by trigger)
    sequence_number = Column(Integer, nullable=False)
    
    # Message data
    message_type = Column(String(10), nullable=False)
    content = Column(JSONB, nullable=False)  # Can store string or object
    
    # Timing
    timestamp = Column(BigInteger, nullable=False)  # Frontend timestamp
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationship to session
    session = relationship("ChatSession", back_populates="messages")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("message_type IN ('user', 'bot')", name="check_message_type"),
        UniqueConstraint('session_id', 'sequence_number', name='unique_session_sequence'),
        Index('idx_session_messages', 'session_id', 'sequence_number'),
        Index('idx_session_timestamp', 'session_id', 'timestamp'),
        Index('idx_message_content', 'content', postgresql_using='gin'),
    )
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.message_id,
            "type": self.message_type,
            "content": self.content,
            "timestamp": self.timestamp,
            "sequence": self.sequence_number  # Include sequence for debugging
        }
