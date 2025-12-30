"""Tool definitions for database operations."""
from app.tools.database import save_research, get_research
from app.tools.report import generate_report

# Simplified tool registry - only keeping database and report tools
TOOLS = {
    "save_research": save_research,
    "get_research": get_research,
    "generate_report": generate_report,
}

__all__ = ["TOOLS", "save_research", "get_research", "generate_report"]
