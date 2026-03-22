"""Refiner agent -- iterative review/refine loop via ADK pipeline."""

import json
from typing import Any, Dict

from google.adk.agents import Agent

from ..tasks import REFINE
from ..utils.callbacks import adk_before_agent, adk_after_agent, adk_before_model
from ..workflows.refine import create_refinement_pipeline
from ..workflows.tools import exit_loop
from .base import BaseAgentService


_INSTRUCTION_BASE = """\
You are an expert content refiner.

You receive content JSON (draft), review feedback, and fact-check verification results.
Your task is to improve the content by applying ALL feedback.

PRIORITY ORDER:
1. Fix ALL factual errors flagged by the verification result FIRST.
   These are accuracy issues (wrong answers, incorrect facts, contradictions).
2. Fix structural errors listed in the review (schema, missing fields, broken refs).
3. Address consistency issues from verification (timeline, character, world-rule).
4. Apply EVERY warning and suggestion from the review — do not skip any.
5. Preserve the original JSON structure and all required fields.

MANDATORY FEEDBACK APPLICATION:
You MUST address EVERY error, warning, and suggestion from both review and
verification feedback. For each piece of feedback, reason about the best way
to incorporate it while maintaining content coherence, then apply the change.
Do not ignore suggestions even if they seem minor.

FORMAT-SPECIFIC REFINEMENT:
- QUIZ: If a fact is flagged as incorrect, replace it with the correct fact
  from the verification detail. Ensure explanations cite specific verifiable facts.
- SIMULATION: Express rules/equations using precise mathematical notation
  (e.g., "population = population * (1 + growth_rate)"). Generic prose like
  "population increases" is insufficient — convert to formulas.
- STORY/GAME: If a consistency issue is flagged, resolve it by updating the
  conflicting node/section. Ensure character names, timelines, and world rules
  are coherent across all branches.

RULES:
- Do NOT invent new facts; use the verification detail to guide corrections.
- Do NOT drop content — only modify or improve existing fields.
- If a suggestion asks for more specificity (e.g., "use math", "cite sources"),
  you MUST make the content more specific, not leave it vague.

DOMAIN AWARENESS:
- If domain is "realworld": When fixing factual errors, use verification details
  to substitute correct facts. Never invent replacements.
- If domain is "fictional": When fixing consistency issues, maintain creative
  freedom. Invented facts are acceptable as long as internally consistent.

CRITICAL: Output the refined content as valid JSON only. No markdown, no explanations."""

_PIPELINE_SUFFIX = """

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
        self._pipeline = create_refinement_pipeline(pipe, reviewer)
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
