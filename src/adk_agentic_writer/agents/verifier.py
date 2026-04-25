"""Verifier agent -- fact-checks content using Google Search via ADK.

Uses google_search directly as the VerifierAgent's sole tool (ADK requires
google_search to be the only tool on an agent). The agent does fact-checking
via search and consistency analysis via LLM reasoning. Produces a
verification_result with fact-check findings, issues, and suggestions.
"""

import json
import logging
from typing import Any, Dict

from google.adk.agents import Agent
from google.adk.tools import google_search

from ..tasks import VERIFY
from ..utils.callbacks import adk_before_agent, adk_after_agent, adk_before_model, adk_after_model
from .base import BaseAgentService
from .model_config import get_generate_content_config, get_model

logger = logging.getLogger(__name__)


_INSTRUCTION_BASE = """\
You are a fact-checker and consistency verifier for generated content.

You receive content JSON and its format type. Your job:

1. CHECK INTERNAL CONSISTENCY (no search needed):
   - Quizzes: total_score == sum of per-question scores; correct_answer indices valid
   - Stories/games: node/branch references exist; no dead-end links
   - Simulations: rule variable names match defined variables; units plausible
   - Character names, timeline, world rules self-consistent

2. FACT-CHECK the TOP 5 most critical/dubious claims via Google Search.
   Prioritize claims that, if wrong, would make the content misleading.
   Skip obvious/trivial facts. Keep each search query focused.

3. Return a CONCISE JSON report:
{
  "facts_checked": [
    {"claim": "...", "verdict": "correct|incorrect|unverifiable", "detail": "1-2 sentences max"}
  ],
  "consistency_issues": ["short description"],
  "errors": ["critical issues only"],
  "warnings": ["minor concerns"],
  "confidence": "high|medium|low",
  "suggestions": ["specific fix, naming the exact field"]
}

BREVITY RULES:
- facts_checked: MAX 5 entries. Only the most important claims.
- claim: Quote or paraphrase in ONE short sentence.
- detail: ONE sentence with the key evidence or source.
- consistency_issues / errors / warnings: ONE sentence each.
- suggestions: MAX 3 entries. Name the field and the fix.
- Total JSON output MUST stay under 1500 tokens.

DOMAIN AWARENESS:
- "realworld": fact-check top 5 claims via search.
- "fictional": skip search for fictional elements; only check internal
  consistency and verify any real-world references.

CRITICAL: Respond with valid JSON only. No markdown, no explanations outside JSON."""

_PIPELINE_SUFFIX = """

Ideation context (format, domain, creative direction):
{ideation_result}

Content to verify:
{draft_content}
"""

_SERVICE_SUFFIX = """

The content to verify will be provided in the user message.

SESSION CONTEXT (multi-turn conversations):
You may be operating inside a session with previous verifications visible. If you
previously verified an earlier version, note which factual errors were corrected,
which persist, and flag any new claims that need checking. Avoid re-searching facts
you already confirmed as correct in a prior round."""

_INSTRUCTION_PIPELINE = _INSTRUCTION_BASE + _PIPELINE_SUFFIX
_INSTRUCTION_SERVICE = _INSTRUCTION_BASE + _SERVICE_SUFFIX


def create_verifier(
    instruction: str | None = None,
    *,
    model: str | None = None,
    output_key: str | None = "verification_result",
    include_contents: str = "none",
) -> Agent:
    """Factory -- google_search is the sole tool (ADK single-tool constraint)."""
    if instruction is None:
        instruction = _INSTRUCTION_PIPELINE
    model = model or get_model("verifier")
    return Agent(
        name="VerifierAgent",
        model=model,
        instruction=instruction,
        description="Fact-checks content accuracy and verifies internal consistency.",
        output_key=output_key,
        tools=[google_search],
        include_contents=include_contents,
        generate_content_config=get_generate_content_config("verifier"),
        before_agent_callback=adk_before_agent,
        after_agent_callback=adk_after_agent,
        before_model_callback=adk_before_model,
        after_model_callback=adk_after_model,
    )


def create_verifier_pipeline(model: str | None = None) -> Agent:
    """Pipeline variant -- reads draft_content from session state."""
    return create_verifier(
        _INSTRUCTION_PIPELINE, model=model, output_key="verification_result",
    )


def create_verifier_service(model: str | None = None) -> Agent:
    """Service variant -- includes session history for context."""
    return create_verifier(
        _INSTRUCTION_SERVICE, model=model, output_key=None,
        include_contents="default",
    )


class VerifierAgentService(BaseAgentService):
    """Fact-checks content using Google Search and consistency analysis."""

    def __init__(self, session_service=None):
        super().__init__(session_service=session_service)
        self._register_tasks([VERIFY])
        self._pipeline_agents.append(create_verifier_pipeline())
        self._service_agents.append(create_verifier_service())

    def prepare_task(
        self,
        task_id: str,
        params: Dict[str, Any],
    ) -> str:
        draft = params.get("draft_content", {})
        content_type = params.get("format", "unknown")
        if isinstance(draft, dict):
            draft_str = json.dumps(draft, indent=2, ensure_ascii=False)
        else:
            draft_str = str(draft)
        domain = params.get("domain", "realworld")
        return (
            f"Content type: {content_type}\n\n"
            f"Content to verify:\n{draft_str}\n\n"
            f"DOMAIN: {domain}"
        )

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        try:
            agent = self._service_agents[0]
            result = await self._run_agent("verifier", agent, "VerifierAgent", prompt)
            result.setdefault("facts_checked", [])
            result.setdefault("consistency_issues", [])
            result.setdefault("errors", [])
            result.setdefault("warnings", [])
            result.setdefault("confidence", "medium")
            result.setdefault("suggestions", [])
            return result
        except Exception:
            logger.exception("VerifierAgent failed")
            return {
                "facts_checked": [],
                "consistency_issues": [],
                "errors": [],
                "warnings": ["Verification unavailable -- search may have failed"],
                "confidence": "low",
                "suggestions": [],
            }
