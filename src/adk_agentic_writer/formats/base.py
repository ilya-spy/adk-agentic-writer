"""Base dataclasses for content format specifications."""

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

    Holds everything agents need: prompts, schemas, defaults, and
    everything the API needs: parameter_specs for the frontend.
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
    aliases: List[str] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 2048
