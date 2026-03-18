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


def _repair_truncated_json(text: str) -> Optional[str]:
    """Attempt to close a truncated JSON object/array.
    Returns the repaired string, or None if repair seems impossible.
    """
    depth_stack: list[str] = []
    in_string = False
    escape_next = False
    last_structural_pos = 0

    for i, ch in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in ("{", "["):
            depth_stack.append("}" if ch == "{" else "]")
            last_structural_pos = i
        elif ch in ("}", "]"):
            if depth_stack:
                depth_stack.pop()
            last_structural_pos = i

    if not depth_stack:
        return None

    # Cut back to the last cleanly-closed element
    candidate = text
    if in_string:
        # Close the dangling string
        candidate += '"'

    # Remove trailing partial tokens (comma, colon, whitespace, partial key)
    candidate = re.sub(r"[,:\s]+$", "", candidate)
    # If we ended inside a string that we just closed, the above won't help
    # much — try stripping the last incomplete key-value pair
    candidate = re.sub(r',\s*"[^"]*"?\s*:?\s*"?[^"]*$', "", candidate)
    candidate = re.sub(r"[,\s]+$", "", candidate)

    # Append closers in reverse order
    candidate += "".join(reversed(depth_stack))
    return candidate


# ---------------------------------------------------------------------------
# Refusal detection
# ---------------------------------------------------------------------------

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
    6. Repair truncated JSON (LLM hit token limit)
    """
    refusal = detect_refusal(text)
    if refusal:
        logger.warning("[%s] LLM refused request: %s", agent_name, refusal)
        raise ValueError(f"LLM refused to generate content: {refusal}")

    cleaned = strip_code_fences(text)

    # --- 1. Strict parse ---
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # --- 2. Escape repair ---
    fixed = _fix_json_escapes(cleaned)
    try:
        result = json.loads(fixed)
        logger.warning("[%s] JSON required escape repair", agent_name)
        return result
    except json.JSONDecodeError:
        pass

    # --- 3. Lenient parse (allow control chars) ---
    try:
        result = json.loads(fixed, strict=False)
        logger.warning("[%s] JSON required strict=False", agent_name)
        return result
    except json.JSONDecodeError:
        pass

    # --- 4. Truncated JSON repair ---
    repaired = _repair_truncated_json(fixed)
    if repaired:
        try:
            result = json.loads(repaired, strict=False)
            logger.warning(
                "[%s] JSON was truncated – repaired by closing open structures",
                agent_name,
            )
            return result
        except json.JSONDecodeError:
            pass

    # --- 5. Give up ---
    logger.error(
        "[%s] JSON parse failed after all recovery attempts.\nRaw (first 500): %s",
        agent_name,
        text[:500],
    )
    raise ValueError(
        f"Invalid JSON from {agent_name}. "
        f"Response may be truncated (token limit). Raw: {text[:500]}"
    )


__all__ = [
    "extract_text",
    "strip_code_fences",
    "parse_json",
    "detect_refusal",
]
