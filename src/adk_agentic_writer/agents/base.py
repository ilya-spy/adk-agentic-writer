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


class BaseAgentService:
    """Shared runner pool, task registry, and prompt execution.

    Subclasses populate ``_tasks`` via ``_register_tasks`` and override:
      - ``prepare_task`` to build a prompt from task params
      - ``run_prompt``   to execute a prompt through the ADK runner
    """

    def __init__(self):
        self._pipeline_agents: List[Agent] = []
        self._service_agents: List[Agent] = []
        self._runners: Dict[str, InMemoryRunner] = {}
        self._tasks: List[AgentTask] = []
        self._task_by_id: Dict[str, AgentTask] = {}

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
        """Convenience: prepare_task -> run_prompt."""
        prompt = self.prepare_task(task_id, params)
        return await self.run_prompt(prompt)


def find_by_task(
    agents: List["BaseAgentService"],
    task_id: str,
) -> "BaseAgentService":
    """Find the first agent in *agents* that handles *task_id*."""
    for agent in agents:
        if agent.handles(task_id):
            return agent
    raise ValueError(f"No agent in the team handles task '{task_id}'")
