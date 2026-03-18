"""Publisher agent -- full ideate-write-review-refine pipeline."""

import json
import logging
from typing import Any, Dict, List

from ..formats import get_format
from ..tasks import PUBLISH
from .base import BaseAgentService, MODEL
from .ideator import IdeatorAgent
from .writer import WriterAgent
from .reviewer import ReviewerAgent
from .refiner import RefinerAgent

logger = logging.getLogger(__name__)


class PublisherAgent(BaseAgentService):
    """Orchestrates the full publish pipeline via sub-agent services."""

    def __init__(self, model: str = MODEL):
        super().__init__(model=model)
        self._register_tasks([PUBLISH])
        self._ideator = IdeatorAgent(model)
        self._writer = WriterAgent(model)
        self._reviewer = ReviewerAgent(model)
        self._refiner = RefinerAgent(model)

    async def process_task(
        self, task_id: str, params: Dict[str, Any],
    ) -> Dict[str, Any]:
        stages: List[Dict[str, Any]] = []
        fmt_name = params.get("format", params.get("flavor", "quiz"))
        topic = params.get("topic", "general")

        draft = await self._writer.process_task("write", {
            "format": fmt_name,
            "flavor": fmt_name,
            "topic": topic,
            **{k: v for k, v in params.items() if k not in ("format", "topic")},
        })
        stages.append({"stage": "write", "output": draft})

        review = await self._reviewer.process_task("review", {
            "draft_content": draft,
            "format": fmt_name,
        })
        stages.append({"stage": "review", "output": review})

        if not review.get("valid", True) or review.get("score", 100) < 90:
            refined = await self._refiner.process_task("refine", {
                "draft_content": draft,
                "review_result": review,
            })
            stages.append({"stage": "refine", "output": refined})
            final = refined
        else:
            final = draft

        return {
            "content": final,
            "validation_result": review,
            "stages": stages,
        }
