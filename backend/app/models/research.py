"""Research data models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Competitor(Base):
    """Competitor course information."""
    
    __tablename__ = "competitors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("research_sessions.id"), nullable=False)
    
    name = Column(String(500), nullable=False)
    url = Column(Text, nullable=True)
    price = Column(String(100), nullable=True)
    price_tier = Column(String(50), nullable=True)  # low, mid, high, premium
    popularity_rank = Column(Integer, nullable=True)
    
    # Extracted data
    curriculum = Column(JSON, nullable=True)  # List of modules/lessons
    certifications = Column(JSON, nullable=True)  # List of certs offered
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ResearchSession", back_populates="competitors")


class ResearchReport(Base):
    """Final research report."""
    
    __tablename__ = "research_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("research_sessions.id"), nullable=False)
    
    # Research data
    master_topics = Column(JSON, nullable=True)  # Exhaustive topic list with rankings
    sentiment_data = Column(JSON, nullable=True)  # Reddit/Quora/Podcast insights
    trending_topics = Column(JSON, nullable=True)  # Hot topics from last 12-18 months
    
    # Final report
    full_report = Column(Text, nullable=True)  # Markdown formatted report
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ResearchSession", back_populates="reports")

