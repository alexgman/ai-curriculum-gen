"""CRUD operations for chat messages."""
import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


async def create_message(
    db: AsyncSession,
    session_id: str,
    role: str,
    content: str,
    message_id: Optional[str] = None,
    thinking_steps: Optional[list] = None,
    tool_name: Optional[str] = None,
    tool_result: Optional[dict] = None,
    metadata: Optional[dict] = None,
) -> Message:
    """Create a new message in a session."""
    message = Message(
        id=uuid.UUID(message_id) if message_id else uuid.uuid4(),
        session_id=uuid.UUID(session_id),
        role=role,
        content=content,
        thinking_steps=thinking_steps,
        tool_name=tool_name,
        tool_result=tool_result,
        metadata=metadata,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_messages(
    db: AsyncSession,
    session_id: str,
    limit: Optional[int] = None,
) -> list[Message]:
    """Get all messages for a session ordered by creation time."""
    query = (
        select(Message)
        .where(Message.session_id == uuid.UUID(session_id))
        .order_by(Message.created_at.asc())
    )
    
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_message(
    db: AsyncSession,
    message_id: str,
) -> Optional[Message]:
    """Get a specific message by ID."""
    query = select(Message).where(Message.id == uuid.UUID(message_id))
    result = await db.execute(query)
    return result.scalar_one_or_none()

