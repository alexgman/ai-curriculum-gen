"""Prompt templates for the research agent."""
from app.prompts.reasoning import REASONING_SYSTEM_PROMPT, REASONING_USER_PROMPT
from app.prompts.reflection import REFLECTION_SYSTEM_PROMPT, REFLECTION_USER_PROMPT
from app.prompts.response import RESPONSE_SYSTEM_PROMPT, RESPONSE_USER_PROMPT
from app.prompts.curriculum import (
    PARSE_EXPERT_INPUT_PROMPT,
    CURRICULUM_PROPOSAL_PROMPT,
    CURRICULUM_REFINEMENT_PROMPT,
    CURRICULUM_GENERATION_PROMPT,
    format_proposal_for_display,
    format_refinement_display,
)

__all__ = [
    "REASONING_SYSTEM_PROMPT",
    "REASONING_USER_PROMPT",
    "REFLECTION_SYSTEM_PROMPT", 
    "REFLECTION_USER_PROMPT",
    "RESPONSE_SYSTEM_PROMPT",
    "RESPONSE_USER_PROMPT",
    "PARSE_EXPERT_INPUT_PROMPT",
    "CURRICULUM_PROPOSAL_PROMPT",
    "CURRICULUM_REFINEMENT_PROMPT",
    "CURRICULUM_GENERATION_PROMPT",
    "format_proposal_for_display",
    "format_refinement_display",
]

