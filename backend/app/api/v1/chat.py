"""Chat API endpoints with SSE streaming and database persistence."""
import json
import uuid
import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from app.graph import research_graph
from app.graph.state import create_initial_state, AgentState
from app.database import get_db
from app.crud.sessions import get_or_create_session, update_session_state, update_session, get_session
from app.crud.messages import create_message, get_messages


router = APIRouter()

# Queue for tool progress updates (still in-memory, per-request)
_progress_queues: dict[str, asyncio.Queue] = {}


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None
    client_id: Optional[str] = None  # Browser/device identifier for session isolation


class ChatResponse(BaseModel):
    """Chat response model."""
    session_id: str
    message: str
    research_data: Optional[dict] = None


class SessionResponse(BaseModel):
    """Session creation response."""
    session_id: str
    message: str


class CreateSessionRequest(BaseModel):
    """Request to create a new session."""
    client_id: Optional[str] = None


@router.post("/sessions", response_model=SessionResponse)
async def create_session_endpoint(
    request: CreateSessionRequest = None,
    db: AsyncSession = Depends(get_db),
):
    """Create a new research session."""
    from app.crud.sessions import create_session
    client_id = request.client_id if request else None
    session = await create_session(db, title="New Research", client_id=client_id)
    return SessionResponse(
        session_id=str(session.id),
        message="Session created successfully",
    )


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint with SSE streaming.
    
    Sends messages to the LangGraph agent and streams responses.
    Uses database for persistence.
    """
    from app.database import async_session
    
    # Create or use existing session
    session_id = request.session_id or str(uuid.uuid4())
    client_id = request.client_id  # Browser/device identifier
    
    async def event_generator():
        """Generate SSE events from agent execution with real-time updates."""
        async with async_session() as db:
            try:
                # Get or create session from database (with client_id for isolation)
                db_session = await get_or_create_session(db, session_id, client_id=client_id)
                
                print(f"🔗 Chat request - session_id: {session_id}, client_id: {client_id}")
                print(f"📊 Session from DB: {db_session.title}, status={db_session.status}")
                
                # Load existing messages from database
                db_messages = await get_messages(db, session_id)
                
                # Convert to LangChain messages
                conversation_history: list[BaseMessage] = []
                for msg in db_messages:
                    if msg.role == "user":
                        conversation_history.append(HumanMessage(content=msg.content))
                    elif msg.role == "assistant":
                        conversation_history.append(AIMessage(content=msg.content))
                
                print(f"📂 Loaded {len(conversation_history)} messages from DB")
                
                # Save user message to database
                user_msg_id = str(uuid.uuid4())
                await create_message(
                    db,
                    session_id=session_id,
                    role="user",
                    content=request.message,
                    message_id=user_msg_id,
                )
                
                # Add current user message to history
                conversation_history.append(HumanMessage(content=request.message))
                
                # Create state with conversation history
                state = create_initial_state(session_id)
                state["messages"] = conversation_history
                
                # Load research state from database
                if db_session.research_plan:
                    state["research_plan"] = db_session.research_plan
                    print(f"📋 Loaded research_plan: confirmed={db_session.research_plan.get('is_confirmed')}")
                
                if db_session.clarification_state:
                    state["clarification"] = db_session.clarification_state
                    print(f"📋 Loaded clarification state: stage={db_session.clarification_state.get('stage')}")
                
                if db_session.research_data:
                    state["research_data"] = db_session.research_data
                    courses_count = len(db_session.research_data.get("courses", []))
                    print(f"📋 Loaded research_data: {courses_count} courses")
                
                if db_session.industry:
                    state["industry"] = db_session.industry
                
                # Check if awaiting clarification
                if db_session.clarification_state:
                    stage = db_session.clarification_state.get("stage", "")
                    if stage in ["presenting_plan", "refining"]:
                        state["awaiting_clarification"] = True
                
                # Setup progress queue for this session
                progress_queue: asyncio.Queue = asyncio.Queue()
                _progress_queues[session_id] = progress_queue
                
                # Setup progress callback
                from app.tools.course_discovery import set_progress_callback
                async def progress_callback(msg: str):
                    await progress_queue.put(msg)
                set_progress_callback(progress_callback)
                
                # Send session info immediately
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
                
                # Send initial thinking status
                yield f"data: {json.dumps({'type': 'thinking', 'status': 'Starting research', 'step': 0})}\n\n"
                await asyncio.sleep(0.02)
                
                step_count = 0
                final_response_content = ""
                thinkingMessages: list[str] = []
                assistant_msg_id = str(uuid.uuid4())
                
                # Variables to track state updates
                new_research_plan = None
                new_clarification = None
                new_research_data = None
                new_industry = None
                
                # Create a shared queue for ALL SSE events
                event_queue: asyncio.Queue = asyncio.Queue()
                graph_complete = False
                
                # Run graph in background task
                async def run_graph():
                    """Run the graph and put events into the queue."""
                    nonlocal graph_complete, step_count
                    try:
                        async for event in research_graph.astream(state):
                            for node_name, node_output in event.items():
                                step_count += 1
                                await event_queue.put(("graph", node_name, node_output, step_count))
                    except Exception as e:
                        print(f"❌ Graph error: {e}")
                        import traceback
                        traceback.print_exc()
                        await event_queue.put(("error", str(e), None, 0))
                    finally:
                        graph_complete = True
                        await event_queue.put(("done", None, None, 0))
                
                # Run progress/keepalive in background
                async def run_keepalive():
                    """Send keepalive and progress messages."""
                    last_keepalive = asyncio.get_event_loop().time()
                    while not graph_complete:
                        # Check for progress messages
                        while not progress_queue.empty():
                            try:
                                msg = progress_queue.get_nowait()
                                await event_queue.put(("progress", msg, None, step_count))
                            except asyncio.QueueEmpty:
                                break
                        
                        # Send keepalive every 15 seconds
                        now = asyncio.get_event_loop().time()
                        if now - last_keepalive > 15:
                            await event_queue.put(("keepalive", now, None, 0))
                            last_keepalive = now
                        
                        await asyncio.sleep(0.3)
                
                # Start both tasks
                graph_task = asyncio.create_task(run_graph())
                keepalive_task = asyncio.create_task(run_keepalive())
                
                # Main loop - yield events from queue
                while True:
                    try:
                        # Wait for next event with timeout
                        event_type, data, extra, step = await asyncio.wait_for(
                            event_queue.get(), 
                            timeout=2.0
                        )
                        
                        if event_type == "done":
                            break
                        elif event_type == "error":
                            yield f"data: {json.dumps({'type': 'error', 'message': data})}\n\n"
                            break
                        elif event_type == "keepalive":
                            yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': data})}\n\n"
                            await asyncio.sleep(0.01)
                        elif event_type == "progress":
                            yield f"data: {json.dumps({'type': 'thinking', 'status': data, 'step': step})}\n\n"
                            await asyncio.sleep(0.01)
                        elif event_type == "graph":
                            node_name, node_output = data, extra
                            
                            # Track state updates from nodes
                            if "research_plan" in node_output:
                                new_research_plan = node_output["research_plan"]
                            if "clarification" in node_output:
                                new_clarification = node_output["clarification"]
                            if "research_data" in node_output:
                                new_research_data = node_output["research_data"]
                            if "industry" in node_output:
                                new_industry = node_output["industry"]
                            
                            # Process graph event - send thinking status
                            if node_name == "entry":
                                yield f"data: {json.dumps({'type': 'thinking', 'status': 'Analyzing request', 'step': step})}\n\n"
                            elif node_name == "clarification":
                                awaiting = node_output.get("awaiting_clarification", False)
                                if awaiting:
                                    yield f"data: {json.dumps({'type': 'thinking', 'status': 'Discovering research landscape', 'step': step})}\n\n"
                                else:
                                    yield f"data: {json.dumps({'type': 'thinking', 'status': 'Processing your feedback', 'step': step})}\n\n"
                            elif node_name == "reasoning":
                                yield f"data: {json.dumps({'type': 'thinking', 'status': 'Planning next action', 'step': step})}\n\n"
                            elif node_name == "tool_executor":
                                tool_call = node_output.get("current_tool_call") or state.get("current_tool_call")
                                tool_name = tool_call.get("name", "tool") if tool_call else "tool"
                                yield f"data: {json.dumps({'type': 'thinking', 'status': f'Executing {tool_name}', 'tool': tool_name, 'step': step})}\n\n"
                            elif node_name == "reflection":
                                yield f"data: {json.dumps({'type': 'thinking', 'status': 'Validating results', 'step': step})}\n\n"
                            elif node_name == "response":
                                yield f"data: {json.dumps({'type': 'thinking', 'status': 'Generating report', 'step': step})}\n\n"
                            
                            await asyncio.sleep(0.02)
                            
                            # Build and send node event
                            event_data = {"type": "node", "node": node_name, "step": step}
                            
                            # Only process messages from nodes that generate NEW content
                            # Skip 'entry' node - it's a pass-through that contains historical messages
                            if "messages" in node_output and node_name != "entry":
                                for msg in node_output["messages"]:
                                    if isinstance(msg, AIMessage) and msg.content:
                                        event_data["content"] = msg.content
                                        
                                        # Handle clarification questions - stream by lines for proper markdown rendering
                                        if node_name == "clarification" and node_output.get("awaiting_clarification"):
                                            import random
                                            final_response_content = msg.content
                                            print(f"CAPTURED CLARIFICATION: {len(final_response_content)} chars")
                                            
                                            # Stream by lines to preserve markdown formatting
                                            lines = final_response_content.split('\n')
                                            streamed_content = ""
                                            
                                            for i, line in enumerate(lines):
                                                streamed_content += line + '\n'
                                                
                                                yield f"data: {json.dumps({'type': 'clarification_stream', 'content': streamed_content.rstrip(), 'is_complete': False})}\n\n"
                                                
                                                # Variable delay based on line content for natural feel
                                                # Longer lines = slightly longer delay, empty lines = quick
                                                base_delay = 0.05 if line.strip() else 0.02
                                                variation = random.random() * 0.03
                                                await asyncio.sleep(base_delay + variation)
                                            
                                            # Send final complete message
                                            yield f"data: {json.dumps({'type': 'clarification', 'content': final_response_content, 'awaiting_response': True, 'is_complete': True})}\n\n"
                                            await asyncio.sleep(0.05)
                                        # Track final response from response node
                                        elif node_name == "response":
                                            is_status = msg.content.startswith(("Reasoning:", "Reflection:", "Found", "Searching", "Analyzing"))
                                            if not is_status and len(msg.content) > 500:
                                                final_response_content = msg.content
                                                print(f"CAPTURED FINAL RESPONSE: {len(final_response_content)} chars")
                                                yield f"data: {json.dumps({'type': 'final_response', 'content': final_response_content})}\n\n"
                                                await asyncio.sleep(0.1)
                            
                            if "reasoning_explanation" in node_output:
                                event_data["reasoning"] = node_output["reasoning_explanation"]
                            if "reflection_explanation" in node_output:
                                event_data["reflection"] = node_output["reflection_explanation"]
                            if "current_tool_call" in node_output and node_output["current_tool_call"]:
                                event_data["tool_call"] = {"name": node_output["current_tool_call"].get("name")}
                            if "current_tool_result" in node_output and node_output["current_tool_result"]:
                                event_data["tool_result"] = {"success": node_output["current_tool_result"].get("success")}
                            if "research_data" in node_output:
                                event_data["research_summary"] = _summarize_research(node_output["research_data"])
                            
                            event_json = json.dumps(event_data)
                            print(f"📤 Sending {node_name}: {len(event_json)} bytes")
                            yield f"data: {event_json}\n\n"
                            await asyncio.sleep(0.02)
                    
                    except asyncio.TimeoutError:
                        if not graph_complete:
                            yield f"data: {json.dumps({'type': 'ping'})}\n\n"
                            await asyncio.sleep(0.01)
                        else:
                            break
                
                # Cleanup
                keepalive_task.cancel()
                try:
                    await keepalive_task
                except asyncio.CancelledError:
                    pass
                
                set_progress_callback(None)
                if session_id in _progress_queues:
                    del _progress_queues[session_id]
                
                # Save assistant response and state to database
                if final_response_content:
                    await create_message(
                        db,
                        session_id=session_id,
                        role="assistant",
                        content=final_response_content,
                        message_id=assistant_msg_id,
                        thinking_steps=thinkingMessages[-20:] if thinkingMessages else None,
                    )
                    print(f"💾 Saved assistant message to DB: {len(final_response_content)} chars")
                
                # Save state updates to database
                await update_session_state(
                    db,
                    session_id=session_id,
                    research_plan=new_research_plan if new_research_plan else db_session.research_plan,
                    clarification_state=new_clarification if new_clarification else db_session.clarification_state,
                    research_data=new_research_data if new_research_data else db_session.research_data,
                    industry=new_industry if new_industry else db_session.industry,
                )
                print(f"💾 Saved session state to DB")
                
                # Send completion event
                yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id, 'total_steps': step_count})}\n\n"
                
            except Exception as e:
                import traceback
                yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'traceback': traceback.format_exc()})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/sync", response_model=ChatResponse)
async def chat_sync(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Synchronous chat endpoint (non-streaming).
    
    Useful for testing or clients that don't support SSE.
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Create initial state
        state = create_initial_state(session_id)
        state["messages"] = [HumanMessage(content=request.message)]
        
        # Run the graph to completion
        final_state = await research_graph.ainvoke(state)
        
        # Extract the final response
        response_content = ""
        for msg in reversed(final_state.get("messages", [])):
            if isinstance(msg, AIMessage):
                response_content = msg.content
                break
        
        return ChatResponse(
            session_id=session_id,
            message=response_content,
            research_data=final_state.get("research_data"),
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TitleRequest(BaseModel):
    """Title generation request."""
    message: str


@router.post("/sessions/generate-title")
async def generate_title(request: TitleRequest):
    """Generate a concise title for a research session based on the first message."""
    from app.services.anthropic import claude_client
    
    try:
        prompt = f"""Generate a concise, professional title (max 6 words) for this research query:

