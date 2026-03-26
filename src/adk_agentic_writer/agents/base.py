"""Base agent service with shared ADK runner and task infrastructure.

Manages a pool of InMemoryRunners (lazy, cached by key),
task discovery/resolution, and prompt execution with JSON parsing.
Concrete agent services inherit and register their tasks.

For pipeline agents that need session continuity, use ``_ensure_session_runner``
+ ``run_session`` instead of ``_ensure_runner`` + ``_run``.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from ..utils.proxy import clear_proxy_env

clear_proxy_env()

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from ..models.agent_models import AgentTask
from ..utils.response import extract_text, parse_json
from ..utils.validator import validate_and_coerce
from ..utils.event_bus import emit_event
from ..utils import log as _log_cfg
from ..utils.log import log_llm_prompt, log_llm_response

logger = logging.getLogger(__name__)

USER_ID = "default"
SESSION_APP_NAME = "adk_writer"


class BaseAgentService:
    """Shared runner pool, task registry, and prompt execution.

    Subclasses populate ``_tasks`` via ``_register_tasks`` and override:
      - ``prepare_task`` to build a prompt from task params
      - ``run_prompt``   to execute a prompt through the ADK runner
    """

    def __init__(self, session_service: Optional[InMemorySessionService] = None):
        self._pipeline_agents: List[Agent] = []
        self._service_agents: List[Agent] = []
        self._runners: Dict[str, InMemoryRunner] = {}
        self._session_runners: Dict[str, Runner] = {}
        self._session_service = session_service
        self._tasks: List[AgentTask] = []
        self._task_by_id: Dict[str, AgentTask] = {}
        cls_name = self.__class__.__name__
        logger.info("[%s] initialized", cls_name)
        emit_event("agent.init", f"{cls_name} initialized", agent=cls_name)

    def _register_tasks(self, tasks: List[AgentTask]) -> None:
        """Append/update tasks. Duplicate task_ids are replaced."""
        for t in tasks:
            self._task_by_id[t.task_id] = t
        self._tasks = list(self._task_by_id.values())

    def get_supported_tasks(self) -> List[AgentTask]:
        return list(self._tasks)

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        return self._task_by_id.get(task_id)
    
    def get_agents(self, mode: str = "pipeline") -> List[Agent]:
        """Return ADK agents.  *mode*: ``'pipeline'`` or ``'service'``."""
        if mode == "service":
            return list(self._service_agents)
        return list(self._pipeline_agents)

    def handles(self, task_id: str) -> bool:
        return task_id in self._task_by_id

    def _ensure_runner(self, key: str, agent: Agent) -> InMemoryRunner:
        if key not in self._runners:
            self._runners[key] = InMemoryRunner(agent=agent)
            logger.info("Created runner: %s", key)
            emit_event("agent.spawn", f"Runner spawned: {key}", agent=key)
        return self._runners[key]

    def _ensure_session_runner(self, key: str, agent: Agent) -> Runner:
        """Like ``_ensure_runner`` but returns an ADK ``Runner`` backed by the
        shared ``InMemorySessionService``, enabling session continuity.

        All session runners share ``SESSION_APP_NAME`` so that different agents
        (ideator, writer, ...) can participate in the same session.
        """
        if key not in self._session_runners:
            if self._session_service is None:
                raise RuntimeError(
                    f"Cannot create session runner '{key}': no session_service provided"
                )
            self._session_runners[key] = Runner(
                agent=agent,
                app_name=SESSION_APP_NAME,
                session_service=self._session_service,
            )
            logger.info("Created session runner: %s (app=%s)", key, SESSION_APP_NAME)
            emit_event("agent.spawn", f"Session runner spawned: {key}", agent=key)
        return self._session_runners[key]

    async def run_session(
        self,
        runner: Runner,
        prompt: str,
        session_id: str,
    ) -> Tuple[list, Any]:
        """Run a prompt through *runner* within a managed session.

        Adapted from the ADK Day-3a notebook ``run_session`` helper.
        Creates the session if it doesn't exist, otherwise retrieves it,
        then streams events via ``runner.run_async``.

        Returns ``(events, session)`` so callers can inspect state/events.
        """
        app_name = runner.app_name
        try:
            session = await self._session_service.create_session(
                app_name=app_name, user_id=USER_ID, session_id=session_id,
            )
        except Exception:
            session = await self._session_service.get_session(
                app_name=app_name, user_id=USER_ID, session_id=session_id,
            )

        message = types.Content(
            role="user", parts=[types.Part(text=prompt)],
        )

        events = []
        async for event in runner.run_async(
            user_id=USER_ID, session_id=session.id, new_message=message,
        ):
            events.append(event)

        session = await self._session_service.get_session(
            app_name=app_name, user_id=USER_ID, session_id=session.id,
        )
        return events, session

    async def _run(
        self,
        runner: InMemoryRunner,
        agent_name: str,
        prompt: str,
        *,
        model_class: Optional[type] = None,
    ) -> Dict[str, Any]:
        log_llm_prompt(logger, agent_name, prompt)
        response = await runner.run_debug(prompt, quiet=not _log_cfg.LOG_LLM_IO)
        text = extract_text(response)
        result = parse_json(text, agent_name=agent_name)
        if model_class is not None:
            result, _ = validate_and_coerce(result, model_class, agent_name)
        log_llm_response(logger, agent_name, result)
        return result

    async def _run_in_session(
        self,
        runner_key: str,
        agent: Agent,
        agent_name: str,
        prompt: str,
        session_id: str,
        *,
        model_class: Optional[type] = None,
    ) -> Dict[str, Any]:
        """Like ``_run`` but routes through the shared session runner."""
        log_llm_prompt(logger, agent_name, prompt)
        session_runner = self._ensure_session_runner(runner_key, agent)
        events, _session = await self.run_session(session_runner, prompt, session_id)
        text = extract_text(events)
        result = parse_json(text, agent_name=agent_name)
        if model_class is not None:
            result, _ = validate_and_coerce(result, model_class, agent_name)
        log_llm_response(logger, agent_name, result)
        return result

    async def _run_agent(
        self,
        runner_key: str,
        agent: Agent,
        agent_name: str,
        prompt: str,
        *,
        model_class: Optional[type] = None,
    ) -> Dict[str, Any]:
        """Smart dispatcher: uses session runner when ``_current_session_id``
        is active, otherwise falls back to ``InMemoryRunner``."""
        session_id = getattr(self, "_current_session_id", None)
        if session_id and self._session_service:
            return await self._run_in_session(
                runner_key, agent, agent_name, prompt, session_id,
                model_class=model_class,
            )
        runner = self._ensure_runner(runner_key, agent)
        return await self._run(runner, agent_name, prompt, model_class=model_class)

    # ------------------------------------------------------------------
    # Public API -- subclasses override prepare_task and run_prompt
    # ------------------------------------------------------------------

    def prepare_task(
        self,
        task_id: str,
        params: Dict[str, Any],
    ) -> str:
        """Build a prompt string from task parameters."""
        raise NotImplementedError(
            f"{self.__class__.__name__}.prepare_task not implemented"
        )

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        """Execute a prompt through the agent's runner / pipeline."""
        raise NotImplementedError(
            f"{self.__class__.__name__}.run_prompt not implemented"
        )

    async def process_task(
        self,
        task_id: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Convenience: prepare_task -> run_prompt.

        Extracts ``session_id`` from *params* and stores it on
        ``self._current_session_id`` so that ``_run_agent`` can route
        through the session runner automatically.
        """
        self._current_session_id = params.pop("session_id", None)
        cls_name = self.__class__.__name__
        emit_event("task.start", f"{cls_name} executing {task_id}", agent=cls_name, task=task_id)
        prompt = self.prepare_task(task_id, params)
        result = await self.run_prompt(prompt)
        emit_event("task.complete", f"{cls_name} completed {task_id}", level="success", agent=cls_name, task=task_id)
        return result


def find_by_task(
    agents: List["BaseAgentService"],
    task_id: str,
) -> "BaseAgentService":
    """Find the first agent in *agents* that handles *task_id*."""
    for agent in agents:
        if agent.handles(task_id):
            return agent
    raise ValueError(f"No agent in the team handles task '{task_id}'")
