"""Agent modules for the ADK Agentic Writer system."""

# Base agent classes
from .base_agent import BaseAgent
from .stateful_agent import StatefulAgent
from .content_writer import ContentWriterAgent
from .text_provider import TextProvider, TemplateTextProvider, GeminiTextProvider

# Protocols (imported from protocols package)
from ..protocols import AgentProtocol, EditorialProtocol

# Static agents (template-based)
from .static import (
    CoordinatorAgent,
    GameDesignerAgent,
    StaticQuizWriterAgent,
    ReviewerAgent,
    SimulationDesignerAgent,
    StoryWriterAgent,
)

# Gemini-powered agents (AI-based using Google ADK)
# These are optional and require google.adk package
try:
    from .gemini import (
        GeminiCoordinatorAgent,
        GeminiGameDesignerAgent,
        GeminiQuizWriterAgent,
        GeminiReviewerAgent,
        GeminiSimulationDesignerAgent,
        GeminiStoryWriterAgent,
        SupportedTask,
    )

    _GEMINI_AVAILABLE = True
except ImportError:
    # Gemini agents not available (google.adk not installed)
    _GEMINI_AVAILABLE = False
    GeminiCoordinatorAgent = None
    GeminiGameDesignerAgent = None
    GeminiQuizWriterAgent = None
    GeminiReviewerAgent = None
    GeminiSimulationDesignerAgent = None
    GeminiStoryWriterAgent = None
    SupportedTask = None

__all__ = [
    # Base agent classes and protocols
    "BaseAgent",
    "StatefulAgent",
    "ContentWriterAgent",
    "TextProvider",
    "TemplateTextProvider",
    "GeminiTextProvider",
    "AgentProtocol",
    "EditorialProtocol",
    # Static agents (template-based)
    "StaticQuizWriterAgent",
    "StoryWriterAgent",
    "GameDesignerAgent",
    "SimulationDesignerAgent",
    "ReviewerAgent",
    "CoordinatorAgent",
    # Gemini agents (AI-powered using Google ADK)
    "GeminiCoordinatorAgent",
    "SupportedTask",
    "GeminiQuizWriterAgent",
    "GeminiStoryWriterAgent",
    "GeminiGameDesignerAgent",
    "GeminiSimulationDesignerAgent",
    "GeminiReviewerAgent",
]
