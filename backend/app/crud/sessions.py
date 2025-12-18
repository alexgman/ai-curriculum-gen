"""CRUD operations for research sessions."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.session import ResearchSession


async def create_session(
    db: AsyncSession,
    session_id: Optional[str] = None,
    title: str = "New Research",
    industry: Optional[str] = None,
    client_id: Optional[str] = None,
) -> ResearchSession:
    """Create a new research session."""
    session = ResearchSession(
        id=uuid.UUID(session_id) if session_id else uuid.uuid4(),
        client_id=client_id,
        title=title,
        industry=industry,
        status="active",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(
    db: AsyncSession,
    session_id: str,
    load_messages: bool = True,
) -> Optional[ResearchSession]:
    """Get a session by ID with optional message loading."""
    query = select(ResearchSession).where(
        ResearchSession.id == uuid.UUID(session_id)
    )
    
    if load_messages:
        query = query.options(selectinload(ResearchSession.messages))
    
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_sessions(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    client_id: Optional[str] = None,
) -> list[ResearchSession]:
    """Get sessions ordered by most recent, optionally filtered by client_id."""
    query = select(ResearchSession)
    
    # Filter by client_id if provided (for browser/device isolation)
    if client_id:
        query = query.where(ResearchSession.client_id == client_id)
    
    query = query.order_by(ResearchSession.updated_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_session(
    db: AsyncSession,
    session_id: str,
    title: Optional[str] = None,
    industry: Optional[str] = None,
    status: Optional[str] = None,
) -> Optional[ResearchSession]:
    """Update session metadata."""
    values = {"updated_at": datetime.utcnow()}
    if title is not None:
        values["title"] = title
    if industry is not None:
        values["industry"] = industry
    if status is not None:
        values["status"] = status
    
    query = (
        update(ResearchSession)
        .where(ResearchSession.id == uuid.UUID(session_id))
        .values(**values)
        .returning(ResearchSession)
    )
    result = await db.execute(query)
    await db.commit()
    return result.scalar_one_or_none()


async def update_session_state(
    db: AsyncSession,
    session_id: str,
    research_plan: Optional[dict] = None,
    clarification_state: Optional[dict] = None,
    research_data: Optional[dict] = None,
    industry: Optional[str] = None,
) -> Optional[ResearchSession]:
    """Update session's research state (research_plan, clarification, research_data)."""
    values = {"updated_at": datetime.utcnow()}
    
    if research_plan is not None:
        values["research_plan"] = research_plan
    if clarification_state is not None:
        values["clarification_state"] = clarification_state
    if research_data is not None:
        values["research_data"] = research_data
    if industry is not None:
        values["industry"] = industry
    
    query = (
        update(ResearchSession)
        .where(ResearchSession.id == uuid.UUID(session_id))
        .values(**values)
        .returning(ResearchSession)
    )
    result = await db.execute(query)
    await db.commit()
    return result.scalar_one_or_none()


async def delete_session(
    db: AsyncSession,
    session_id: str,
) -> bool:
    """Delete a session and all related data (uses ORM for cascade)."""
    # Get the session first to trigger cascade delete through ORM
    session = await get_session(db, session_id, load_messages=False)
    if session is None:
        return False
    
    await db.delete(session)
    await db.commit()
    return True


async def get_or_create_session(
    db: AsyncSession,
    session_id: str,
    title: str = "New Research",
    client_id: Optional[str] = None,
) -> ResearchSession:
    """Get existing session or create new one."""
    session = await get_session(db, session_id, load_messages=True)
    if session is None:
        session = await create_session(db, session_id=session_id, title=title, client_id=client_id)
    return session

