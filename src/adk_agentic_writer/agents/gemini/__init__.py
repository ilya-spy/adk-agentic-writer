"""Gemini-powered agent implementations using Google ADK.

Provides real AI content generation via Google's Agent Development Kit.
Falls back to static templates if ADK is unavailable or API key not set.
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
from .prompts import (
    build_quiz_prompt,
    build_story_prompt,
    build_generation_prompt,
    get_system_instruction,
    QUIZ_SYSTEM_INSTRUCTION,
    STORY_SYSTEM_INSTRUCTION,
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
    # Prompts
    "build_quiz_prompt",
    "build_story_prompt",
    "build_generation_prompt",
    "get_system_instruction",
    "QUIZ_SYSTEM_INSTRUCTION",
    "STORY_SYSTEM_INSTRUCTION",
]
