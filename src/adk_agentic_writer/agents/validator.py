"""Pure ADK validator agent for content quality checks.

Uses google.adk.agents.Agent + InMemoryRunner directly.
Combines LLM-based quality assessment with lightweight schema validation.
"""

import json
import logging
import os
from typing import Any, Dict, List

from ..utils.proxy_utils import clear_proxy_env

clear_proxy_env()

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

from ..teams.editorial_team import CONTENT_VALIDATOR
from ..utils.content_registry import CONTENT_REGISTRY
from ..utils.log_config import log_llm_prompt, log_llm_response
from .adk_utils import extract_text, parse_json

logger = logging.getLogger(__name__)

_VALIDATOR_INSTRUCTION = """\
You are a strict content quality validator.

When given content JSON and its content type, you MUST respond with a JSON object:
{
  "valid": true/false,
  "score": 0-100,
  "errors": ["critical issue 1", ...],
  "warnings": ["minor issue 1", ...],
  "summary": "one-line overall assessment"
}

Check for:
- Required fields present and non-empty
- Data type correctness (strings, numbers, lists, dicts)
- Logical consistency (e.g. correct_answer index within options bounds)
- Content quality (engaging titles, non-trivial descriptions)
- Structural integrity (e.g. story nodes reference valid node IDs)

CRITICAL: Respond with valid JSON only. No markdown, no explanations outside the JSON.
"""


class ValidatorAgent:
    """ADK-powered content validator.

    Uses an LLM Agent for quality assessment.
    Falls back to local schema checks if the LLM call fails.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash-lite"):
        if not os.environ.get("GOOGLE_API_KEY"):
            raise RuntimeError("GOOGLE_API_KEY not set")

        self._model_name = model_name
        self._agent: Agent | None = None
        self._runner: InMemoryRunner | None = None
        logger.info("ValidatorAgent initialized (model=%s)", model_name)

    def _ensure_agent(self) -> InMemoryRunner:
        """Lazily create the ADK validator agent."""
        if self._runner is not None:
            return self._runner

        self._agent = Agent(
            name="content_validator",
            model=self._model_name,
            description="Validates generated content for quality and correctness.",
            instruction=_VALIDATOR_INSTRUCTION,
        )
        self._runner = InMemoryRunner(agent=self._agent)
        logger.info("Created ADK agent: content_validator")
        return self._runner

    async def validate(
        self,
        content: Dict[str, Any],
        content_type: str = "unknown",
    ) -> Dict[str, Any]:
        """Validate content and return a validation report.

        Returns dict with keys: valid, score, errors, warnings, summary.
        Falls back to local schema checks on LLM failure.
        """
        try:
            return await self._llm_validate(content, content_type)
        except Exception as exc:
            logger.warning(
                "LLM validation failed (%s), falling back to schema checks: %s",
                content_type, exc,
            )
            return self._schema_validate(content, content_type)

    async def _llm_validate(
        self,
        content: Dict[str, Any],
        content_type: str,
    ) -> Dict[str, Any]:
        """Run LLM-based validation."""
        runner = self._ensure_agent()
        content_json = json.dumps(content, indent=2, ensure_ascii=False)

        type_config = CONTENT_REGISTRY.get(content_type)
        schema_hint = ""
        if type_config and type_config.schema_description:
            schema_hint = f"\n\nExpected schema:\n{type_config.schema_description}"

        prompt = (
            f"Validate the following {content_type} content.{schema_hint}\n\n"
            f"Content to validate:\n{content_json}"
        )

        log_llm_prompt(logger, "content_validator", prompt)

        response = await runner.run_debug(prompt, quiet=True)
        text = extract_text(response)
        result = parse_json(text, agent_name="content_validator")

        log_llm_response(logger, "content_validator", result)

        result.setdefault("valid", len(result.get("errors", [])) == 0)
        result.setdefault("score", 100 if result["valid"] else 50)
        result.setdefault("errors", [])
        result.setdefault("warnings", [])
        result.setdefault("summary", "Validation complete")
        return result

    @staticmethod
    def _schema_validate(
        content: Dict[str, Any],
        content_type: str,
    ) -> Dict[str, Any]:
        """Lightweight local schema validation (no LLM)."""
        errors: List[str] = []
        warnings: List[str] = []

        if not content:
            errors.append("Content is empty")
            return {
                "valid": False, "score": 0,
                "errors": errors, "warnings": warnings,
                "summary": "Empty content",
            }

        type_config = CONTENT_REGISTRY.get(content_type)
        if type_config:
            model_cls = type_config.model_class
            try:
                model_cls.model_validate(content)
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


__all__ = ["ValidatorAgent"]
