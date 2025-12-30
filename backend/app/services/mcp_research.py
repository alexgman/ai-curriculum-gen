"""MCP-based Deep Research Service using Claude.

Implements Claude's Deep Research approach:
- Dynamic/adaptive search (not fixed counts)
- Iterative research with multiple passes
- Claude decides when it has enough information
- Extended thinking for reasoning transparency
"""
import asyncio
import json
from typing import AsyncGenerator, Optional, Dict, Any, List
from anthropic import Anthropic, AsyncAnthropic
from app.config import settings


class MCPDeepResearchService:
    """
    Deep Research service matching Claude.ai's Deep Research behavior.
    
    Key differences from static approach:
    1. Large search budget - Claude decides when to stop
    2. Iterative passes - identifies gaps and fills them
    3. Extended thinking - shows reasoning process
    4. Comprehensive by default - thorough coverage
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.anthropic_api_key
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"
    
    async def deep_research(
        self,
        prompt: str,
        system: str = None,
        max_searches: int = 50,  # Large budget - Claude stops when satisfied
        enable_thinking: bool = True,
        thinking_budget: int = 10000,  # Thinking budget
        max_tokens: int = 20000,  # Must be > thinking_budget
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Perform deep research like Claude.ai's Deep Research.
        
        Claude is given a large search budget but naturally stops when
        it has comprehensive information - just like claude.ai behavior.
        
        Args:
            prompt: Research prompt/question
            system: System prompt for context
            max_searches: Maximum searches (large budget, Claude decides when enough)
            enable_thinking: Enable extended thinking
            thinking_budget: Token budget for thinking (higher = deeper reasoning)
            max_tokens: Max output tokens (must be > thinking_budget)
        
        Yields:
            Events during research process
        """
        messages = [{"role": "user", "content": prompt}]
        
        # Ensure max_tokens > thinking_budget
        if max_tokens <= thinking_budget:
            max_tokens = thinking_budget + 8000
        
        # Build request - large budget, Claude decides coverage
        request_params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        
        # Only include web_search tool if searches are allowed
        if max_searches > 0:
            request_params["tools"] = [{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": max_searches,
            }]
        
        if system:
            request_params["system"] = system
        
        if enable_thinking:
            request_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget,
            }
        
        search_count = 0
        
        # Stream the response
        async with self.client.messages.stream(**request_params) as stream:
            current_thinking = ""
            current_text = ""
            
            async for event in stream:
                # Handle thinking blocks (extended thinking)
                if event.type == "content_block_start":
                    if hasattr(event.content_block, "type"):
                        if event.content_block.type == "thinking":
                            yield {"type": "thinking_start"}
                        elif event.content_block.type == "text":
                            yield {"type": "text_start"}
                        elif event.content_block.type == "tool_use":
                            search_count += 1
                            tool_data = {
                                "type": "tool_start",
                                "tool": event.content_block.name,
                                "id": event.content_block.id,
                                "search_number": search_count,
                            }
                            yield tool_data
                
                elif event.type == "content_block_delta":
                    delta = event.delta
                    
                    # Thinking content
                    if hasattr(delta, "type") and delta.type == "thinking_delta":
                        if hasattr(delta, "thinking"):
                            current_thinking += delta.thinking
                            yield {"type": "thinking", "content": delta.thinking}
                    
                    # Text content
                    elif hasattr(delta, "type") and delta.type == "text_delta":
                        if hasattr(delta, "text"):
                            current_text += delta.text
                            yield {"type": "text", "content": delta.text}
                    
                    # Tool input
                    elif hasattr(delta, "type") and delta.type == "input_json_delta":
                        if hasattr(delta, "partial_json"):
                            yield {"type": "tool_input", "content": delta.partial_json}
                
                elif event.type == "content_block_stop":
                    yield {"type": "block_stop"}
                
                elif event.type == "message_stop":
                    yield {
                        "type": "complete",
                        "thinking_length": len(current_thinking),
                        "text_length": len(current_text),
                        "total_searches": search_count,
                    }
    
    async def adaptive_deep_research(
        self,
        prompt: str,
        system: str = None,
        depth: str = "comprehensive",  # "quick", "standard", "comprehensive", "exhaustive"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Adaptive deep research matching Claude.ai's Deep Research behavior.
        
        This is the main method that mimics claude.ai's approach:
        1. First pass: Broad search to understand the landscape
        2. Second pass: Identify gaps and fill them
        3. Third pass: Deep dive into specific areas
        4. Claude decides coverage at each step
        
        Args:
            prompt: Research question
            system: System prompt
            depth: Research depth level
                - "quick": ~10-20 searches, fast overview
                - "standard": ~30-50 searches, good coverage
                - "comprehensive": ~50-80 searches, thorough (default)
                - "exhaustive": ~100+ searches, maximum depth
        """
        # Configure based on depth (like claude.ai's research modes)
        # Note: max_tokens (32000) must be > thinking budget
        depth_config = {
            "quick": {"searches": 20, "thinking": 8000, "passes": 1, "max_tokens": 16000},
            "standard": {"searches": 40, "thinking": 10000, "passes": 2, "max_tokens": 20000},
            "comprehensive": {"searches": 60, "thinking": 12000, "passes": 3, "max_tokens": 24000},
            "exhaustive": {"searches": 100, "thinking": 16000, "passes": 4, "max_tokens": 32000},
        }
        config = depth_config.get(depth, depth_config["comprehensive"])
        
        yield {
            "type": "research_config",
            "depth": depth,
            "max_searches": config["searches"],
            "passes": config["passes"],
        }
        
        all_findings = []
        total_searches = 0
        
        for pass_num in range(config["passes"]):
            yield {
                "type": "pass_start",
                "pass": pass_num + 1,
                "total_passes": config["passes"],
                "description": self._get_pass_description(pass_num),
            }
            
            # Build prompt for this pass
            if pass_num == 0:
                # First pass: Broad exploration
                current_prompt = f"""{prompt}

IMPORTANT: Conduct a COMPREHENSIVE search. Do NOT stop after just a few searches.
Search broadly to find ALL relevant information. Use many different search queries
to cover different aspects, providers, sources, and perspectives.

Be thorough - this is deep research, not a quick lookup."""
            else:
                # Subsequent passes: Fill gaps
                findings_summary = "\n---\n".join(all_findings[-2:])
                current_prompt = f"""{prompt}

PREVIOUS RESEARCH FINDINGS:
{findings_summary}

NEXT STEPS:
1. Review what we've found so far
2. Identify GAPS or areas needing more detail
3. Search for specific information we're missing
4. Find additional sources we haven't covered
5. Verify key claims with additional searches

Do NOT repeat information already found. Focus on NEW details and filling gaps.
Continue until you have comprehensive coverage."""
            
            # Research for this pass
            pass_findings = ""
            searches_this_pass = config["searches"] // config["passes"]
            
            async for event in self.deep_research(
                prompt=current_prompt,
                system=system,
                max_searches=searches_this_pass + 10,  # Buffer for thoroughness
                enable_thinking=True,
                thinking_budget=config["thinking"],
                max_tokens=config["max_tokens"],
            ):
                yield event
                
                if event.get("type") == "text":
                    pass_findings += event.get("content", "")
                elif event.get("type") == "complete":
                    total_searches += event.get("total_searches", 0)
            
            all_findings.append(pass_findings)
            
            yield {
                "type": "pass_complete",
                "pass": pass_num + 1,
                "searches_so_far": total_searches,
            }
        
        yield {
            "type": "research_complete",
            "total_passes": config["passes"],
            "total_searches": total_searches,
            "depth": depth,
        }
    
    def _get_pass_description(self, pass_num: int) -> str:
        """Get description for research pass."""
        descriptions = [
            "Broad exploration - surveying the landscape",
            "Gap analysis - filling missing information",
            "Deep dive - specific details and verification",
            "Final sweep - comprehensive coverage check",
        ]
        return descriptions[min(pass_num, len(descriptions) - 1)]
    
    async def iterative_research(
        self,
        initial_prompt: str,
        system: str = None,
        max_iterations: int = 3,
        max_searches_per_iteration: int = 20,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Legacy iterative research method.
        
        For new implementations, use adaptive_deep_research() instead.
        """
        # Redirect to adaptive research
        depth = "standard" if max_iterations <= 2 else "comprehensive"
        async for event in self.adaptive_deep_research(
            prompt=initial_prompt,
            system=system,
            depth=depth,
        ):
            yield event


# Singleton instance
mcp_research_service = MCPDeepResearchService()

