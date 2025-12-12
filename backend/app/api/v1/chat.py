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
            
            # Send initial thinking status immediately
            yield f"data: {json.dumps({'type': 'thinking', 'status': 'Starting research...', 'step': 0})}\n\n"
            await asyncio.sleep(0.02)
            
            step_count = 0
            last_node = None
            final_response_content = ""  # Track the final response
            
            # Stream through the graph with immediate updates
            async for event in research_graph.astream(state):
                # Check for progress updates from tools
                while not progress_queue.empty():
                    try:
                        progress_msg = progress_queue.get_nowait()
                        yield f"data: {json.dumps({'type': 'thinking', 'status': progress_msg, 'step': step_count})}\n\n"
                        await asyncio.sleep(0.01)
                    except asyncio.QueueEmpty:
                        break
                # Process each event from the graph
                for node_name, node_output in event.items():
                    step_count += 1
                    
                    # Send immediate thinking status BEFORE processing
                    if node_name == "reasoning":
                        yield f"data: {json.dumps({'type': 'thinking', 'status': 'Planning next action...', 'step': step_count})}\n\n"
                        await asyncio.sleep(0.02)
                    elif node_name == "tool_executor":
                        tool_call = node_output.get("current_tool_call") or state.get("current_tool_call")
                        tool_name = tool_call.get("name", "tool") if tool_call else "tool"
                        yield f"data: {json.dumps({'type': 'thinking', 'status': f'Executing {tool_name}...', 'tool': tool_name, 'step': step_count})}\n\n"
                        await asyncio.sleep(0.02)
                    elif node_name == "reflection":
                        yield f"data: {json.dumps({'type': 'thinking', 'status': 'Validating results...', 'step': step_count})}\n\n"
                        await asyncio.sleep(0.02)
                    elif node_name == "response":
                        yield f"data: {json.dumps({'type': 'thinking', 'status': 'Generating response...', 'step': step_count})}\n\n"
                        await asyncio.sleep(0.02)
                    
                    # Build node event data
                    event_data = {
                        "type": "node",
                        "node": node_name,
                        "step": step_count,
                    }
                    
                    # Extract relevant info from node output
                    if "messages" in node_output:
                        messages = node_output["messages"]
                        for msg in messages:
                            if isinstance(msg, AIMessage):
                                if msg.content:
                                    event_data["content"] = msg.content
                                    # Track final response (from response node, not internal messages)
                                    if node_name == "response" and not msg.content.startswith(("Reasoning:", "Reflection:")):
                                        final_response_content = msg.content
                    
                    # Include reasoning explanation if available
                    if "reasoning_explanation" in node_output:
                        event_data["reasoning"] = node_output["reasoning_explanation"]
                    
                    # Include reflection explanation if available
                    if "reflection_explanation" in node_output:
                        event_data["reflection"] = node_output["reflection_explanation"]
                    
                    if "current_tool_call" in node_output and node_output["current_tool_call"]:
                        tool_call = node_output["current_tool_call"]
                        event_data["tool_call"] = {
                            "name": tool_call.get("name"),
                            "arguments": tool_call.get("arguments", {}),
                        }
                    
                    if "current_tool_result" in node_output and node_output["current_tool_result"]:
                        result = node_output["current_tool_result"]
                        event_data["tool_result"] = {
                            "name": result.get("tool_name"),
                            "success": result.get("success"),
                        }
                    
                    if "research_data" in node_output:
                        event_data["research_summary"] = _summarize_research(node_output["research_data"])
                    
                    # Send node event immediately
                    yield f"data: {json.dumps(event_data)}\n\n"
                    await asyncio.sleep(0.02)  # Ensure event is flushed
                    
                    last_node = node_name
            
            # Cleanup progress callback
            set_progress_callback(None)
            if session_id in _progress_queues:
                del _progress_queues[session_id]
            
            # Save assistant response to conversation history
            if final_response_content:
                assistant_message = AIMessage(content=final_response_content)
                _conversation_store[session_id].append(assistant_message)
                print(f"📝 Saved response to session {session_id}. History now has {len(_conversation_store[session_id])} messages.")
            
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

