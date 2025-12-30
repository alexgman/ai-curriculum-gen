import asyncio
import httpx
import uuid

async def test_chat():
    """Test the chat API and see what events come back."""
    session_id = str(uuid.uuid4())  # Proper UUID format
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        print(f"Session ID: {session_id}")
        print("Sending request to /api/v1/chat...")
        
        async with client.stream(
            "POST",
            "http://localhost:8000/api/v1/chat",
            json={
                "message": "HVAC technician training",
                "session_id": session_id,
                "client_id": str(uuid.uuid4()),
            },
        ) as response:
            print(f"Status: {response.status_code}")
            print("=" * 60)
            print("STREAMING EVENTS (first 100):")
            print("=" * 60)
            
            event_count = 0
            text_content = ""
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_count += 1
                    data = line[6:]
                    
                    try:
                        import json
                        event = json.loads(data)
                        event_type = event.get("type", "unknown")
                        
                        if event_type == "text":
                            content = event.get("content", "")
                            text_content += content
                            # Show text chunks
                            display = content[:80] + "..." if len(content) > 80 else content
                            print(f"[TEXT] {display}")
                        elif event_type == "thinking":
                            print(f"[THINKING] +{len(event.get('content', ''))} chars")
                        elif event_type == "search":
                            print(f"[SEARCH] #{event.get('number', 0)}")
                        elif event_type == "phase_start":
                            print(f"[PHASE_START] {event.get('title', '')}")
                        elif event_type == "status":
                            print(f"[STATUS] {event.get('content', '')[:60]}")
                        elif event_type == "error":
                            print(f"[ERROR] {event.get('message', '')}")
                        elif event_type in ["done", "session"]:
                            print(f"[{event_type.upper()}]")
                        else:
                            print(f"[{event_type.upper()}] {str(event)[:60]}")
                            
                        if event_count >= 100:
                            print("\n... stopping after 100 events")
                            break
                            
                    except Exception as e:
                        print(f"[PARSE_ERROR] {e}")
            
            print("\n" + "=" * 60)
            print(f"Total events: {event_count}")
            print(f"Total TEXT content: {len(text_content)} chars")
            print("=" * 60)
            
            if text_content:
                print("\n=== TEXT CONTENT (first 1000 chars) ===")
                print(text_content[:1000])

asyncio.run(test_chat())
