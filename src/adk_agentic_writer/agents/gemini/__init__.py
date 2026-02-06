"""Gemini-powered agent implementations using Google ADK.

Provides real AI content generation via Google's Agent Development Kit.
Falls back to static templates if ADK is unavailable or API key not set.

Prompts and configurations are defined in teams/content_team.py.
Use get_config_for_role() to get AgentConfig with prompts for a role.
"""

from .coordinator import GeminiCoordinatorAgent, SupportedTask
from .writer import (
    GeminiWriterAgent,
    GeminiQuizWriterAgent,
    GeminiStoryWriterAgent,
    ADKAgentWrapper,
    GeminiTextProvider,
)
from .designer import (
    GeminiDesignerAgent,
    GeminiGameDesignerAgent,
    GeminiSimulationDesignerAgent,
)

__all__ = [
    # Coordinator
    "GeminiCoordinatorAgent",
    "SupportedTask",
    # Unified agents
    "GeminiWriterAgent",
    "GeminiDesignerAgent",
    # Writer aliases
    "GeminiQuizWriterAgent",
    "GeminiStoryWriterAgent",
    # Designer aliases
    "GeminiGameDesignerAgent",
    "GeminiSimulationDesignerAgent",
    # ADK utilities
    "ADKAgentWrapper",
    "GeminiTextProvider",
]
