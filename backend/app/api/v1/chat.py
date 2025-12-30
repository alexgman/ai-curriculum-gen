"""Chat API - AI Curriculum Builder with 3-Phase Deep Research."""
import json
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.crud.sessions import get_or_create_session, update_session_state, update_session, get_session
from app.crud.messages import create_message, get_messages
from app.services.research_orchestrator import CurriculumResearchOrchestrator


router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None
    client_id: Optional[str] = None


# Store orchestrators per session
_session_orchestrators: dict[str, CurriculumResearchOrchestrator] = {}


def get_orchestrator(session_id: str, saved_state: dict = None) -> CurriculumResearchOrchestrator:
    """Get or create orchestrator for session."""
    if session_id not in _session_orchestrators:
        orchestrator = CurriculumResearchOrchestrator()
        if saved_state:
            orchestrator.restore_state(saved_state)
        _session_orchestrators[session_id] = orchestrator
    return _session_orchestrators[session_id]


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    AI Curriculum Builder chat endpoint.
    
    Flow:
    1. User provides topic → Claude asks natural clarifying questions
    2. User answers → Phase 1: Competitive Research (courses, pricing, lessons)
    3. User feedback → Phase 2: Industry Expertise (podcasts, blogs, trends)
    4. User feedback → Phase 3: Consumer Sentiment (Reddit, forums)
    5. User feedback → Final Synthesis (comprehensive module/lesson list)
    """
    from app.database import async_session
    
    session_id = request.session_id or str(uuid.uuid4())
    client_id = request.client_id
    
    async def event_generator():
        """Generate SSE events from curriculum research."""
        async with async_session() as db:
            try:
                # Get or create session
                db_session = await get_or_create_session(db, session_id, client_id=client_id)
                
                print(f"💬 Chat - session: {session_id}")
                print(f"📝 Message: {request.message[:100]}...")
                
                # Get orchestrator
                saved_state = db_session.clarification_state if db_session.clarification_state else None
                orchestrator = get_orchestrator(session_id, saved_state)
                
                print(f"🔄 Current phase: {orchestrator.state['phase']}")
                
                # Save user message
                await create_message(
                    db,
                    session_id=session_id,
                    role="user",
                    content=request.message,
                    message_id=str(uuid.uuid4()),
                )
                
                # Send session info
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
                
                # Process message
                assistant_content = ""
                thinking_content = ""
                
                async for event in orchestrator.process_message(request.message):
                    event_type = event.get("type", "")
                    
                    if event_type == "status":
                        yield f"data: {json.dumps({'type': 'status', 'content': event.get('content', '')})}\n\n"
                    
                    elif event_type == "thinking":
                        content = event.get("content", "")
                        thinking_content += content
                        yield f"data: {json.dumps({'type': 'thinking', 'content': content})}\n\n"
                    
                    elif event_type == "text_stream":
                        chunk = event.get("content", "")
                        assistant_content += chunk
                        yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
                    
                    elif event_type == "search_status":
                        yield f"data: {json.dumps({'type': 'search', 'number': event.get('search_number', 0)})}\n\n"
                    
                    elif event_type == "search_complete":
                        yield f"data: {json.dumps({'type': 'search_complete', 'total': event.get('total_searches', 0)})}\n\n"
                    
                    elif event_type == "phase_start":
                        yield f"data: {json.dumps({'type': 'phase_start', 'phase': event.get('phase'), 'number': event.get('phase_number'), 'total': event.get('total_phases'), 'title': event.get('title'), 'description': event.get('description')})}\n\n"
                    
                    elif event_type == "phase_complete":
                        yield f"data: {json.dumps({'type': 'phase_complete', 'phase': event.get('phase'), 'search_count': event.get('search_count', 0)})}\n\n"
                    
                    elif event_type == "clarification_needed":
                        content = event.get("content", "")
                        assistant_content = content
                        yield f"data: {json.dumps({'type': 'clarification', 'content': content, 'phase': event.get('phase')})}\n\n"
                    
                    elif event_type == "feedback_request":
                        content = event.get("content", "")
                        assistant_content += "\n\n" + content
                        yield f"data: {json.dumps({'type': 'feedback_request', 'content': content, 'phase': event.get('phase')})}\n\n"
                    
                    elif event_type == "research_complete":
                        report = event.get("final_report", "")
                        yield f"data: {json.dumps({'type': 'research_complete', 'report': report, 'topic': event.get('topic')})}\n\n"
                    
                    elif event_type == "completion_message":
                        content = event.get("content", "")
                        assistant_content += "\n\n" + content
                        yield f"data: {json.dumps({'type': 'complete', 'content': content})}\n\n"
                    
                    elif event_type == "refinement_complete":
                        yield f"data: {json.dumps({'type': 'refinement', 'phase': event.get('phase')})}\n\n"
                    
                    elif event_type == "navigation":
                        yield f"data: {json.dumps({'type': 'navigation', 'to': event.get('to_phase'), 'content': event.get('content')})}\n\n"
                    
                    elif event_type == "followup_complete":
                        content = event.get("content", "")
                        assistant_content = content
                        yield f"data: {json.dumps({'type': 'followup', 'content': content})}\n\n"
                    
                    elif event_type == "error":
                        yield f"data: {json.dumps({'type': 'error', 'message': event.get('content', '')})}\n\n"
                
                # Save orchestrator state
                await update_session_state(
                    db,
                    session_id,
                    clarification_state=orchestrator.get_state(),
                )
                
                # Save assistant message
                if assistant_content:
                    await create_message(
                        db,
                        session_id=session_id,
                        role="assistant",
                        content=assistant_content,
                        message_id=str(uuid.uuid4()),
                        thinking_steps={"thinking": thinking_content} if thinking_content else None,
                    )
                
                # Update session title if this is initial topic
                if orchestrator.state["topic"] and not db_session.industry:
                    topic = orchestrator.state["topic"]
                    title = f"{topic[:50]}..." if len(topic) > 50 else topic
                    await update_session(db, session_id, title=title, industry=topic)
                
                yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"
                
            except Exception as e:
                import traceback
                print(f"❌ Error: {e}")
                traceback.print_exc()
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============= SESSION MANAGEMENT =============

class CreateSessionRequest(BaseModel):
    client_id: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    message: str

@router.post("/sessions", response_model=SessionResponse)
async def create_session_endpoint(
    request: CreateSessionRequest = None,
    db: AsyncSession = Depends(get_db),
):
    """Create a new research session."""
    from app.crud.sessions import create_session
    client_id = request.client_id if request else None
    session = await create_session(db, title="New Research", client_id=client_id)
    return SessionResponse(session_id=str(session.id), message="Session created")


class SessionInfo(BaseModel):
    id: str
    title: str
    industry: str | None
    status: str
    created_at: str
    updated_at: str
    message_count: int

@router.get("/sessions")
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    client_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List research sessions."""
    from app.crud.sessions import get_sessions
    
    sessions = await get_sessions(db, limit=limit, offset=offset, client_id=client_id)
    
    result = []
    for session in sessions:
        messages = await get_messages(db, str(session.id))
        result.append(SessionInfo(
            id=str(session.id),
            title=session.title or "New Research",
            industry=session.industry,
            status=session.status,
            created_at=session.created_at.isoformat() if session.created_at else "",
            updated_at=session.updated_at.isoformat() if session.updated_at else "",
            message_count=len(messages),
        ))
    
    return {"sessions": result, "total": len(result)}


