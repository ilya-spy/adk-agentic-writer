"""ADK Agentic Writer - Multi-agent content generation system."""

from .agents import CoordinatorAgent
from .backend import app
from .models import ContentType
from .protocols import AgentProtocol

__version__ = "0.1.0"

__all__ = [
    "CoordinatorAgent",
    "ContentType",
    "app",
    "AgentProtocol",
]
