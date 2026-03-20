"""Refiner agent -- iterative review/refine loop via ADK pipeline."""

import json
from typing import Any, Dict

from google.adk.agents import Agent

from ..tasks import REFINE
from ..workflows.refine import create_refinement_pipeline
from .base import BaseAgentService, MODEL


_INSTRUCTION_WITH_EXIT = """\
You are an expert content refiner.

You receive content JSON (draft) and review feedback.
Your task is to improve the content OR signal completion.

**Current Content:**
{draft_content}

**Review Feedback:**
{review_result}

TASK:
- If the review indicates the content is excellent (score >= 90, no errors):
  You MUST call the 'exit_loop' function. Do not output any text.
- Otherwise:
  1. Fix all errors from the review.
  2. Address warnings where possible.
  3. Apply suggestions to improve quality.
  4. Output the refined content as valid JSON only.

OUTPUT: Either call exit_loop OR output refined JSON. Nothing else.
"""


def create_refiner(exit_loop_tool, model: str = MODEL) -> Agent:
    """Factory for a loop-aware refiner that can call exit_loop."""
    return Agent(
        name="RefinerAgent",
        model=model,
        instruction=_INSTRUCTION_WITH_EXIT,
        description="Refines content or exits the loop when quality is sufficient.",
        output_key="draft_content",
        include_contents="none",
        tools=[exit_loop_tool],
    )


class RefinerAgentService(BaseAgentService):
    """Runs an iterative Reviewer <-> Refiner loop pipeline.

    Accepts pre-built ADK reviewer and refiner agents and composes
    them into a LoopAgent via create_refinement_pipeline.
    """

    def __init__(self, reviewer: Agent, refiner: Agent, model: str = MODEL):
        super().__init__(model=model)
        self._register_tasks([REFINE])
        self._pipeline = create_refinement_pipeline(reviewer, refiner)

    def prepare_task(
        self,
        task_id: str,
        params: Dict[str, Any],
    ) -> str:
        draft = params.get("draft_content", {})
        if isinstance(draft, dict):
            draft_str = json.dumps(draft, indent=2, ensure_ascii=False)
        else:
            draft_str = str(draft)
        return f"Content to refine:\n{draft_str}"

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        runner = self._ensure_runner("refiner", self._pipeline)
        return await self._run(runner, "RefinementLoop", prompt)
