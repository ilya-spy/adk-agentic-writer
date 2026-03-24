"""Refiner agent -- iterative review/refine loop via ADK pipeline."""

import json
from typing import Any, Dict

from google.adk.agents import Agent

from ..tasks import REFINE
from ..utils.callbacks import adk_before_agent, adk_after_agent, adk_before_model, adk_after_model
from ..workflows.tools import exit_loop
from .base import BaseAgentService


_INSTRUCTION_BASE = """\
You are an expert content refiner that makes MINIMAL, SURGICAL changes.

You receive content JSON (draft), review feedback, and fact-check verification results.
Your goal is to fix ONLY the specific issues flagged, while preserving everything else verbatim.

CONSERVATIVE APPROACH (most important):
- Make the MINIMUM changes necessary to address each flagged issue.
- Do NOT rewrite content that was not flagged — preserve working text verbatim.
- Do NOT rephrase, reorganize, or "improve" sections that have no errors or warnings.
- Each change should be surgical: fix the specific problem without altering surrounding content.
- When in doubt, make FEWER changes rather than more.

PRIORITY ORDER:
1. Fix factual errors flagged by the verification result FIRST.
2. Fix structural errors listed in the review (schema, missing fields, broken refs).
3. Address consistency issues from verification (timeline, character, world-rule).
4. Address high-severity warnings only — skip minor stylistic suggestions.
5. Preserve the original JSON structure and all required fields.

FORMAT-SPECIFIC REFINEMENT:
- QUIZ: Replace incorrect facts with correct ones from verification detail.
- SIMULATION: If rules use vague prose, convert to arithmetic formulas.
- STORY/GAME: Fix flagged consistency issues in the conflicting node only.

RULES:
- Do NOT invent new facts; use the verification detail to guide corrections.
- Do NOT drop content — only modify or improve existing fields.

DOMAIN AWARENESS:
- If domain is "realworld": use the verification detail section to find correct facts
  and substitute them precisely. Trust the verifier's citations over your own knowledge.
- If domain is "fictional": maintain creative freedom if internally consistent.

CRITICAL: Output the refined content as valid JSON only. No markdown, no explanations."""

_PIPELINE_SUFFIX = """

**Ideation Context (format, domain, creative direction):**
{ideation_result}

**Current Content:**
{draft_content}

**Review Feedback:**
{review_result}

**Verification Result:**
{verification_result}

ADDITIONAL RULE:
- If the review indicates the content is excellent (score >= 90, no errors)
  AND verification found no factual errors or consistency issues:
  You MUST call the 'exit_loop' function. Do not output any text.
- Otherwise output refined JSON."""

_SERVICE_SUFFIX = """

The draft content, review feedback, and verification results will be provided
in the user message."""

_INSTRUCTION_PIPELINE = _INSTRUCTION_BASE + _PIPELINE_SUFFIX
_INSTRUCTION_SERVICE = _INSTRUCTION_BASE + _SERVICE_SUFFIX


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
        before_agent_callback=adk_before_agent,
        after_agent_callback=adk_after_agent,
        before_model_callback=adk_before_model,
        after_model_callback=adk_after_model,
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
    The pipeline agent (with exit_loop) is available for extraction
    by the publisher; service calls use a standalone agent.
    """

    def __init__(self):
        super().__init__()
        self._register_tasks([REFINE])
        self._pipeline_agents.append(create_refiner_pipeline(exit_loop))
        self._service_agents.append(create_refiner_service())

    def prepare_task(
        self,
        task_id: str,
        params: Dict[str, Any],
    ) -> str:
        draft = params.get("draft_content", {})
        review = params.get("review_result", {})
        verification = params.get("verification_result", {})
        fmt = params.get("format", "")

        draft_str = json.dumps(draft, indent=2, ensure_ascii=False) if isinstance(draft, dict) else str(draft)
        review_str = json.dumps(review, indent=2, ensure_ascii=False) if isinstance(review, dict) else str(review)
        verif_str = json.dumps(verification, indent=2, ensure_ascii=False) if isinstance(verification, dict) else str(verification)

        domain = params.get("domain", "realworld")
        parts = [
            f"DRAFT CONTENT:\n{draft_str}",
            f"REVIEW FEEDBACK:\n{review_str}",
            f"VERIFICATION RESULT:\n{verif_str}",
        ]
        if fmt:
            parts.append(f"CONTENT FORMAT: {fmt}")
        parts.append(f"DOMAIN: {domain}")
        return "\n\n".join(parts)

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        agent = self._service_agents[0]
        runner = self._ensure_runner("refiner_svc", agent)
        return await self._run(runner, "RefinerAgent", prompt)
