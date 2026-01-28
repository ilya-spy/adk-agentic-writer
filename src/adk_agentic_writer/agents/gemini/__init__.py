"""Gemini-powered agent implementations (stubs).

Placeholder implementations that mirror the static team structure.
ADK integration will be added later for actual LLM-powered generation.
"""

from .coordinator import GeminiCoordinatorAgent, SupportedTask
from .writer import GeminiWriterAgent, GeminiQuizWriterAgent, GeminiStoryWriterAgent
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
]
