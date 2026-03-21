"""Refiner agent -- iterative review/refine loop via ADK pipeline."""

import json
from typing import Any, Dict

from google.adk.agents import Agent

from ..tasks import REFINE
from ..workflows.refine import create_refinement_pipeline
from ..workflows.tools import exit_loop
from .base import BaseAgentService


_INSTRUCTION_PIPELINE = """\
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

_INSTRUCTION_SERVICE = """\
You are an expert content refiner.

You receive content JSON (draft) and review feedback in the user message.
Your task is to improve the content based on the review.

RULES:
1. Fix all errors listed in the review.
2. Address warnings where possible.
3. Apply suggestions to improve quality.
4. Preserve the original JSON structure and all required fields.

CRITICAL: Output the refined content as valid JSON only. No markdown, no explanations."""


def create_refiner(
    instruction: str | None = None,
    *,
    model: str = "gemini-2.5-flash",
    output_key: str | None = "draft_content",
    tools: list | None = None,
) -> Agent:
    """Base factory -- accepts explicit instruction, output_key, and tools."""
    if instruction is None:
        instruction = _INSTRUCTION_PIPELINE
    return Agent(
        name="RefinerAgent",
        model=model,
        instruction=instruction,
        description="Refines content or exits the loop when quality is sufficient.",
        output_key=output_key,
        include_contents="none",
        tools=tools or [],
    )


def create_refiner_pipeline(
    exit_loop_tool, model: str = "gemini-2.5-flash",
) -> Agent:
    """Pipeline variant -- loop-aware with exit_loop tool and output_key."""
    return create_refiner(
        _INSTRUCTION_PIPELINE,
        model=model,
        output_key="draft_content",
        tools=[exit_loop_tool],
    )


def create_refiner_service(model: str = "gemini-2.5-flash") -> Agent:
    """Service variant -- no output_key, no tools; result returned explicitly."""
    return create_refiner(
        _INSTRUCTION_SERVICE, model=model, output_key=None, tools=None,
    )


class RefinerAgentService(BaseAgentService):
    """Refines content based on review feedback.

    Creates its own refiner ADK agents internally.
    Receives the reviewer ADK agent to compose the loop pipeline
    (used by publisher); service calls use a standalone agent.
    """

    def __init__(self, reviewer: Agent):
        super().__init__()
        self._register_tasks([REFINE])
        pipe = create_refiner_pipeline(exit_loop)
        self._pipeline_agents.append(pipe)
        self._pipeline = create_refinement_pipeline(reviewer, pipe)
        self._service_agents.append(create_refiner_service())

    def prepare_task(
        self,
        task_id: str,
        params: Dict[str, Any],
    ) -> str:
        draft = params.get("draft_content", {})
        review = params.get("review_result", {})
        fmt = params.get("format", "")
        if isinstance(draft, dict):
            draft_str = json.dumps(draft, indent=2, ensure_ascii=False)
        else:
            draft_str = str(draft)
        if isinstance(review, dict):
            review_str = json.dumps(review, indent=2, ensure_ascii=False)
        else:
            review_str = str(review)
        parts = [f"DRAFT CONTENT:\n{draft_str}", f"REVIEW FEEDBACK:\n{review_str}"]
        if fmt:
            parts.append(f"Content format: {fmt}")
        parts.append("Refine the draft based on the review feedback above.")
        return "\n\n".join(parts)

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        agent = self._service_agents[0]
        runner = self._ensure_runner("refiner_svc", agent)
        return await self._run(runner, "RefinerAgent", prompt)
