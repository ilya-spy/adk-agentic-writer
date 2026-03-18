"""Base agent service with shared ADK runner and task infrastructure.

Manages a pool of InMemoryRunners (lazy, cached by key),
task discovery/resolution, and prompt execution with JSON parsing.
Concrete services (Coordinator) inherit and add domain logic.
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

    Subclasses populate ``_tasks`` and call ``_ensure_runner`` /
    ``_run`` to execute prompts against cached ADK runners.
    """

    def __init__(self, model: str = MODEL):
        self._model = model
        self._runners: Dict[str, InMemoryRunner] = {}
        self._tasks: List[AgentTask] = []
        self._task_by_id: Dict[str, AgentTask] = {}
        self._type_to_task: Dict[str, AgentTask] = {}

    # ------------------------------------------------------------------
    # Task registry helpers
    # ------------------------------------------------------------------

    def _register_tasks(self, tasks: List[AgentTask]) -> None:
        """Populate task lookup indices."""
        self._tasks = list(tasks)
        self._task_by_id = {t.task_id: t for t in tasks}
        self._type_to_task = {}
        for t in tasks:
            for ct in t.content_types:
                self._type_to_task[ct] = t

    def get_supported_tasks(self) -> List[AgentTask]:
        return list(self._tasks)

    def resolve_task(
        self,
        task_id: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Optional[AgentTask]:
        if task_id and task_id in self._task_by_id:
            return self._task_by_id[task_id]
        if content_type and content_type in self._type_to_task:
            return self._type_to_task[content_type]
        return None

    @staticmethod
    def _effective_content_type(task: AgentTask, params: Dict[str, Any]) -> str:
        ct = params.get("content_type")
        if ct:
            return ct
        if task.content_types:
            return task.content_types[0]
        return "quiz"

    # ------------------------------------------------------------------
    # Runner pool
    # ------------------------------------------------------------------

    def _ensure_runner(self, key: str, agent: Agent) -> InMemoryRunner:
        """Get or create an InMemoryRunner for *agent*, cached by *key*."""
        if key not in self._runners:
            self._runners[key] = InMemoryRunner(agent=agent)
            logger.info("Created runner: %s", key)
        return self._runners[key]

    # ------------------------------------------------------------------
    # Prompt execution
    # ------------------------------------------------------------------

    async def _run(
        self,
        runner: InMemoryRunner,
        agent_name: str,
        prompt: str,
    ) -> Dict[str, Any]:
        """Execute *prompt* on *runner*, parse the JSON response."""
        log_llm_prompt(logger, agent_name, prompt)
        response = await runner.run_debug(prompt, quiet=True)
        text = extract_text(response)
        result = parse_json(text, agent_name=agent_name)
        log_llm_response(logger, agent_name, result)
        return result
