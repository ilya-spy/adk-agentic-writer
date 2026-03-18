"""Team configurations (legacy -- prompts now live in formats/)."""

from .content_team import (
    CONTENT_WRITER,
    GAME_WRITER,
    QUIZ_WRITER,
    SIMULATION_WRITER,
    STORY_WRITER,
    ContentRole,
    get_config_for_role,
)

__all__ = [
    "ContentRole",
    "CONTENT_WRITER",
    "STORY_WRITER",
    "QUIZ_WRITER",
    "GAME_WRITER",
    "SIMULATION_WRITER",
    "get_config_for_role",
]
