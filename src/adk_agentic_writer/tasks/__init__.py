"""Task definitions for the ADK Agentic Writer."""

from .content_tasks import IDEATE, WRITE
from .editorial_tasks import REVIEW, REFINE, PUBLISH

ALL_TASKS = [IDEATE, WRITE, REVIEW, REFINE, PUBLISH]

__all__ = [
    "IDEATE",
    "WRITE",
    "REVIEW",
    "REFINE",
    "PUBLISH",
    "ALL_TASKS",
]
