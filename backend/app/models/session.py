"""Research session model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ResearchSession(Base):
    """Research session tracking."""
    
    __tablename__ = "research_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    industry = Column(String(500), nullable=True)
    status = Column(String(50), default="active")  # active, completed, error
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    competitors = relationship("Competitor", back_populates="session", cascade="all, delete-orphan")
    reports = relationship("ResearchReport", back_populates="session", cascade="all, delete-orphan")

