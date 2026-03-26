"""Publisher agent -- full ideate-write-review/refine pipeline via ADK."""

import logging
import uuid
from typing import Any, Dict, Optional

from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService

from ..tasks import PUBLISH
from ..utils.event_bus import emit_event
from ..utils.log import log_llm_prompt, log_llm_response
from ..utils.response import normalize_content, parse_json, strip_code_fences
from ..workflows.publish import create_publish_pipeline
from .base import BaseAgentService

logger = logging.getLogger(__name__)


def _is_json_like(text) -> bool:
    """Quick check whether *text* plausibly starts with JSON."""
    if isinstance(text, dict):
        return True
    s = strip_code_fences(str(text).strip()) if isinstance(text, str) else ""
    return s.startswith("{") or s.startswith("[")


def _extract_state_from_events(events: list, key: str) -> Optional[str]:
    """Walk events in reverse to find the last non-empty state_delta for *key*."""
    for event in reversed(events):
        if event.actions and event.actions.state_delta:
            val = event.actions.state_delta.get(key)
            if val:
                return val
    return None


def _extract_valid_json_from_events(events: list, key: str) -> Optional[str]:
    """Walk events in reverse to find the last *JSON-like* state_delta for *key*.

    Unlike ``_extract_state_from_events`` this skips values that are clearly
    not JSON (e.g. a refiner that output prose instead of content).
    """
    for event in reversed(events):
        if event.actions and event.actions.state_delta:
            val = event.actions.state_delta.get(key)
            if val and _is_json_like(val):
                return val
    return None


_FORMAT_KEYS = {"quiz", "story", "game", "simulation"}


def _unwrap_format(data: dict) -> dict:
    """Unwrap single-key format wrappers like {"quiz": {...}}."""
    if not isinstance(data, dict):
        return data
    keys = list(data.keys())
    if len(keys) == 1 and keys[0].lower() in _FORMAT_KEYS:
        inner = data[keys[0]]
        if isinstance(inner, dict):
            return inner
    return data


def _extract_writer_tool_output(events: list) -> Optional[str]:
    """Fallback: extract content from a writer AgentTool's function_response.

    When the LeadWriter delegates to a format writer via AgentTool, the actual
    content lives in the function_response (not the LeadWriter's text output).
    """
    for event in reversed(events):
        if not event.content or not event.content.parts:
            continue
        for part in event.content.parts:
            fr = getattr(part, "function_response", None)
            if not fr:
                continue
            name = fr.name or ""
            if not name.lower().endswith("writer"):
                continue
            resp = fr.response
            if isinstance(resp, dict):
                return resp.get("result") or str(resp)
            return str(resp) if resp else None
    return None


class PublisherAgentService(BaseAgentService):
    """Runs the full publish pipeline as an ADK SequentialAgent.

    Receives pre-built ADK agents (including a single lead writer)
    to compose the pipeline:
      Ideator -> LeadWriter -> Loop(Parallel(Reviewer, Verifier), Refiner)
    """

    def __init__(
        self,
        ideator: Agent,
        writer: Agent,
        reviewer: Agent,
        refiner: Agent,
        verifier: Agent,
        session_service: Optional[InMemorySessionService] = None,
    ):
        super().__init__(session_service=session_service)
        self._register_tasks([PUBLISH])
        self._ideator = ideator
        self._writer = writer
        self._reviewer = reviewer
        self._refiner = refiner
        self._verifier = verifier
        self._pipeline: Any = None
        self._pipeline_agents.extend(
            [ideator, writer, reviewer, refiner, verifier]
        )

    def _get_pipeline(self):
        if self._pipeline is None:
            self._pipeline = create_publish_pipeline(
                self._ideator,
                self._writer,
                self._reviewer,
                self._refiner,
                self._verifier,
            )
        return self._pipeline

    def prepare_task(
        self, task_id: str, params: Dict[str, Any],
    ) -> str:
        formats = params.get("formats", [])
        prompt = params.get("prompt", "")
        if formats:
            prompt += f"\n\nREQUESTED FORMATS: {', '.join(formats)}"
        domain = params.get("domain", "realworld")
        prompt += f"\nDOMAIN: {domain}"
        if not prompt.strip():
            prompt = "Create content"
        return prompt

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        pipeline = self._get_pipeline()
        runner = self._ensure_session_runner("publish", pipeline)
        session_id = getattr(self, "_current_session_id", None)
        if not session_id:
            session_id = f"publish_{uuid.uuid4().hex[:8]}"

        log_llm_prompt(logger, pipeline.name, prompt)
        events, session = await self.run_session(runner, prompt, session_id)

        draft = self._extract_draft(session, events)
        if draft:
            result = (
                draft if isinstance(draft, dict)
                else parse_json(strip_code_fences(draft), agent_name=pipeline.name)
            )
            result = _unwrap_format(result)
            result = normalize_content(result, caller="PublishPipeline")
            result["session_id"] = session_id
            log_llm_response(logger, pipeline.name, result)
            emit_event("pipeline.complete",
                       f"Pipeline finished — {len(events)} events",
                       level="success", events_count=len(events))
            return result

        emit_event("pipeline.complete", "Pipeline produced no output",
                   level="error", events_count=len(events))
        logger.error("Publish pipeline produced no draft_content")
        return {"error": "Pipeline produced no output", "session_id": session_id}

    def _extract_draft(self, session, events: list) -> Optional[str]:
        """Try session state first, then events, then tool output fallback.

        Validates that the candidate is JSON-like before accepting it.  If
        the refiner overwrote ``draft_content`` with prose (e.g. an error
        explanation) we fall back to the last valid JSON snapshot in the
        event stream.
        """
        if session and session.state:
            draft = session.state.get("draft_content")
            if draft:
                logger.debug("draft_content from session state (%d chars)", len(str(draft)))
                if _is_json_like(draft):
                    return draft
                logger.warning(
                    "draft_content in session state is not JSON – "
                    "falling back to last valid snapshot in events"
                )

        draft = _extract_valid_json_from_events(events, "draft_content")
        if draft:
            logger.debug("draft_content from events fallback (%d chars)", len(str(draft)))
            return draft

        draft = _extract_writer_tool_output(events)
        if draft:
            logger.debug("draft_content from writer tool output fallback")
        return draft
