"""Chat message model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Message(Base):
    """Chat message in a research session."""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("research_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, tool, system
    content = Column(Text, nullable=False)
    tool_name = Column(String(100), nullable=True)  # If role is "tool"
    tool_result = Column(JSON, nullable=True)  # Tool execution result
    thinking_steps = Column(JSON, nullable=True)  # List of thinking steps for assistant messages
    is_streaming = Column(Boolean, default=False)  # Whether message is still streaming
    extra_data = Column(JSON, nullable=True)  # Additional metadata (renamed from metadata)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ResearchSession", back_populates="messages")

