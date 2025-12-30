import asyncio
import httpx
import uuid

async def test_phase1():
    """Test Phase 1 research to see what streams."""
    session_id = str(uuid.uuid4())
    client_id = str(uuid.uuid4())
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # First: send topic
        print("=" * 60)
        print("STEP 1: Sending topic...")
        print("=" * 60)
        
        async with client.stream(
            "POST",
            "http://localhost:8000/api/v1/chat",
            json={
                "message": "HVAC technician training",
                "session_id": session_id,
                "client_id": client_id,
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    import json
                    try:
                        event = json.loads(line[6:])
                        if event.get("type") == "text":
                            print(f"[TEXT] {event.get('content', '')}", end="", flush=True)
                        elif event.get("type") == "clarification":
                            print("\n[CLARIFICATION COMPLETE]")
                    except:
                        pass
        
        print("\n")
        print("=" * 60)
        print("STEP 2: Answering clarification, starting Phase 1...")
        print("=" * 60)
        
        # Send clarification answers
        async with client.stream(
            "POST",
            "http://localhost:8000/api/v1/chat",
            json={
                "message": "Complete beginners, USA, residential and commercial, 6 month program",
                "session_id": session_id,
                "client_id": client_id,
            },
        ) as response:
            event_count = 0
            text_content = ""
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_count += 1
                    import json
                    try:
                        event = json.loads(line[6:])
                        event_type = event.get("type", "")
                        
                        if event_type == "text":
                            chunk = event.get("content", "")
                            text_content += chunk
                            print(chunk, end="", flush=True)
                        elif event_type == "status":
                            print(f"\n[STATUS] {event.get('content', '')}")
                        elif event_type == "phase_start":
                            print(f"\n[PHASE START] {event.get('title', '')}")
                        elif event_type == "search":
                            print(f"\n[SEARCH #{event.get('number', 0)}]", end="")
                        elif event_type == "thinking":
                            pass  # Skip thinking output
                        elif event_type == "phase_complete":
                            print(f"\n[PHASE COMPLETE]")
                        elif event_type == "feedback_request":
                            print(f"\n[FEEDBACK REQUEST] {event.get('content', '')[:100]}")
                        elif event_type == "error":
                            print(f"\n[ERROR] {event.get('message', '')}")
                        elif event_type == "done":
                            print("\n[DONE]")
                            
                        # Stop after 200 events for manageable output  
                        if event_count >= 200:
                            print("\n... stopping after 200 events")
                            break
                    except Exception as e:
                        print(f"\n[ERROR parsing] {e}")
            
            print("\n")
            print("=" * 60)
            print(f"Total events: {event_count}")
            print(f"Total TEXT chars: {len(text_content)}")
            print("=" * 60)

asyncio.run(test_phase1())
