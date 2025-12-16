"""Tool executor node - executes the tool selected by reasoning node."""
import traceback
from langchain_core.messages import ToolMessage
from app.graph.state import AgentState, ToolResult
from app.tools import execute_tool


async def tool_executor_node(state: AgentState) -> dict:
    """
    Execute the tool specified in current_tool_call.
    
    This node:
    1. Gets the tool call from state
    2. Executes the tool with provided arguments
    3. Returns the result for reflection
    
    The tool result is NEVER fabricated - it comes directly from
    the actual tool execution (API calls, scraping, etc.)
    """
    
    tool_call = state.get("current_tool_call")
    
    if not tool_call:
        return {
            "current_tool_result": ToolResult(
                tool_name="unknown",
                success=False,
                data=None,
                error="No tool call specified",
            ),
            "next_node": "reflection",
        }
    
    tool_name = tool_call["name"]
    tool_args = tool_call["arguments"]
    
    print(f"🔧 TOOL EXECUTOR: Starting {tool_name} with args: {tool_args}")
    
    try:
        # Execute the tool
        print(f"🔧 TOOL EXECUTOR: Calling execute_tool...")
        result = await execute_tool(tool_name, tool_args)
        print(f"🔧 TOOL EXECUTOR: Tool {tool_name} completed successfully")
        
        tool_result = ToolResult(
            tool_name=tool_name,
            success=True,
            data=result,
            error=None,
        )
        
        # Create tool message for conversation history
        tool_message = ToolMessage(
            content=f"Tool '{tool_name}' executed successfully.",
            tool_call_id=f"{tool_name}_{state['session_id'][:8]}",
            name=tool_name,
        )
        
        return {
            "current_tool_result": tool_result,
            "next_node": "reflection",
            "messages": [tool_message],
        }
        
    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        
        tool_result = ToolResult(
            tool_name=tool_name,
            success=False,
            data=None,
            error=error_msg,
        )
        
        return {
            "current_tool_result": tool_result,
            "next_node": "reflection",
            "error": error_msg,
        }

