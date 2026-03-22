"""Publisher agent -- full ideate-write-review/refine pipeline via ADK."""

import logging
from typing import Any, Dict, List

from google.adk.agents import Agent

from ..tasks import PUBLISH
from ..workflows.publish import create_publish_pipeline
from .base import BaseAgentService

logger = logging.getLogger(__name__)


def _writers_by_format(writers: List[Agent]) -> Dict[str, Agent]:
    """Derive format->agent mapping from agent names (e.g. QuizWriter -> quiz)."""
    return {
        agent.name.replace("Writer", "").lower(): agent
        for agent in writers
    }


class PublisherAgentService(BaseAgentService):
    """Runs the full publish pipeline as an ADK SequentialAgent.

    Receives pre-built ADK agents to compose per-format pipelines.
    """

    def __init__(
        self,
        ideator: Agent,
        writers: List[Agent],
        reviewer: Agent,
        refiner: Agent,
        verifier: Agent,
    ):
        super().__init__()
        self._register_tasks([PUBLISH])
        self._ideator = ideator
        self._writers = _writers_by_format(writers)
        self._reviewer = reviewer
        self._refiner = refiner
        self._verifier = verifier
        self._pipelines: Dict[str, Any] = {}
        self._pipeline_agents.extend(
            [ideator, reviewer, refiner, verifier, *writers]
        )

    def _get_pipeline(self, fmt_name: str):
        if fmt_name not in self._pipelines:
            writer = self._writers.get(
                fmt_name, next(iter(self._writers.values())),
            )
            self._pipelines[fmt_name] = create_publish_pipeline(
                self._ideator, writer, self._reviewer,
                self._refiner, self._verifier,
            )
        return self._pipelines[fmt_name]

    def prepare_task(
        self, task_id: str, params: Dict[str, Any],
    ) -> str:
        formats = params.get("formats", [])
        prompt = params.get("prompt", "")
        fmt_name = formats[0] if formats else "quiz"
        self._last_fmt_name = fmt_name
        if formats:
            prompt += f"\n\nREQUESTED FORMATS: {', '.join(formats)}"
        if not prompt.strip():
            prompt = f"Create {fmt_name} content"
        return prompt

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        fmt_name = getattr(self, "_last_fmt_name", "quiz")
        pipeline = self._get_pipeline(fmt_name)
        runner = self._ensure_runner(f"publish_{fmt_name}", pipeline)
        return await self._run(runner, pipeline.name, prompt)
