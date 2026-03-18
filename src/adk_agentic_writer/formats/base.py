"""Base dataclasses for content format specifications."""

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Type

from pydantic import BaseModel


@dataclass
class ParamSpec:
    """Describes one user-facing parameter for a content format."""

    name: str
    type: str  # "int", "str", "float"
    default: Any
    description: str


@dataclass
class FormatSpec:
    """Self-contained specification for a content format.

    Each flavor (e.g. "quiz", "trivia", "test") gets its own FormatSpec
    instance with the ``flavor`` field set accordingly.
    """

    name: str
    label: str
    model_class: Type[BaseModel]
    default_params: Dict[str, Any] = field(default_factory=dict)
    parameter_specs: List[ParamSpec] = field(default_factory=list)
    schema_description: str = ""
    sample_output: Dict[str, Any] = field(default_factory=dict)
    writer_instruction: str = ""
    writer_prompt: str = ""
    reviewer_prompt: str = ""
    refiner_prompt: str = ""
    flavors: List[str] = field(default_factory=list)
    flavor: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048

    def for_flavor(self, flavor: str) -> "FormatSpec":
        """Return a shallow copy with ``flavor`` set."""
        clone = copy.copy(self)
        clone.flavor = flavor
        clone.default_params = {**self.default_params, "flavor": flavor}
        return clone
