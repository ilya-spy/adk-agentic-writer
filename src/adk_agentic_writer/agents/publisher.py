"""Publisher agent -- full ideate-write-review/refine pipeline via ADK."""

import logging
from typing import Any, Dict

from google.adk.agents import Agent

from ..tasks import PUBLISH
from ..workflows.publish import create_publish_pipeline
from .base import BaseAgentService, MODEL

logger = logging.getLogger(__name__)


class PublisherAgentService(BaseAgentService):
    """Runs the full publish pipeline as an ADK SequentialAgent.

    Accepts pre-built ADK agents: ideator, per-format writers dict,
    reviewer, and refiner.  Builds a pipeline per format on demand.
    """

    def __init__(
        self,
        ideator: Agent,
        writers: Dict[str, Agent],
        reviewer: Agent,
        refiner: Agent,
        model: str = MODEL,
    ):
        super().__init__(model=model)
        self._register_tasks([PUBLISH])
        self._ideator = ideator
        self._writers = writers
        self._reviewer = reviewer
        self._refiner = refiner
        self._pipelines: Dict[str, Any] = {}

    def _get_pipeline(self, fmt_name: str):
        if fmt_name not in self._pipelines:
            writer = self._writers.get(
                fmt_name, next(iter(self._writers.values())),
            )
            self._pipelines[fmt_name] = create_publish_pipeline(
                self._ideator, writer, self._reviewer, self._refiner,
            )
        return self._pipelines[fmt_name]

    def prepare_task(
        self, task_id: str, params: Dict[str, Any],
    ) -> str:
        fmt_name = params.get("format", params.get("flavor", "quiz"))
        topic = params.get("topic", "general")
        self._last_fmt_name = fmt_name
        return f"Create {fmt_name} about {topic}"

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        fmt_name = getattr(self, "_last_fmt_name", "quiz")
        pipeline = self._get_pipeline(fmt_name)
        runner = self._ensure_runner(f"publish_{fmt_name}", pipeline)
        return await self._run(runner, pipeline.name, prompt)
