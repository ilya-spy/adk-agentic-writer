"""Agent modules for the ADK Agentic Writer system."""

# Base agent classes
from .base_agent import BaseAgent
from .stateful_agent import StatefulAgent
from .content_agent import ContentWriterAgent

# Utilities (from utils)
from ..utils.text_provider import TextProvider, TemplateTextProvider, GeminiTextProvider
from ..utils.content_registry import (
    CONTENT_REGISTRY,
    ContentTypeConfig,
    ContentRegistry,
)

# Protocols
from ..protocols import AgentProtocol

# Static agents (primary implementation)
from .static import (
    CoordinatorAgent,
    WriterAgent,
    DesignerAgent,
    StaticQuizWriterAgent,
    StoryWriterAgent,
    GameDesignerAgent,
    SimulationDesignerAgent,
)

# Gemini agents (stubs - ADK integration pending)
from .gemini import (
    GeminiCoordinatorAgent,
    GeminiWriterAgent,
    GeminiDesignerAgent,
    GeminiQuizWriterAgent,
    GeminiStoryWriterAgent,
    GeminiGameDesignerAgent,
    GeminiSimulationDesignerAgent,
    SupportedTask,
)

__all__ = [
    # Base classes
    "BaseAgent",
    "StatefulAgent",
    "ContentWriterAgent",
    # Utilities
    "TextProvider",
    "TemplateTextProvider",
    "GeminiTextProvider",
    "CONTENT_REGISTRY",
    "ContentTypeConfig",
    "ContentRegistry",
    # Protocols
    "AgentProtocol",
    # Static agents
    "CoordinatorAgent",
    "WriterAgent",
    "DesignerAgent",
    "StaticQuizWriterAgent",
    "StoryWriterAgent",
    "GameDesignerAgent",
    "SimulationDesignerAgent",
    # Gemini agents (stubs)
    "GeminiCoordinatorAgent",
    "GeminiWriterAgent",
    "GeminiDesignerAgent",
    "GeminiQuizWriterAgent",
    "GeminiStoryWriterAgent",
    "GeminiGameDesignerAgent",
    "GeminiSimulationDesignerAgent",
    "SupportedTask",
]
