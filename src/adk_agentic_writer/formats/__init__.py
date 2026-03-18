"""Content format registry.

Each format module defines a FormatSpec with all prompts, schemas,
parameters, and sample outputs. The registry makes them available
by name or alias.
"""

from typing import Dict, List, Optional

from .base import FormatSpec, ParamSpec
from .quiz import QUIZ_FORMAT
from .story import STORY_FORMAT
from .game import GAME_FORMAT
from .simulation import SIMULATION_FORMAT


def _build_registry() -> Dict[str, FormatSpec]:
    """Build name+alias -> FormatSpec lookup."""
    reg: Dict[str, FormatSpec] = {}
    for fmt in [QUIZ_FORMAT, STORY_FORMAT, GAME_FORMAT, SIMULATION_FORMAT]:
        reg[fmt.name] = fmt
        for alias in fmt.aliases:
            reg[alias] = fmt
    return reg


FORMAT_REGISTRY: Dict[str, FormatSpec] = _build_registry()


def get_format(name: str) -> Optional[FormatSpec]:
    return FORMAT_REGISTRY.get(name)


def list_formats() -> List[FormatSpec]:
    """Return de-duplicated list of base formats (no aliases)."""
    seen: set = set()
    result: List[FormatSpec] = []
    for fmt in FORMAT_REGISTRY.values():
        if fmt.name not in seen:
            seen.add(fmt.name)
            result.append(fmt)
    return result


__all__ = [
    "FormatSpec",
    "ParamSpec",
    "FORMAT_REGISTRY",
    "get_format",
    "list_formats",
    "QUIZ_FORMAT",
    "STORY_FORMAT",
    "GAME_FORMAT",
    "SIMULATION_FORMAT",
]
