"""Reviewer agent -- validates and reviews generated content.

Creates a native ADK LlmAgent that reads draft_content from session
state, validates it against the format schema, and produces a
structured review result.
"""

import json
from typing import Any, Dict, List

from google.adk.agents import Agent

from ..formats import get_format

MODEL = "gemini-2.5-flash"

_INSTRUCTION = """\
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

CRITICAL: Respond with valid JSON only. No markdown, no explanations outside the JSON.

Review the following content:
{draft_content}
"""


def create_reviewer(model: str = MODEL) -> Agent:
    return Agent(
        name="ReviewerAgent",
        model=model,
        instruction=_INSTRUCTION,
        description="Reviews and validates generated content for quality and correctness.",
        output_key="review_result",
        include_contents="none",
    )


def schema_validate(
    content: Dict[str, Any],
    content_type: str,
) -> Dict[str, Any]:
    """Lightweight local schema validation (no LLM).

    Kept as a standalone utility for fast fallback validation.
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not content:
        errors.append("Content is empty")
        return {
            "valid": False, "score": 0,
            "errors": errors, "warnings": warnings,
            "summary": "Empty content",
        }

    fmt = get_format(content_type)
    if fmt:
        try:
            fmt.model_class.model_validate(content)
        except Exception as exc:
            errors.append(f"Schema validation failed: {exc}")

    if content_type == "quiz":
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

    if content_type in ("story", "branched_narrative"):
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
