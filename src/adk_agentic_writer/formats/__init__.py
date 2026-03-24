"""Content format registry.

Each format module defines a FormatSpec with prompts, schemas, parameters,
and sample outputs.  The registry creates a separate entry per *flavor*
so that ``get_format("trivia")`` returns a FormatSpec with ``flavor="trivia"``.
"""

from typing import Dict, List, Optional

from .base import FormatSpec, ParamSpec
from .quiz import QUIZ_FORMAT
from .story import STORY_FORMAT
from .game import GAME_FORMAT
from .simulation import SIMULATION_FORMAT

_BASE_FORMATS = [QUIZ_FORMAT, STORY_FORMAT, GAME_FORMAT, SIMULATION_FORMAT]


def _build_registry() -> Dict[str, FormatSpec]:
    """Build flavor -> FormatSpec lookup (one entry per flavor)."""
    reg: Dict[str, FormatSpec] = {}
    for fmt in _BASE_FORMATS:
        for flavor in fmt.flavors:
            reg[flavor] = fmt.for_flavor(flavor)
        if fmt.name not in reg:
            reg[fmt.name] = fmt.for_flavor(fmt.name)
    return reg


FORMAT_REGISTRY: Dict[str, FormatSpec] = _build_registry()


def get_format(name: str) -> Optional[FormatSpec]:
    return FORMAT_REGISTRY.get(name)


def list_formats() -> List[FormatSpec]:
    """Return de-duplicated list of base formats (one per base name)."""
    seen: set = set()
    result: List[FormatSpec] = []
    for fmt in _BASE_FORMATS:
        if fmt.name not in seen:
            seen.add(fmt.name)
            result.append(fmt.for_flavor(fmt.name))
    return result


def detect_content_format(data: dict) -> Optional[str]:
    """Detect which content format *data* represents based on its keys."""
    if not isinstance(data, dict):
        return None
    if "questions" in data and isinstance(data["questions"], list):
        return "quiz"
    if "variables" in data or "parameters" in data:
        return "simulation"
    if "nodes" in data and "victory_conditions" in data:
        return "game"
    if "nodes" in data:
        return "story"
    return None


__all__ = [
    "FormatSpec",
    "ParamSpec",
    "FORMAT_REGISTRY",
    "get_format",
    "list_formats",
    "detect_content_format",
    "QUIZ_FORMAT",
    "STORY_FORMAT",
    "GAME_FORMAT",
    "SIMULATION_FORMAT",
]
