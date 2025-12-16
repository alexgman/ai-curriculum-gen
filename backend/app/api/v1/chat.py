"""Chat API endpoints with SSE streaming."""
import json
import uuid
import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from app.graph import research_graph
from app.graph.state import create_initial_state, AgentState


router = APIRouter()

# In-memory conversation history per session
_conversation_store: dict[str, list[BaseMessage]] = {}

# Queue for tool progress updates
_progress_queues: dict[str, asyncio.Queue] = {}


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    session_id: str
    message: str
    research_data: Optional[dict] = None


class SessionResponse(BaseModel):
    """Session creation response."""
    session_id: str
    message: str


@router.post("/sessions", response_model=SessionResponse)
async def create_session():
    """Create a new research session."""
    session_id = str(uuid.uuid4())
    return SessionResponse(
        session_id=session_id,
        message="Session created successfully",
    )


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint with SSE streaming.
    
    Sends messages to the LangGraph agent and streams responses.
    """
    # Create or use existing session
    session_id = request.session_id or str(uuid.uuid4())
    
    # Debug: Log session info
    from app.graph.nodes.reflection import _session_research_data
    print(f"🔗 Chat request - session_id from client: {request.session_id}")
    print(f"🔗 Using session_id: {session_id}")
    print(f"📊 Active sessions in memory: {len(_conversation_store)} conversations, {len(_session_research_data)} research datasets")
    if session_id in _session_research_data:
        print(f"✅ Found existing research data: {len(_session_research_data[session_id].get('courses', []))} courses")
    else:
        print(f"⚠️ No existing research data for session {session_id[:8] if session_id else 'None'}")
    
    async def event_generator():
        """Generate SSE events from agent execution with real-time updates."""
        try:
            # Get or create conversation history for this session
            if session_id not in _conversation_store:
                _conversation_store[session_id] = []
            
            # Add current user message to history
            user_message = HumanMessage(content=request.message)
            _conversation_store[session_id].append(user_message)
            
            # Create state with FULL conversation history
            state = create_initial_state(session_id)
            state["messages"] = list(_conversation_store[session_id])  # All previous messages
            
            # IMPORTANT: Load existing research data for follow-up questions
            from app.graph.nodes.reflection import _session_research_data
            if session_id in _session_research_data:
                state["research_data"] = _session_research_data[session_id]
                print(f"📂 Loaded existing research data for session {session_id[:8]}: {len(state['research_data'].get('courses', []))} courses")
            
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
            
            # Send initial thinking status immediately (no trailing dots)
            yield f"data: {json.dumps({'type': 'thinking', 'status': 'Starting research', 'step': 0})}\n\n"
            await asyncio.sleep(0.02)
            
            step_count = 0
            last_node = None
            final_response_content = ""  # Track the final response
            
            # Create a shared queue for ALL SSE events
            event_queue = asyncio.Queue()
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
                        timeout=2.0  # Check every 2 seconds for timeout
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
                        
                        # Process graph event - send thinking status (NO EMOJIS)
                        if node_name == "reasoning":
                            yield f"data: {json.dumps({'type': 'thinking', 'status': 'Planning next action', 'step': step})}\n\n"
                        elif node_name == "tool_executor":
                            tool_call = node_output.get("current_tool_call") or state.get("current_tool_call")
                            tool_name = tool_call.get("name", "tool") if tool_call else "tool"
                            yield f"data: {json.dumps({'type': 'thinking', 'status': f'Executing {tool_name}', 'tool': tool_name, 'step': step})}\n\n"
                        elif node_name == "reflection":
                            yield f"data: {json.dumps({'type': 'thinking', 'status': 'Validating results', 'step': step})}\n\n"
                        elif node_name == "response":
                            yield f"data: {json.dumps({'type': 'thinking', 'status': 'Generating report', 'step': step})}\n\n"
                            print(f"RESPONSE NODE OUTPUT: {list(node_output.keys())}")
                        
                        await asyncio.sleep(0.02)
                        
                        # Build and send node event
                        event_data = {"type": "node", "node": node_name, "step": step}
                        
                        if "messages" in node_output:
                            for msg in node_output["messages"]:
                                if isinstance(msg, AIMessage) and msg.content:
                                    event_data["content"] = msg.content
                                    # Track final response from response node only
                                    if node_name == "response":
                                        is_status = msg.content.startswith(("Reasoning:", "Reflection:", "Found", "Searching", "Analyzing"))
                                        if not is_status and len(msg.content) > 500:  # Real reports are long
                                            final_response_content = msg.content
                                            print(f"CAPTURED FINAL RESPONSE: {len(final_response_content)} chars")
                                            # IMMEDIATELY send final_response event - don't wait
                                            yield f"data: {json.dumps({'type': 'final_response', 'content': final_response_content})}\n\n"
                                            await asyncio.sleep(0.1)  # Ensure it's flushed
                        
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
                        print(f"📤 Sending {node_name}: {len(event_json)} bytes, has_content={bool(event_data.get('content'))}")
                        yield f"data: {event_json}\n\n"
                        await asyncio.sleep(0.02)
                        
                        last_node = node_name
                
                except asyncio.TimeoutError:
                    # No events for 2 seconds - send a ping to keep connection alive
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
            
            # Cleanup progress callback
            set_progress_callback(None)
            if session_id in _progress_queues:
                del _progress_queues[session_id]
            
            # Save assistant response to conversation history
            if final_response_content:
                assistant_message = AIMessage(content=final_response_content)
                _conversation_store[session_id].append(assistant_message)
                print(f"Saved response to session {session_id}. History now has {len(_conversation_store[session_id])} messages.")
            else:
                print("WARNING: No final response content captured!")
            
            # Send completion event
            yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id, 'total_steps': step_count})}\n\n"
            
        except Exception as e:
            # Send error event
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
async def chat_sync(request: ChatRequest):
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


@router.get("/sessions/{session_id}/research")
async def get_session_research(session_id: str):
    """Get research data for a session."""
    from app.tools.database import get_research
    
    research = await get_research(session_id)
    return research


@router.post("/sessions/{session_id}/report")
async def generate_session_report(session_id: str, format: str = "markdown"):
    """Generate a research report for a session."""
    from app.tools.report import generate_report
    
    report = await generate_report(session_id, format)
    return report


class TitleRequest(BaseModel):
    """Title generation request."""
    message: str


@router.post("/sessions/generate-title")
async def generate_title(request: TitleRequest):
    """Generate a concise title for a research session based on the first message."""
    from app.services.anthropic import claude_client
    
    try:
        # Generate title using Claude
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
        
        # Clean up title
        title = title.strip().strip('"').strip("'")
        if len(title) > 60:
            title = title[:57] + "..."
        
        return {"title": title}
    
    except Exception as e:
        # Fallback to first few words
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