@router.get("/sessions/{session_id}")
async def get_session_detail(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get full session details."""
    session = await get_session(db, session_id, load_messages=True)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = await get_messages(db, session_id)
    
    return {
        "id": str(session.id),
        "title": session.title or "New Research",
        "industry": session.industry,
        "status": session.status,
        "created_at": session.created_at.isoformat() if session.created_at else "",
        "updated_at": session.updated_at.isoformat() if session.updated_at else "",
        "messages": [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else "",
            }
            for msg in messages
        ],
        "clarification_state": session.clarification_state,
    }


@router.put("/sessions/{session_id}")
async def update_session_endpoint(
    session_id: str,
    title: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Update session metadata."""
    session = await update_session(db, session_id, title=title)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Updated", "id": str(session.id)}


@router.delete("/sessions/{session_id}")
async def delete_session_endpoint(session_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a session."""
    from app.crud.sessions import delete_session
    
    deleted = await delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Clean up orchestrator
    if session_id in _session_orchestrators:
        del _session_orchestrators[session_id]
    
    return {"message": "Deleted", "id": session_id}


class TitleRequest(BaseModel):
    message: str

@router.post("/sessions/generate-title")
async def generate_title(request: TitleRequest):
    """Generate a title for a session."""
    words = request.message.split()[:6]
    return {"title": " ".join(words)}
