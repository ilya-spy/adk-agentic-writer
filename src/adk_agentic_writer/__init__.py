"""ADK Agentic Writer - Multi-agent content generation system."""

from .agents import Coordinator
from .backend import app
from .models import ContentType

__version__ = "2.0.0"

__all__ = [
    "Coordinator",
    "ContentType",
    "app",
]