"{request.message}"

Return ONLY the title, nothing else. Make it descriptive and specific to the industry/topic.

Examples:
- "Research data center technician courses" → "Data Center Technician Courses"
- "Find real estate training" → "Real Estate Training Programs"
- "AI curriculum for beginners" → "AI Curriculum for Beginners"
"""
        
        title = await claude_client.complete(
            prompt=prompt,
            system="You generate concise titles for research sessions. Return only the title.",
            max_tokens=50,
            temperature=0,
        )
        
        title = title.strip().strip('"').strip("'")
        if len(title) > 60:
            title = title[:57] + "..."
        
        return {"title": title}
    
    except Exception as e:
        words = request.message.split()[:6]
        title = " ".join(words)
        if len(title) > 60:
            title = title[:57] + "..."
        return {"title": title}


def _summarize_research(research_data: dict) -> dict:
    """Create a summary of research data for streaming."""
    return {
        "courses_count": len(research_data.get("courses", [])),
        "competitors_count": len(research_data.get("competitors", [])),
        "curricula_count": len(research_data.get("curricula", [])),
        "reddit_posts_count": len(research_data.get("reddit_posts", [])),
        "podcasts_count": len(research_data.get("podcasts", [])),
        "blogs_count": len(research_data.get("blogs", [])),
    }


# ============= SESSION MANAGEMENT ENDPOINTS =============

class SessionInfo(BaseModel):
    """Session info for listing."""
    id: str
    title: str
    industry: str | None
    status: str
    created_at: str
    updated_at: str
    message_count: int


class SessionDetail(BaseModel):
    """Full session details with messages."""
    id: str
    title: str
    industry: str | None
    status: str
    created_at: str
    updated_at: str
    messages: list[dict]
    research_plan: dict | None
    clarification_state: dict | None
    has_research_data: bool


@router.get("/sessions")
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    client_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List research sessions ordered by most recent, filtered by client_id if provided."""
    from app.crud.sessions import get_sessions
    
    # Filter by client_id to isolate sessions per browser/device
    sessions = await get_sessions(db, limit=limit, offset=offset, client_id=client_id)
    
    result = []
    for session in sessions:
        # Get message count
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
async def get_session_detail(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get full session details including messages and state."""
    from app.crud.sessions import get_session as get_session_crud
    
    session = await get_session_crud(db, session_id, load_messages=True)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get messages from database
    messages = await get_messages(db, session_id)
    
    message_list = [
        {
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "thinking_steps": msg.thinking_steps,
            "created_at": msg.created_at.isoformat() if msg.created_at else "",
        }
        for msg in messages
    ]
    
    return SessionDetail(
        id=str(session.id),
        title=session.title or "New Research",
        industry=session.industry,
        status=session.status,
        created_at=session.created_at.isoformat() if session.created_at else "",
        updated_at=session.updated_at.isoformat() if session.updated_at else "",
        messages=message_list,
        research_plan=session.research_plan,
        clarification_state=session.clarification_state,
        has_research_data=bool(session.research_data),
    )


@router.put("/sessions/{session_id}")
async def update_session_endpoint(
    session_id: str,
    title: str | None = None,
    industry: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Update session metadata (title, industry, status)."""
    session = await update_session(db, session_id, title=title, industry=industry, status=status)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session updated", "id": str(session.id)}


@router.delete("/sessions/{session_id}")
async def delete_session_endpoint(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a session and all its messages."""
    from app.crud.sessions import delete_session
    
    deleted = await delete_session(db, session_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted", "id": session_id}
