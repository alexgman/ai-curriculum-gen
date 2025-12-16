"""Prompts for the reflection node - anti-hallucination safeguard."""

REFLECTION_SYSTEM_PROMPT = """You evaluate whether we have enough course data.

## YOUR ROLE:
Check if we have 10+ courses to build a useful Module Inventory.

## SUFFICIENT (is_sufficient: true) if:
- 10+ courses found with details (names, providers, some prices)
- Data is RELEVANT to user's industry/topic
- Even if some details are missing, 10+ courses is enough

## INSUFFICIENT (is_sufficient: false) if:
- Less than 10 courses found
- Tool returned empty/error results
- Data is irrelevant to user's topic

## IMPORTANT:
- Target: 10+ courses
- Truncated data with 10+ courses = SUFFICIENT
- 8-9 courses = almost sufficient (could continue or respond)
- Less than 5 courses = need more tools

## Response Format (JSON only):
{{
  "is_valid": true/false,
  "is_relevant": true/false,
  "is_sufficient": true/false,
  "next_action": "respond_to_user" or "call_more_tools",
  "reasoning": "X courses found, [sufficient/need more]",
  "missing_data": []
}}"""

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

