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


def _fix_double_braces(text: str) -> Optional[str]:
    """Collapse ``{{`` / ``}}`` to ``{`` / ``}`` outside JSON string literals.

    LLMs sometimes echo Python-template-style double braces from prompts.
    Valid JSON never contains ``{{`` or ``}}`` outside strings, so this is safe.
    Returns the fixed text if any replacements were made, else None.
    """
    if "{{" not in text and "}}" not in text:
        return None

    out: list[str] = []
    in_string = False
    escape_next = False
    i = 0
    changed = False
    while i < len(text):
        ch = text[i]
        if escape_next:
            escape_next = False
            out.append(ch)
            i += 1
            continue
        if ch == "\\" and in_string:
            escape_next = True
            out.append(ch)
            i += 1
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            i += 1
            continue
        if not in_string and i + 1 < len(text):
            pair = text[i : i + 2]
            if pair == "{{":
                out.append("{")
                i += 2
                changed = True
                continue
            if pair == "}}":
                out.append("}")
                i += 2
                changed = True
                continue
        out.append(ch)
        i += 1

    return "".join(out) if changed else None


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

    1. Strip code fences
    2. Check for refusal (after stripping so ``{``/``[`` guard works)
    3. Strict parse
    4. Fix escape sequences and retry
    5. Collapse double braces (``{{`` / ``}}``)
    6. Allow control characters (strict=False)
    7. Extract JSON object from surrounding prose
    8. Repair truncated JSON (LLM hit token limit)
    """
    cleaned = strip_code_fences(text)

    refusal = detect_refusal(cleaned)
    if refusal:
        logger.warning("[%s] LLM refused request: %s", agent_name, refusal)
        raise ValueError(f"LLM refused to generate content: {refusal}")

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

    # --- 3. Double-brace collapse (LLM echoed {{ / }} from prompt) ---
    debraced = _fix_double_braces(fixed)
    if debraced:
        try:
            result = json.loads(debraced)
            logger.warning("[%s] JSON required double-brace collapse", agent_name)
            return result
        except json.JSONDecodeError:
            fixed = debraced  # carry forward for subsequent steps

    # --- 4. Lenient parse (allow control chars) ---
    try:
        result = json.loads(fixed, strict=False)
        logger.warning("[%s] JSON required strict=False", agent_name)
        return result
    except json.JSONDecodeError:
        pass

    # --- 5. Extract JSON from surrounding prose ---
    json_start = fixed.find('{')
    json_end = fixed.rfind('}')
    if json_start >= 0 and json_end > json_start:
        substr = fixed[json_start:json_end + 1]
        try:
            result = json.loads(substr, strict=False)
            logger.warning("[%s] JSON extracted from surrounding text", agent_name)
            return result
        except json.JSONDecodeError:
            pass

    # --- 6. Truncated JSON repair ---
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

    # --- 7. Give up ---
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
