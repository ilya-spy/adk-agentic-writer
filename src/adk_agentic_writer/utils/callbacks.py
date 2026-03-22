"""ADK agent callbacks for lifecycle logging and SSE event emission.

These are attached to Agent() instances via before_agent_callback,
after_agent_callback, and before_model_callback.  They never interfere
with execution (always return None).
"""

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
