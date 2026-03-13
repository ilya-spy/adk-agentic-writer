"""Shared ADK response utilities.

Provides helpers for:
- Text extraction from ADK runner responses
- JSON parsing with progressive fallbacks
- LLM refusal detection
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text(response: Any) -> str:
    """Extract text from an ADK runner response.

    Handles list-of-events, object-with-.text, and string fallback.
    """
    if isinstance(response, list):
        texts: List[str] = []
        for event in response:
            if hasattr(event, "content") and hasattr(event.content, "parts"):
                for part in event.content.parts:
                    if hasattr(part, "text"):
                        texts.append(part.text)
        if texts:
            return "".join(texts)

    if hasattr(response, "text"):
        return response.text

    resp_str = str(response)
    match = re.search(r'text="""(.+?)"""', resp_str, re.DOTALL)
    if match:
        return match.group(1)
    return resp_str


# ---------------------------------------------------------------------------
# Code-fence stripping
# ---------------------------------------------------------------------------

def strip_code_fences(text: str) -> str:
    """Strip markdown code fences (```json ... ```)."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


# ---------------------------------------------------------------------------
# JSON escape repair
# ---------------------------------------------------------------------------

def _fix_json_escapes(text: str) -> str:
    r"""Fix common LLM JSON escape issues (invalid \' etc.)."""
    text = text.replace("\\'", "'")
    text = re.sub(r'\\(?!["\\/bfnrtu])', "", text)
    return text


# ---------------------------------------------------------------------------
# Refusal detection
# ---------------------------------------------------------------------------

_REFUSAL_PATTERNS = (
    "i cannot", "i can't", "i'm unable", "i am unable",
    "i'm not able", "i am not able", "i apologize",
    "i'm sorry", "i am sorry", "as an ai",
    "not appropriate", "cannot generate", "can't generate",
    "against my guidelines", "safety", "harmful", "offensive",
    "sensitive topic", "not comfortable",
)


def detect_refusal(text: str) -> Optional[str]:
    """Return the refusal snippet (first 300 chars) if detected, else None."""
    lower = text.strip().lower()
    if lower.startswith("{") or lower.startswith("["):
        return None
    for pattern in _REFUSAL_PATTERNS:
        if pattern in lower:
            return text.strip()[:300]
    return None


# ---------------------------------------------------------------------------
# JSON parsing (progressive fallback)
# ---------------------------------------------------------------------------

def parse_json(text: str, agent_name: str = "agent") -> Dict[str, Any]:
    """Parse JSON from LLM response with progressive fallbacks.

    1. Check for refusal
    2. Strip code fences
    3. Strict parse
    4. Fix escape sequences and retry
    5. Allow control characters (strict=False)
    """
    refusal = detect_refusal(text)
    if refusal:
        logger.warning("[%s] LLM refused request: %s", agent_name, refusal)
        raise ValueError(f"LLM refused to generate content: {refusal}")

    cleaned = strip_code_fences(text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    fixed = _fix_json_escapes(cleaned)
    try:
        result = json.loads(fixed)
        logger.warning("[%s] JSON required escape repair", agent_name)
        return result
    except json.JSONDecodeError:
        pass

    try:
        result = json.loads(fixed, strict=False)
        logger.warning("[%s] JSON required strict=False", agent_name)
        return result
    except json.JSONDecodeError as exc:
        logger.error(
            "[%s] JSON parse failed: %s\nRaw (first 500): %s",
            agent_name, exc, text[:500],
        )
        raise ValueError(
            f"Invalid JSON from {agent_name}: {exc}\nRaw: {text[:500]}"
        ) from exc


__all__ = [
    "extract_text",
    "strip_code_fences",
    "parse_json",
    "detect_refusal",
]
