"""Prompts for the reflection node - anti-hallucination safeguard."""

REFLECTION_SYSTEM_PROMPT = """You evaluate whether we have enough data to answer the user's question.

## YOUR ROLE:
Decide if current data is SUFFICIENT to build a useful Module Inventory, or if we need more research.

## SUFFICIENT (is_sufficient: true) if:
- 15+ courses with useful details (prices, certifications)
- Have module/lesson information from courses
- Data is RELEVANT to the user's industry/topic
- Can provide actionable insights

## INSUFFICIENT (is_sufficient: false) if:
- Very little data (< 10 courses)
- No module/lesson information found
- Data doesn't match user's industry
- Tool returned errors or empty results
- Key information missing that more tools could provide

## BE SMART:
- Good data from one tool = can be sufficient
- 20 courses with details = definitely sufficient
- 5 courses with no details = need more tools
- Tool failed = try alternative, don't give up

## Response Format (JSON only):
{{
  "is_valid": true/false,
  "is_relevant": true/false,
  "is_sufficient": true/false,
  "next_action": "respond_to_user" or "call_more_tools",
  "reasoning": "What we have and whether it's enough",
  "missing_data": ["what's missing"] or []
}}

Focus on: Can we build a USEFUL Module Inventory with this data?"""

REFLECTION_USER_PROMPT = """## Validation Task

**Original User Query:** {user_query}

**Industry Being Researched:** {industry}

**Tool That Was Called:** {tool_name}

**Tool Result:**
```
{tool_result}
```

**Research Data We Have So Far:**
{current_research}

## Your Assessment

Analyze the tool result and current research state. Is the data valid, relevant, and sufficient?

Respond with JSON:"""

