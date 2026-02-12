"""Reusable ADK Agent wrapper with common JSON/response logic.

Provides ADKAgentWrapper that encapsulates:
- Lazy ADK agent/runner initialization
- Response text extraction from ADK events
- JSON parsing with markdown fence stripping
- Response validation with field-level warnings

Used by GeminiWriterAgent, GeminiCoordinatorAgent, and other ADK-based agents.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Set

from ...utils.log_config import log_llm_prompt, log_llm_response

logger = logging.getLogger(__name__)

# ADK imports (optional dependency)
try:
    from google.adk.agents import Agent
    from google.adk.runners import InMemoryRunner

    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False


class ADKAgentWrapper:
    """Wrapper for ADK Agent with InMemoryRunner.

    Handles:
    - Lazy initialization of ADK Agent + InMemoryRunner
    - Text extraction from various ADK response formats
    - JSON parsing with markdown code fence stripping
    - Response validation with configurable required/optional fields
    """

    def __init__(
        self,
        name: str,
        instruction: str,
        model_name: str = "gemini-2.5-flash-lite",
    ):
        if not ADK_AVAILABLE:
            raise RuntimeError("Google ADK not installed. Run: pip install google-adk")
        if not os.environ.get("GOOGLE_API_KEY"):
            raise RuntimeError("GOOGLE_API_KEY not set")

        self.name = name
        self.instruction = instruction
        self.model_name = model_name
        self._agent: Optional[Agent] = None
        self._runner: Optional[InMemoryRunner] = None

    async def _ensure_initialized(self) -> None:
        """Lazily initialize ADK Agent and InMemoryRunner."""
        if self._agent is not None:
            return
        self._agent = Agent(
            name=self.name, model=self.model_name, instruction=self.instruction
        )
        self._runner = InMemoryRunner(agent=self._agent)
        logger.info(f"Initialized ADK agent: {self.name}")

    async def run(
        self,
        prompt: str,
        required_fields: Optional[Set[str]] = None,
        optional_fields: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """Run agent and return parsed JSON response.

        Args:
            prompt: The prompt to send to the agent
            required_fields: Fields that must be present (warns if missing)
            optional_fields: Fields that are nice-to-have (debug log if missing)

        Returns:
            Parsed JSON dict from LLM response
        """
        await self._ensure_initialized()
        log_llm_prompt(logger, self.name, prompt)

        response = await self._runner.run_debug(prompt, quiet=True)
        text = self._extract_text(response)
        result = self._parse_json(text)

        log_llm_response(logger, self.name, result)

        if required_fields or optional_fields:
            self._validate_response(result, required_fields, optional_fields)

        return result

    # =========================================================================
    # Text Extraction
    # =========================================================================

    def _extract_text(self, response: Any) -> str:
        """Extract text from ADK response.

        Handles multiple response formats:
        - List of events with content.parts
        - Object with .text attribute
        - String representation fallback
        """
        if isinstance(response, list):
            texts = []
            for event in response:
                if hasattr(event, "content") and hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if hasattr(part, "text"):
                            texts.append(part.text)
            if texts:
                return "".join(texts)

        if hasattr(response, "text"):
            return response.text

        # Fallback: extract from string representation
        resp_str = str(response)
        match = re.search(r'text="""(.+?)"""', resp_str, re.DOTALL)
        if match:
            return match.group(1)
        return resp_str

    # =========================================================================
    # JSON Parsing
    # =========================================================================

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """Strip markdown code fences (```json ... ```)."""
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    @staticmethod
    def _fix_json_escapes(text: str) -> str:
        r"""Fix common LLM JSON escape issues.

        LLMs sometimes produce invalid escape sequences like \' or \" inside
        JSON strings that are already properly delimited with double quotes.
        This repairs them so json.loads() can succeed.
        """
        import re

        # Fix invalid \' (not valid in JSON)
        text = text.replace("\\'", "'")
        # Fix double-escaped quotes that create invalid sequences
        # e.g. \" inside a JSON string value that's already quoted
        # We do a targeted fix: replace \<invalid_char> with the char itself
        # Valid JSON escapes: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
        text = re.sub(r'\\(?!["\\/bfnrtu])', "", text)
        return text

    # Common refusal phrases LLMs use when declining a request
    _REFUSAL_PATTERNS = (
        "i cannot",
        "i can't",
        "i'm unable",
        "i am unable",
        "i'm not able",
        "i am not able",
        "i apologize",
        "i'm sorry",
        "i am sorry",
        "as an ai",
        "not appropriate",
        "cannot generate",
        "can't generate",
        "against my guidelines",
        "safety",
        "harmful",
        "offensive",
        "sensitive topic",
        "not comfortable",
    )

    def _detect_refusal(self, text: str) -> Optional[str]:
        """Detect if the LLM refused to generate content.

        Returns the refusal message (first 300 chars) if detected, else None.
        """
        lower = text.strip().lower()
        # If it starts with { it's likely JSON, not a refusal
        if lower.startswith("{") or lower.startswith("["):
            return None
        for pattern in self._REFUSAL_PATTERNS:
            if pattern in lower:
                return text.strip()[:300]
        return None

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response text.

        Strips markdown code fences before parsing.
        Progressively relaxes parsing strictness:
          1. Strict parse
          2. Fix invalid escape sequences
          3. Allow control characters (strict=False)
        Detects LLM refusals and raises ValueError with the refusal reason.
        Raises ValueError with truncated raw text if all attempts fail.
        """
        # Check for LLM refusal before attempting JSON parse
        refusal = self._detect_refusal(text)
        if refusal:
            logger.warning(f"[{self.name}] LLM refused request: {refusal}")
            raise ValueError(f"LLM refused to generate content: {refusal}")

        cleaned = self._strip_code_fences(text)

        # Attempt 1: strict parse
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Attempt 2: fix invalid escape sequences
        fixed = self._fix_json_escapes(cleaned)
        try:
            result = json.loads(fixed)
            logger.warning(
                f"[{self.name}] JSON required escape repair -- "
                "LLM produced invalid escape sequences"
            )
            return result
        except json.JSONDecodeError:
            pass

        # Attempt 3: allow control characters (LLM sometimes puts
        # raw newlines/tabs inside JSON string values)
        try:
            result = json.loads(fixed, strict=False)
            logger.warning(
                f"[{self.name}] JSON required strict=False -- "
                "LLM produced control characters in strings"
            )
            return result
        except json.JSONDecodeError as e:
            logger.error(
                f"[{self.name}] JSON parse failed: {e}\n"
                f"Raw text (first 500 chars): {text[:500]}"
            )
            raise ValueError(f"Invalid JSON from {self.name}: {e}\nRaw: {text[:500]}")

    # =========================================================================
    # Response Validation
    # =========================================================================

    def _validate_response(
        self,
        result: Dict[str, Any],
        required_fields: Optional[Set[str]] = None,
        optional_fields: Optional[Set[str]] = None,
    ) -> None:
        """Validate LLM response has expected fields, logging warnings.

        Args:
            result: Parsed JSON dict
            required_fields: Fields that should be present (WARNING level)
            optional_fields: Fields that are nice-to-have (DEBUG level)
        """
        if required_fields:
            missing = required_fields - set(result.keys())
            if missing:
                logger.warning(
                    f"[{self.name}] LLM response missing required fields: {missing}. "
                    f"Present fields: {set(result.keys())}"
                )

        if optional_fields:
            missing_opt = optional_fields - set(result.keys())
            if missing_opt:
                logger.debug(
                    f"[{self.name}] LLM response missing optional fields: {missing_opt}"
                )


__all__ = ["ADKAgentWrapper", "ADK_AVAILABLE"]
