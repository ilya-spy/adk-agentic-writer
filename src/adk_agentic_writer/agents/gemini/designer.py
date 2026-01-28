"""Gemini-powered designer agent (stub).

TODO: Implement ADK integration for LLM-powered content generation.
Currently mirrors the static DesignerAgent interface.
"""

from typing import Any, Dict, Optional

from ..static.designer import DesignerAgent
from ...utils.text_provider import GeminiTextProvider


class GeminiDesignerAgent(DesignerAgent):
    """Gemini designer agent stub.

    Placeholder for ADK-powered content generation.
    Currently inherits from static DesignerAgent.
    """

    def __init__(
        self,
        agent_id: str = "gemini_designer",
        content_type: str = "game",
    ):
        super().__init__(
            agent_id=agent_id,
            content_type=content_type,
            text_provider=GeminiTextProvider(),
        )


# Backward-compatible aliases
class GeminiGameDesignerAgent(GeminiDesignerAgent):
    """Gemini game designer (stub)."""

    def __init__(self, agent_id: str = "gemini_game_designer"):
        super().__init__(agent_id=agent_id, content_type="game")


class GeminiSimulationDesignerAgent(GeminiDesignerAgent):
    """Gemini simulation designer (stub)."""

    def __init__(self, agent_id: str = "gemini_simulation_designer"):
        super().__init__(agent_id=agent_id, content_type="simulation")


__all__ = [
    "GeminiDesignerAgent",
    "GeminiGameDesignerAgent",
    "GeminiSimulationDesignerAgent",
]
