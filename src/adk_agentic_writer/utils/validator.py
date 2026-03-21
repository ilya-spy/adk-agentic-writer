"""Structural validation and coercion for LLM-generated content.

Validates parsed JSON against Pydantic models and applies safe structural
fixes (missing defaults, type coercion) without altering content semantics.
Also provides format-specific integrity checks (e.g. quiz answer bounds).
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


def validate_and_coerce(
    data: Dict[str, Any],
    model_class: Type[BaseModel],
    agent_name: str = "agent",
) -> Tuple[Dict[str, Any], List[str]]:
    """Validate parsed JSON against a Pydantic model with auto-fix.

    Attempts to fix common structural issues:
    - Missing fields filled with schema defaults
    - Obvious type coercion (``"5"`` -> ``5`` for int fields)

    Returns ``(coerced_data, list_of_changes)``.
    Content strings, descriptions, etc. are never altered.
    """
    changes: List[str] = []

    try:
        model_class.model_validate(data)
        return data, changes
    except ValidationError:
        pass

    schema = model_class.model_json_schema()
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    for field_name, field_schema in properties.items():
        if field_name not in data:
            if field_name not in required:
                continue
            default = field_schema.get("default")
            if default is not None:
                data[field_name] = default
                changes.append(f"added missing field '{field_name}' with default {default!r}")
            elif field_schema.get("type") == "object":
                data[field_name] = {}
                changes.append(f"added missing field '{field_name}' as empty object")
            elif field_schema.get("type") == "array":
                data[field_name] = []
                changes.append(f"added missing field '{field_name}' as empty list")
            continue

        value = data[field_name]
        ftype = field_schema.get("type")

        if ftype == "integer" and isinstance(value, str):
            try:
                data[field_name] = int(value)
                changes.append(f"coerced '{field_name}' from str to int")
            except ValueError:
                pass
        elif ftype == "number" and isinstance(value, str):
            try:
                data[field_name] = float(value)
                changes.append(f"coerced '{field_name}' from str to float")
            except ValueError:
                pass
        elif ftype == "boolean" and isinstance(value, str):
            lower = value.lower()
            if lower in ("true", "1", "yes"):
                data[field_name] = True
                changes.append(f"coerced '{field_name}' from str to bool")
            elif lower in ("false", "0", "no"):
                data[field_name] = False
                changes.append(f"coerced '{field_name}' from str to bool")
        elif ftype == "string" and not isinstance(value, str) and value is not None:
            data[field_name] = str(value)
            changes.append(f"coerced '{field_name}' to str")

    try:
        model_class.model_validate(data)
    except ValidationError as exc:
        logger.warning(
            "[%s] Pydantic validation still fails after coercion: %s",
            agent_name,
            exc.error_count(),
        )

    if changes:
        logger.info(
            "[%s] Structural coercion applied: %s",
            agent_name,
            "; ".join(changes),
        )

    return data, changes


def schema_validate(
    content: Dict[str, Any],
    content_type: str,
) -> Dict[str, Any]:
    """Format-aware validation combining Pydantic schema + domain rules.

    Returns a review-style dict with ``valid``, ``score``, ``errors``,
    ``warnings``, and ``summary``.
    """
    from ..formats import get_format

    errors: List[str] = []
    warnings: List[str] = []

    if not content:
        return {
            "valid": False,
            "score": 0,
            "errors": ["Content is empty"],
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
        _validate_quiz(content, errors, warnings)
    elif content_type in ("story", "narrative", "branched_narrative", "adventure"):
        _validate_story(content, errors, warnings)
    elif content_type in ("game", "quest_game", "quest", "rpg"):
        _validate_game(content, errors, warnings)
    elif content_type in ("simulation", "web_simulation", "interactive", "simulator"):
        _validate_simulation(content, errors, warnings)

    valid = len(errors) == 0
    score = 100 if valid else max(0, 100 - len(errors) * 20)
    return {
        "valid": valid,
        "score": score,
        "errors": errors,
        "warnings": warnings,
        "summary": "Schema validation passed" if valid else "Schema issues found",
    }


def _validate_quiz(
    content: Dict[str, Any],
    errors: List[str],
    warnings: List[str],
) -> None:
    questions = content.get("questions", [])
    if not questions:
        errors.append("Quiz has no questions")
    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            continue
        opts = q.get("options", [])
        ca = q.get("correct_answer", 0)
        if isinstance(ca, int) and ca >= len(opts):
            errors.append(
                f"Question {i}: correct_answer index {ca} "
                f"out of bounds (only {len(opts)} options)"
            )
        tier = q.get("tier", "")
        score = q.get("score", 0)
        expected = {"low": 1, "mid": 2, "high": 3}
        if tier in expected and score != expected[tier]:
            warnings.append(
                f"Question {i}: tier '{tier}' expects score {expected[tier]}, got {score}"
            )


def _validate_story(
    content: Dict[str, Any],
    errors: List[str],
    warnings: List[str],
) -> None:
    nodes = content.get("nodes", {})
    start = content.get("start_node", "start")
    if start not in nodes:
        errors.append(f"Story missing start node '{start}'")
    endings = [nid for nid, n in nodes.items() if isinstance(n, dict) and n.get("is_ending")]
    if len(endings) < 1:
        warnings.append("Story has no ending nodes")
    for nid, node in nodes.items():
        if not isinstance(node, dict):
            continue
        for branch in node.get("branches", []):
            if isinstance(branch, dict):
                target = branch.get("next_node_id", "")
                if target and target not in nodes:
                    errors.append(f"Node '{nid}' branch references missing node '{target}'")


def _validate_game(
    content: Dict[str, Any],
    errors: List[str],
    warnings: List[str],
) -> None:
    nodes = content.get("nodes", {})
    start = content.get("start_node", "")
    if start and start not in nodes:
        errors.append(f"Game start_node '{start}' not found in nodes")
    if not content.get("victory_conditions"):
        warnings.append("Game has no victory conditions")


def _validate_simulation(
    content: Dict[str, Any],
    errors: List[str],
    warnings: List[str],
) -> None:
    variables = content.get("variables", [])
    controls = content.get("controls", [])
    var_names = {v.get("name", "") for v in variables if isinstance(v, dict)}
    for ctrl in controls:
        if not isinstance(ctrl, dict):
            continue
        for affected in ctrl.get("affects", []):
            if affected not in var_names:
                warnings.append(
                    f"Control '{ctrl.get('label', '?')}' affects unknown variable '{affected}'"
                )
