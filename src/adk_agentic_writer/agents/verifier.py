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
from ..utils.callbacks import adk_before_agent, adk_after_agent, adk_before_model
from .base import BaseAgentService

logger = logging.getLogger(__name__)


_INSTRUCTION_BASE = """\
You are a rigorous fact-checker and consistency verifier for generated content.

You receive content JSON and its format type. Your job is to:

1. IDENTIFY verifiable claims in the content:
   - For quizzes: correct answers, explanations, factual statements in questions
   - For stories/narratives: historical, scientific, or cultural references;
     internal consistency of characters, timeline, and world rules
   - For games/RPGs: any real-world references; internal quest logic and
     node reachability; reward/requirement consistency
   - For simulations: scientific accuracy of variables, units, ranges,
     and described interactions

2. FACT-CHECK verifiable claims using Google Search.
   Search for specific queries to verify factual claims, e.g.:
   "What is the hardest natural substance?" or "When was the 96th Academy Awards?"

3. CHECK INTERNAL CONSISTENCY (no search needed):
   - Character names used consistently throughout
   - Timeline/sequence of events does not contradict
   - World rules established early are not violated later
   - Node/branch references point to existing elements
   - Variable ranges and units are physically plausible
   - For simulations: verify that rules/equations are dimensionally consistent
     (units on both sides match) and that variable references in rules match
     defined variable names. Flag prose rules that lack mathematical formulas.

4. Return a JSON report:
{
  "facts_checked": [
    {"claim": "...", "verdict": "correct|incorrect|unverifiable", "detail": "..."}
  ],
  "consistency_issues": ["..."],
  "errors": ["critical issues that must be fixed"],
  "warnings": ["minor concerns"],
  "confidence": "high|medium|low",
  "suggestions": ["specific improvements based on findings"]
}

RULES:
- Focus on ACCURACY over style (style is the reviewer's job).
- If search fails or returns ambiguous results, mark claim as "unverifiable"
  rather than guessing.
- Always check internal consistency regardless of content type.
- Every suggestion MUST be specific and actionable — name the exact field
  or claim that needs correction, and provide the correct information.

DOMAIN AWARENESS:
- If domain is "realworld": Rigorously fact-check ALL claims via Google Search.
  Every factual statement must be verified.
- If domain is "fictional": Do NOT fact-check fictional elements via search.
  Only check internal consistency (characters, timeline, world rules).
  However, if the content references REAL entities (real people, real places,
  real events), those references must still be accurate.
- DOMAIN MATCH CHECK: If the content appears to be entirely fictional but
  domain is "realworld", flag this as an error. Conversely, if content contains
  entirely real-world facts but domain is "fictional", note this as a warning.

CRITICAL: Respond with valid JSON only. No markdown, no explanations outside JSON."""

_PIPELINE_SUFFIX = """

Content to verify:
{draft_content}
"""

_SERVICE_SUFFIX = """

The content to verify will be provided in the user message."""

_INSTRUCTION_PIPELINE = _INSTRUCTION_BASE + _PIPELINE_SUFFIX
_INSTRUCTION_SERVICE = _INSTRUCTION_BASE + _SERVICE_SUFFIX


def create_verifier(
    instruction: str | None = None,
    *,
    model: str = "gemini-2.5-flash",
    output_key: str | None = "verification_result",
) -> Agent:
    """Factory -- google_search is the sole tool (ADK single-tool constraint)."""
    if instruction is None:
        instruction = _INSTRUCTION_PIPELINE
    return Agent(
        name="VerifierAgent",
        model=model,
        instruction=instruction,
        description="Fact-checks content accuracy and verifies internal consistency.",
        output_key=output_key,
        tools=[google_search],
        include_contents="none",
        before_agent_callback=adk_before_agent,
        after_agent_callback=adk_after_agent,
        before_model_callback=adk_before_model,
    )


def create_verifier_pipeline(model: str = "gemini-2.5-flash") -> Agent:
    """Pipeline variant -- reads draft_content from session state."""
    return create_verifier(
        _INSTRUCTION_PIPELINE, model=model, output_key="verification_result",
    )


def create_verifier_service(model: str = "gemini-2.5-flash") -> Agent:
    """Service variant -- no output_key; result returned explicitly."""
    return create_verifier(
        _INSTRUCTION_SERVICE, model=model, output_key=None,
    )


class VerifierAgentService(BaseAgentService):
    """Fact-checks content using Google Search and consistency analysis."""

    def __init__(self):
        super().__init__()
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
            runner = self._ensure_runner("verifier", agent)
            result = await self._run(runner, "VerifierAgent", prompt)
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
