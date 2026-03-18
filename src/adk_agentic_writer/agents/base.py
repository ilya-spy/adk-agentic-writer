"""Base agent service with shared ADK runner and task infrastructure.

Manages a pool of InMemoryRunners (lazy, cached by key),
task discovery/resolution, and prompt execution with JSON parsing.
Concrete agent services inherit and register their tasks.
"""

import logging
from typing import Any, Dict, List, Optional

from ..utils.proxy import clear_proxy_env

clear_proxy_env()

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

from ..models.agent_models import AgentTask
from ..utils.response import extract_text, parse_json
from ..utils.log import log_llm_prompt, log_llm_response

logger = logging.getLogger(__name__)

MODEL = "gemini-2.5-flash"


class BaseAgentService:
    """Shared runner pool, task registry, and prompt execution.

    Subclasses populate ``_tasks`` via ``_register_tasks`` and override
    ``process_task`` to handle their specific tasks.
    """

    def __init__(self, model: str = MODEL):
        self._model = model
        self._runners: Dict[str, InMemoryRunner] = {}
        self._tasks: List[AgentTask] = []
        self._task_by_id: Dict[str, AgentTask] = {}

    def _register_tasks(self, tasks: List[AgentTask]) -> None:
        self._tasks = list(tasks)
        self._task_by_id = {t.task_id: t for t in tasks}

    def get_supported_tasks(self) -> List[AgentTask]:
        return list(self._tasks)

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        return self._task_by_id.get(task_id)

    def handles(self, task_id: str) -> bool:
        return task_id in self._task_by_id

    def _ensure_runner(self, key: str, agent: Agent) -> InMemoryRunner:
        if key not in self._runners:
            self._runners[key] = InMemoryRunner(agent=agent)
            logger.info("Created runner: %s", key)
        return self._runners[key]

    async def _run(
        self,
        runner: InMemoryRunner,
        agent_name: str,
        prompt: str,
    ) -> Dict[str, Any]:
        log_llm_prompt(logger, agent_name, prompt)
        response = await runner.run_debug(prompt, quiet=True)
        text = extract_text(response)
        result = parse_json(text, agent_name=agent_name)
        log_llm_response(logger, agent_name, result)
        return result

    async def process_task(
        self, task_id: str, params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a task by id. Subclasses must override."""
        raise NotImplementedError(
            f"{self.__class__.__name__} does not handle task '{task_id}'"
        )
