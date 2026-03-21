"""CoordinatorService -- collects sub-agent tasks and routes by task_id."""

import logging
from typing import Any, Dict, List

from ..models.agent_models import AgentTask
from .base import BaseAgentService

logger = logging.getLogger(__name__)


class CoordinatorService(BaseAgentService):
    """Central router that delegates to sub-agent services by task_id.

    Receives pre-built sub-agents via constructor injection.
    Routes ``prepare_task``, ``run_prompt``, and ``process_task``
    to the correct sub-agent based on task_id.
    """

    def __init__(
        self,
        sub_agents: List[BaseAgentService],
    ):
        super().__init__()

        self._sub_agents = list(sub_agents)

        all_tasks: List[AgentTask] = []
        self._router: Dict[str, BaseAgentService] = {}
        for svc in self._sub_agents:
            for task in svc.get_supported_tasks():
                all_tasks.append(task)
                self._router[task.task_id] = svc

        self._register_tasks(all_tasks)

        logger.info(
            "CoordinatorService ready: tasks=%s",
            [t.task_id for t in all_tasks],
        )

    def _resolve(self, task_id: str) -> BaseAgentService:
        svc = self._router.get(task_id)
        if not svc:
            raise ValueError(f"Unknown task: {task_id}")
        return svc

    def prepare_task(
        self, task_id: str, params: Dict[str, Any],
    ) -> str:
        svc = self._resolve(task_id)
        self._last_routed = svc
        return svc.prepare_task(task_id, params)

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        svc = getattr(self, "_last_routed", None)
        if not svc:
            raise RuntimeError(
                "CoordinatorService.run_prompt requires prepare_task first"
            )
        return await svc.run_prompt(prompt)

    async def process_task(
        self, task_id: str, params: Dict[str, Any],
    ) -> Dict[str, Any]:
        return await self._resolve(task_id).process_task(task_id, params)


__all__ = ["CoordinatorService"]
