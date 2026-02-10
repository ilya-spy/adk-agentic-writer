"""Gemini-powered coordinator agent using ADK.

Routes content generation tasks to Gemini-powered writer and designer agents.
Requires GOOGLE_API_KEY for LLM generation.
"""

import logging
from enum import Enum
from typing import Any, Dict

from ..static.coordinator import CoordinatorAgent
from .writer import GeminiWriterAgent
from .designer import GeminiDesignerAgent

logger = logging.getLogger(__name__)


class SupportedTask(str, Enum):
    """Tasks supported by the Gemini coordinator."""

    GENERATE_QUIZ = "generate_quiz"
    GENERATE_STORY = "generate_story"
    GENERATE_GAME = "generate_game"
    GENERATE_SIMULATION = "generate_simulation"


class GeminiCoordinatorAgent(CoordinatorAgent):
    """Gemini coordinator using ADK-powered agents.

    Replaces static agents with Gemini agents and rebuilds task mappings.
    """

    def __init__(self, agent_id: str = "gemini_coordinator"):
        super().__init__(agent_id=agent_id)

        # Replace with Gemini agents
        self._writer = GeminiWriterAgent("gemini_writer")
        self._designer = GeminiDesignerAgent("gemini_designer")

        # CRITICAL: Rebuild task mappings with Gemini agents
        self._task_to_agent: Dict[str, Any] = {}
        for agent in [self._writer, self._designer]:
            for task in agent.get_supported_tasks():
                self._task_to_agent[task.task_id] = agent

        # Rebuild content_type -> task mapping
        self._content_type_to_task = {}
        for task in self.get_supported_tasks():
            for ct in task.content_types:
                self._content_type_to_task[ct] = task

        logger.info(
            f"GeminiCoordinator: {len(self._task_to_agent)} tasks mapped to Gemini agents"
        )


__all__ = ["GeminiCoordinatorAgent", "SupportedTask"]
