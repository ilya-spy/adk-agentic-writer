"""Reviewer agent -- validates and reviews generated content."""

import json
from typing import Any, Dict

from google.adk.agents import Agent

from ..tasks import REVIEW
from ..utils.callbacks import adk_before_agent, adk_after_agent, adk_before_model, adk_after_model
from ..utils.validator import schema_validate
from .base import BaseAgentService
from .model_config import get_generate_content_config, get_model

_INSTRUCTION_BASE = """\
You are a strict content quality reviewer.

You receive generated content JSON and its format type.
Analyze the content and respond with ONLY a valid JSON object:

{
  "valid": true,
  "score": 85,
  "errors": [],
  "warnings": ["minor issue"],
  "summary": "one-line overall assessment",
  "suggestions": ["specific improvement suggestion"]
}

STRUCTURAL checks (all formats):
- Required fields present and non-empty
- Data type correctness (strings, numbers, lists, dicts)
- Logical consistency (e.g. correct_answer index within options bounds)
- Content quality (clear, topic-appropriate titles; non-trivial descriptions)

NARRATIVE CONSISTENCY checks (story, game, narrative formats):
- Character names are spelled consistently throughout all nodes
- Timeline and sequence of events do not contradict across branches
- World rules established in early nodes are not violated in later ones
- Tone and voice remain consistent across the narrative
- Choices offered to the player/reader are meaningfully distinct

STRUCTURAL INTEGRITY checks (story, game formats):
- All branch next_node_id values reference existing nodes
- No orphaned nodes unreachable from the start node
- At least 2 ending nodes exist (is_ending=true)
- Quest/game rewards and requirements are balanced and achievable
- Victory conditions are logically reachable

QUIZ-SPECIFIC checks:
- correct_answer index is within options bounds for every question
- Each tier (low/mid/high) is represented with correct score mapping
- total_score is present and equals the sum of all question score values
- passing_score is 60-80% of total points
- Explanations should cite specific verifiable facts, not vague claims

SIMULATION-SPECIFIC checks:
- Variable ranges have sensible units and bounds
- Controls reference existing variables
- Rules MUST express variable relationships using mathematical formulas or
  equations (e.g., "GDP = GDP * (1 + growth_rate)"), not vague prose.
  Flag any rule that lacks a formula as an error.
- Equations are dimensionally consistent (units match on both sides)

Scoring guide:
- 90-100: Excellent, ready to publish
- 70-89: Good, minor improvements possible
- 50-69: Acceptable, needs refinement
- Below 50: Poor, major issues

TONE APPROPRIATENESS:
Flag content whose tone clashes with the subject matter (e.g., cheerful language
for a somber topic, or overly grim treatment of a lighthearted subject). Tone
should be derived from the topic, not imposed by default.

SUGGESTION QUALITY:
Every suggestion MUST be specific and actionable — name the exact field, value,
or text that should change, and describe how to fix it. Vague suggestions like
"improve quality" are not acceptable; instead say e.g. "question 3 explanation
should cite the specific treaty name and date".

NOTE: Factual accuracy is handled by a separate verifier agent.
Focus on structure, tone, consistency, and quality.

DOMAIN AWARENESS:
- If domain is "realworld": Penalize vague or unverifiable claims. Expect specific
  dates, names, sources. Flag any claim that sounds made up.
- If domain is "fictional": Do not penalize fictional elements. Focus on internal
  consistency and creative quality instead.

CRITICAL: Respond with valid JSON only. No markdown, no explanations outside the JSON."""

_INSTRUCTION_PIPELINE = _INSTRUCTION_BASE + """

Ideation context (format, domain, creative direction):
{ideation_result}

Review the following content:
{draft_content}
"""

_INSTRUCTION_SERVICE = _INSTRUCTION_BASE + """

The content to review will be provided in the user message."""


def create_reviewer(
    instruction: str | None = None,
    *,
    model: str | None = None,
    output_key: str | None = "review_result",
    include_contents: str = "none",
) -> Agent:
    """Base factory -- accepts explicit instruction and output_key."""
    if instruction is None:
        instruction = _INSTRUCTION_PIPELINE
    model = model or get_model("reviewer")
    return Agent(
        name="ReviewerAgent",
        model=model,
        instruction=instruction,
        description="Reviews and validates generated content for quality and correctness.",
        output_key=output_key,
        include_contents=include_contents,
        generate_content_config=get_generate_content_config("reviewer"),
        before_agent_callback=adk_before_agent,
        after_agent_callback=adk_after_agent,
        before_model_callback=adk_before_model,
        after_model_callback=adk_after_model,
    )


def create_reviewer_pipeline(model: str | None = None) -> Agent:
    """Pipeline variant -- reads draft_content from session state."""
    return create_reviewer(
        _INSTRUCTION_PIPELINE, model=model, output_key="review_result",
    )


def create_reviewer_service(model: str | None = None) -> Agent:
    """Service variant -- includes session history for context."""
    return create_reviewer(
        _INSTRUCTION_SERVICE, model=model, output_key=None,
        include_contents="default",
    )


class ReviewerAgentService(BaseAgentService):
    """Reviews content quality and validates against schema."""

    def __init__(self, session_service=None):
        super().__init__(session_service=session_service)
        self._register_tasks([REVIEW])
        self._pipeline_agents.append(create_reviewer_pipeline())
        self._service_agents.append(create_reviewer_service())

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
        self._last_draft = draft
        self._last_content_type = content_type
        domain = params.get("domain", "realworld")
        return (
            f"Content type: {content_type}\n\n"
            f"Content to review:\n{draft_str}\n\n"
            f"DOMAIN: {domain}"
        )

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        try:
            agent = self._service_agents[0]
            result = await self._run_agent("reviewer", agent, "ReviewerAgent", prompt)
            result.setdefault("valid", len(result.get("errors", [])) == 0)
            result.setdefault("score", 100 if result["valid"] else 50)
            result.setdefault("errors", [])
            result.setdefault("warnings", [])
            result.setdefault("summary", "Review complete")
            return result
        except Exception:
            draft = getattr(self, "_last_draft", {})
            ct = getattr(self, "_last_content_type", "unknown")
            return schema_validate(draft if isinstance(draft, dict) else {}, ct)
