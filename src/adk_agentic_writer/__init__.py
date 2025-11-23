"""Main package initialization."""

from .agents import CoordinatorAgent
from .backend import app
from .models import ContentRequest, ContentResponse, ContentType
from .protocols import AgentProtocol, ContentProtocol, EditorialProtocol

__version__ = "0.1.0"

__all__ = [
    "CoordinatorAgent",
    "ContentRequest",
    "ContentResponse",
    "ContentType",
    "app",
    "AgentProtocol",
    "ContentProtocol",
    "EditorialProtocol",
]
