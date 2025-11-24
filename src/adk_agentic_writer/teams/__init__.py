"""Team configurations with agent pools."""

from .content_team import (
    CONTENT_WRITER,
    GAME_WRITER,
    GAME_WRITERS_POOL,
    QUIZ_WRITER,
    QUIZ_WRITERS_POOL,
    SIMULATION_WRITER,
    SIMULATION_WRITERS_POOL,
    STORY_WRITER,
    STORY_WRITERS_POOL,
    ContentRole,
)
from .editorial_team import (
    EDITORIAL_GROUP_POOL,
    EDITORIAL_REFINER,
    EDITORIAL_REFINERS_POOL,
    EDITORIAL_REVIEWER,
    EDITORIAL_REVIEWERS_POOL,
    EditorialRole,
)

__all__ = [
    # Content roles
    "ContentRole",
    # Content agents
    "CONTENT_WRITER",
    "STORY_WRITER",
    "QUIZ_WRITER",
    "GAME_WRITER",
    "SIMULATION_WRITER",
    # Content pools
    "STORY_WRITERS_POOL",
    "QUIZ_WRITERS_POOL",
    "GAME_WRITERS_POOL",
    "SIMULATION_WRITERS_POOL",
    # Editorial roles
    "EditorialRole",
    # Editorial agents
    "EDITORIAL_REVIEWER",
    "EDITORIAL_REFINER",
    # Editorial pools
    "EDITORIAL_REVIEWERS_POOL",
    "EDITORIAL_REFINERS_POOL",
    "EDITORIAL_GROUP_POOL",
]
