"""Task definitions for content generation and editorial workflows."""

from .content_tasks import (
    # Primary content tasks (with content_types aliases)
    GENERATE_QUIZ,
    GENERATE_STORY,
    GENERATE_GAME,
    GENERATE_SIMULATION,
    # Block-level tasks
    GENERATE_BLOCK,
    GENERATE_SEQUENTIAL_BLOCKS,
    GENERATE_LOOPED_BLOCKS,
    GENERATE_BRANCHED_BLOCKS,
    GENERATE_CONDITIONAL_BLOCKS,
)
from .editorial_tasks import REFINE_CONTENT, REVIEW_CONTENT, VALIDATE_CONTENT

__all__ = [
    # Primary content tasks
    "GENERATE_QUIZ",
    "GENERATE_STORY",
    "GENERATE_GAME",
    "GENERATE_SIMULATION",
    # Block-level tasks
    "GENERATE_BLOCK",
    "GENERATE_SEQUENTIAL_BLOCKS",
    "GENERATE_LOOPED_BLOCKS",
    "GENERATE_BRANCHED_BLOCKS",
    "GENERATE_CONDITIONAL_BLOCKS",
    # Editorial tasks
    "REVIEW_CONTENT",
    "VALIDATE_CONTENT",
    "REFINE_CONTENT",
]
