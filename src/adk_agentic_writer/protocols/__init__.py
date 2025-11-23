"""Protocol definitions for the agentic writer system.

This package contains protocol interfaces that define contracts for agents and content generation.

Protocols are pure interface definitions (using Python's Protocol from typing).
They define WHAT agents can do, not HOW they do it.
"""

from .agent_protocol import AgentProtocol
from .content_protocol import ContentBlock, ContentBlockType, ContentProtocol
from .editorial_protocol import EditorialProtocol

__all__ = [
    "AgentProtocol",
    "ContentProtocol",
    "ContentBlock",
    "ContentBlockType",
    "EditorialProtocol",
]
