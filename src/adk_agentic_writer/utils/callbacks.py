"""ADK agent callbacks for lifecycle logging and SSE event emission.

These are attached to Agent() instances via before_agent_callback,
after_agent_callback, and before_model_callback.  They never interfere
with execution (always return None).
"""

import json
import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

from .event_bus import emit_event

logger = logging.getLogger("adk_agentic_writer.agents.callbacks")


def adk_before_agent(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """Fired when an ADK agent begins processing a request."""
    name = callback_context.agent_name
    logger.info("[%s] agent started", name)
    emit_event("agent.start", f"{name} started processing", agent=name)
    return None


def adk_after_agent(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """Fired when an ADK agent finishes processing a request."""
    name = callback_context.agent_name
    logger.info("[%s] agent completed", name)
    emit_event("agent.complete", f"{name} finished", level="success", agent=name)
    return None


def adk_before_model(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    """Fired before the LLM call.  Logs summary to SSE, full body to terminal."""
    name = callback_context.agent_name
    logger.debug("[%s] calling LLM…", name)
    emit_event("model.start", f"{name} calling LLM…", agent=name)
    return None


def _try_extract_metric(text: str, agent_name: str) -> Optional[dict]:
    """Best-effort extraction of key metrics from agent response text."""
    if not text:
        return None
    try:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        data = json.loads(cleaned)
        if agent_name == "ReviewerAgent" and "score" in data:
            return {"score": data["score"]}
        if agent_name == "VerifierAgent" and "confidence" in data:
            return {"confidence": data["confidence"]}
    except Exception:
        pass
    return None


def adk_after_model(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> Optional[LlmResponse]:
    """Fired after the LLM call. Emits tool calls, token usage, and errors."""
    name = callback_context.agent_name
    logger.debug("[%s] LLM responded", name)

    if llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            fc = getattr(part, "function_call", None)
            if fc and fc.name:
                emit_event("model.tool_call", f"{name} → {fc.name}",
                           agent=name, tool=fc.name)

    gm = llm_response.grounding_metadata
    if gm and gm.web_search_queries:
        queries = ", ".join(gm.web_search_queries[:3])
        logger.info("[%s] google_search: %s", name, queries)
        emit_event("model.tool_call",
                   f"{name} → google_search ({queries})",
                   agent=name, tool="google_search")

    tokens = None
    um = llm_response.usage_metadata
    if um and um.total_token_count:
        tokens = um.total_token_count

    extra: dict = {"agent": name}
    if tokens:
        extra["tokens"] = tokens

    resp_text = None
    if llm_response.content and llm_response.content.parts:
        resp_text = "".join(p.text or "" for p in llm_response.content.parts)

    metric = _try_extract_metric(resp_text, name)
    msg = f"{name} LLM responded"
    if metric:
        extra.update(metric)
        detail = ", ".join(f"{k}: {v}" for k, v in metric.items())
        msg = f"{name} LLM responded ({detail})"

    emit_event("model.complete", msg, **extra)

    if llm_response.error_code:
        emit_event("model.error",
                   f"{name} LLM error: {llm_response.error_message or llm_response.error_code}",
                   level="error", agent=name)

    return None
