"""Gemini-powered coordinator agent using ADK.

Routes content generation tasks to Gemini-powered writer and designer agents.
Requires GOOGLE_API_KEY for LLM generation.
"""

import logging
from typing import Any, Dict

from ..static.coordinator import CoordinatorAgent
from .validator import GeminiValidator
from .writer import GeminiWriterAgent
from .designer import GeminiDesignerAgent

logger = logging.getLogger(__name__)


class GeminiCoordinatorAgent(CoordinatorAgent):
    """Gemini coordinator using ADK-powered agents.

    Replaces static agents with Gemini agents, rebuilds task mappings,
    and calls inherited _build_validation_workflow() to rewire the
    validation pipeline with the new agents.
    """

    def __init__(self, agent_id: str = "gemini_coordinator"):
        super().__init__(agent_id=agent_id)

        # Replace with Gemini-powered agents
        self._validator = GeminiValidator(f"{agent_id}_validator")
        self._writer = GeminiWriterAgent("gemini_writer")
        self._designer = GeminiDesignerAgent("gemini_designer")

        # Rebuild task mappings with Gemini agents
        self._task_to_agent: Dict[str, Any] = {}
        for agent in [self._writer, self._designer]:
            for task in agent.get_supported_tasks():
                self._task_to_agent[task.task_id] = agent

        # Rebuild validation workflow with Gemini agents (inherited helper)
        self._build_validation_workflow()

        logger.info(
            f"GeminiCoordinator: {len(self._task_to_agent)} tasks mapped to Gemini agents"
        )


__all__ = ["GeminiCoordinatorAgent"]
