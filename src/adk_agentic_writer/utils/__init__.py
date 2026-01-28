"""Utility functions for the ADK Agentic Writer."""

from .schema_helpers import (
    build_schema_instruction,
    model_to_example_json,
    model_to_json_schema,
)
from .variable_substitution import substitute_variables
from .text_provider import (
    TextProvider,
    TemplateTextProvider,
    GeminiTextProvider,
)
from .content_registry import (
    ContentTypeConfig,
    ContentRegistry,
    CONTENT_REGISTRY,
)

__all__ = [
    # Variable/schema utilities
    "substitute_variables",
    "model_to_example_json",
    "model_to_json_schema",
    "build_schema_instruction",
    # Text providers
    "TextProvider",
    "TemplateTextProvider",
    "GeminiTextProvider",
    # Content registry
    "ContentTypeConfig",
    "ContentRegistry",
    "CONTENT_REGISTRY",
]
