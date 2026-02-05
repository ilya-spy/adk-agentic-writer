"""Protocol definitions for the agentic writer system."""

from .agent_protocol import AgentProtocol
from .content_protocol import AdaptiveContentProtocol, ContentProtocol

__all__ = [
    "AgentProtocol",
    "ContentProtocol",
    "AdaptiveContentProtocol",
]
