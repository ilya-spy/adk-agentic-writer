"""Gemini-powered coordinator agent (stub).

TODO: Implement ADK integration for intelligent task routing.
Currently mirrors the static CoordinatorAgent interface.
"""

from enum import Enum

from ..static.coordinator import CoordinatorAgent
from .writer import GeminiWriterAgent
from .designer import GeminiDesignerAgent


class SupportedTask(str, Enum):
    """Tasks supported by the Gemini coordinator."""

    GENERATE_QUIZ = "generate_quiz"
    GENERATE_STORY = "generate_story"
    GENERATE_GAME = "generate_game"
    GENERATE_SIMULATION = "generate_simulation"


class GeminiCoordinatorAgent(CoordinatorAgent):
    """Gemini coordinator agent stub.

    Placeholder for ADK-powered intelligent coordination.
    Currently inherits from static CoordinatorAgent.
    """

    def __init__(self, agent_id: str = "gemini_coordinator"):
        super().__init__(agent_id=agent_id)
        # Override with Gemini agents (stubs for now)
        self._writer = GeminiWriterAgent("gemini_writer")
        self._designer = GeminiDesignerAgent("gemini_designer")


__all__ = ["GeminiCoordinatorAgent", "SupportedTask"]
