"""Research session model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ResearchSession(Base):
    """Research session tracking."""
    
    __tablename__ = "research_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String(100), nullable=True, index=True)  # Browser/device identifier for session isolation
    title = Column(String(200), nullable=True, default="New Research")
    industry = Column(String(500), nullable=True)
    status = Column(String(50), default="active")  # active, completed, error
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Research state - stores planning and clarification data
    research_plan = Column(JSON, nullable=True)  # { industry, competitors, certifications, selected_*, is_confirmed }
    clarification_state = Column(JSON, nullable=True)  # { stage, iteration, user_feedback, is_complete }
    research_data = Column(JSON, nullable=True)  # { courses, module_inventory, etc. }
    
    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at")
    competitors = relationship("Competitor", back_populates="session", cascade="all, delete-orphan")
    reports = relationship("ResearchReport", back_populates="session", cascade="all, delete-orphan")

