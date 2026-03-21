"""Reviewer agent -- validates and reviews generated content."""

import json
from typing import Any, Dict, List

from google.adk.agents import Agent

from ..formats import get_format
from ..tasks import REVIEW
from .base import BaseAgentService

_INSTRUCTION_BASE = """\
You are a strict content quality reviewer.

You receive generated content JSON and its format type.
Analyze the content and respond with ONLY a valid JSON object:

{{
  "valid": true,
  "score": 85,
  "errors": [],
  "warnings": ["minor issue"],
  "summary": "one-line overall assessment",
  "suggestions": ["specific improvement suggestion"]
}}

Check for:
- Required fields present and non-empty
- Data type correctness (strings, numbers, lists, dicts)
- Logical consistency (e.g. correct_answer index within options bounds)
- Content quality (engaging titles, non-trivial descriptions)
- Structural integrity (e.g. story nodes reference valid node IDs)

Scoring guide:
- 90-100: Excellent, ready to publish
- 70-89: Good, minor improvements possible
- 50-69: Acceptable, needs refinement
- Below 50: Poor, major issues

CRITICAL: Respond with valid JSON only. No markdown, no explanations outside the JSON."""

_INSTRUCTION_PIPELINE = _INSTRUCTION_BASE + """

Review the following content:
{draft_content}
"""

_INSTRUCTION_SERVICE = _INSTRUCTION_BASE + """

The content to review will be provided in the user message."""


def create_reviewer(
    instruction: str | None = None,
    *,
    model: str = "gemini-2.5-flash",
    output_key: str | None = "review_result",
) -> Agent:
    """Base factory -- accepts explicit instruction and output_key."""
    if instruction is None:
        instruction = _INSTRUCTION_PIPELINE
    return Agent(
        name="ReviewerAgent",
        model=model,
        instruction=instruction,
        description="Reviews and validates generated content for quality and correctness.",
        output_key=output_key,
        include_contents="none",
    )


def create_reviewer_pipeline(model: str = "gemini-2.5-flash") -> Agent:
    """Pipeline variant -- reads draft_content from session state."""
    return create_reviewer(
        _INSTRUCTION_PIPELINE, model=model, output_key="review_result",
    )


def create_reviewer_service(model: str = "gemini-2.5-flash") -> Agent:
    """Service variant -- receives content via user prompt, no output_key."""
    return create_reviewer(
        _INSTRUCTION_SERVICE, model=model, output_key=None,
    )


class ReviewerAgentService(BaseAgentService):
    """Reviews content quality and validates against schema."""

    def __init__(self):
        super().__init__()
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
        return f"Content type: {content_type}\n\nContent to review:\n{draft_str}"

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        try:
            agent = self._service_agents[0]
            runner = self._ensure_runner("reviewer", agent)
            result = await self._run(runner, "ReviewerAgent", prompt)
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


def schema_validate(
    content: Dict[str, Any],
    content_type: str,
) -> Dict[str, Any]:
    """Lightweight local schema validation (no LLM)."""
    errors: List[str] = []
    warnings: List[str] = []

    if not content:
        errors.append("Content is empty")
        return {
            "valid": False,
            "score": 0,
            "errors": errors,
            "warnings": warnings,
            "summary": "Empty content",
        }

    fmt = get_format(content_type)
    if fmt:
        try:
            fmt.model_class.model_validate(content)
        except Exception as exc:
            errors.append(f"Schema validation failed: {exc}")

    if content_type in ("quiz", "trivia", "test"):
        questions = content.get("questions", [])
        if not questions:
            errors.append("Quiz has no questions")
        for i, q in enumerate(questions):
            if isinstance(q, dict):
                opts = q.get("options", [])
                ca = q.get("correct_answer", 0)
                if isinstance(ca, int) and ca >= len(opts):
                    errors.append(
                        f"Question {i}: correct_answer index {ca} "
                        f"out of bounds (only {len(opts)} options)"
                    )

    if content_type in ("story", "narrative", "branched_narrative", "adventure"):
        nodes = content.get("nodes", {})
        if "start" not in nodes:
            errors.append("Story missing 'start' node")

    valid = len(errors) == 0
    score = 100 if valid else max(0, 100 - len(errors) * 20)
    return {
        "valid": valid,
        "score": score,
        "errors": errors,
        "warnings": warnings,
        "summary": "Schema validation passed" if valid else "Schema issues found",
    }
