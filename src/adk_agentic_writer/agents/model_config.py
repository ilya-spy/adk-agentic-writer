"""Centralized model configuration for pipeline agents.

Maps agent roles to model name + thinking budget, allowing per-stage
tuning of latency vs quality.  Thinking budget of None means auto
(Gemini default); 0 disables thinking entirely.
"""

from __future__ import annotations

import logging
from typing import Optional

from google.genai import types

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "gemini-2.5-flash"

PIPELINE_MODELS: dict[str, dict] = {
    "ideator":     {"model": _DEFAULT_MODEL, "thinking_budget": None},
    "writer":      {"model": _DEFAULT_MODEL, "thinking_budget": None},
    "lead_writer": {"model": _DEFAULT_MODEL, "thinking_budget": 0},
    "reviewer":    {"model": _DEFAULT_MODEL, "thinking_budget": 1024, "max_output_tokens": 2048, "json_output": True},
    "verifier":    {"model": _DEFAULT_MODEL, "thinking_budget": 4096, "max_output_tokens": 4096},
    "refiner":     {"model": _DEFAULT_MODEL, "thinking_budget": 2048},
}


def get_generate_content_config(
    role: str,
    *,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
) -> Optional[types.GenerateContentConfig]:
    """Build a GenerateContentConfig for *role*, or None if all defaults.

    *max_output_tokens* from caller (e.g. FormatSpec.max_tokens) overrides
    the role-level default in PIPELINE_MODELS.
    """
    cfg = PIPELINE_MODELS.get(role, {})
    thinking_budget = cfg.get("thinking_budget")
    mot = max_output_tokens or cfg.get("max_output_tokens")

    json_output = cfg.get("json_output", False)
    if thinking_budget is None and temperature is None and mot is None and not json_output:
        return None

    kwargs: dict = {}
    if json_output:
        kwargs["response_mime_type"] = "application/json"

    if thinking_budget is not None:
        kwargs["thinking_config"] = types.ThinkingConfig(
            thinking_budget=thinking_budget,
        )
    if temperature is not None:
        kwargs["temperature"] = temperature
    if mot is not None:
        kwargs["max_output_tokens"] = mot

    return types.GenerateContentConfig(**kwargs)


def get_model(role: str) -> str:
    """Return the model name for *role*."""
    return PIPELINE_MODELS.get(role, {}).get("model", _DEFAULT_MODEL)
