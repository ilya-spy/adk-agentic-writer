"""Refiner agent -- improves content based on review feedback."""

import json
from typing import Any, Dict

from google.adk.agents import Agent

from ..tasks import REFINE
from .base import BaseAgentService, MODEL

_INSTRUCTION = """\
You are an expert content refiner.

You receive content JSON (draft) and review feedback.
Your task is to improve the content based on the review.

**Current Content:**
{draft_content}

**Review Feedback:**
{review_result}

TASK:
1. Read every error and warning from the review.
2. Fix all errors -- these are critical.
3. Address warnings where possible.
4. Apply suggestions to improve quality.
5. Maintain the same JSON schema structure.
6. Keep the content engaging and creative.

OUTPUT: The refined content as valid JSON only.
Same schema as the input, but improved.
No markdown, no explanations -- just the JSON object.
"""

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


def create_refiner(model: str = MODEL) -> Agent:
    """Standalone factory kept for workflow composition."""
    return Agent(
        name="RefinerAgent",
        model=model,
        instruction=_INSTRUCTION,
        description="Refines and improves content based on review feedback.",
        output_key="draft_content",
        include_contents="none",
    )


def create_loop_refiner(exit_loop_tool, model: str = MODEL) -> Agent:
    return Agent(
        name="RefinerAgent",
        model=model,
        instruction=_INSTRUCTION_WITH_EXIT,
        description="Refines content or exits the loop when quality is sufficient.",
        output_key="draft_content",
        include_contents="none",
        tools=[exit_loop_tool],
    )


class RefinerAgent(BaseAgentService):
    """Refines content based on review feedback."""

    def __init__(self, model: str = MODEL):
        super().__init__(model=model)
        self._register_tasks([REFINE])
        self._agent = create_refiner(model)

    async def process_task(
        self, task_id: str, params: Dict[str, Any],
    ) -> Dict[str, Any]:
        draft = params.get("draft_content", {})
        review = params.get("review_result", {})
        if isinstance(draft, dict):
            draft_str = json.dumps(draft, indent=2, ensure_ascii=False)
        else:
            draft_str = str(draft)
        if isinstance(review, dict):
            review_str = json.dumps(review, indent=2, ensure_ascii=False)
        else:
            review_str = str(review)

        prompt = (
            f"Content to refine:\n{draft_str}\n\n"
            f"Review feedback:\n{review_str}"
        )
        runner = self._ensure_runner("refiner", self._agent)
        return await self._run(runner, "RefinerAgent", prompt)
