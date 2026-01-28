"""Gemini-powered writer agent (stub).

TODO: Implement ADK integration for LLM-powered content generation.
Currently mirrors the static WriterAgent interface.
"""

from typing import Any, Dict, Optional

from ..static.writer import WriterAgent
from ...utils.text_provider import GeminiTextProvider


class GeminiWriterAgent(WriterAgent):
    """Gemini writer agent stub.

    Placeholder for ADK-powered content generation.
    Currently inherits from static WriterAgent.
    """

    def __init__(
        self,
        agent_id: str = "gemini_writer",
        content_type: str = "quiz",
    ):
        super().__init__(
            agent_id=agent_id,
            content_type=content_type,
            text_provider=GeminiTextProvider(),
        )


# Backward-compatible aliases
class GeminiQuizWriterAgent(GeminiWriterAgent):
    """Gemini quiz writer (stub)."""

    def __init__(self, agent_id: str = "gemini_quiz_writer"):
        super().__init__(agent_id=agent_id, content_type="quiz")


class GeminiStoryWriterAgent(GeminiWriterAgent):
    """Gemini story writer (stub)."""

    def __init__(self, agent_id: str = "gemini_story_writer"):
        super().__init__(agent_id=agent_id, content_type="story")


__all__ = ["GeminiWriterAgent", "GeminiQuizWriterAgent", "GeminiStoryWriterAgent"]
