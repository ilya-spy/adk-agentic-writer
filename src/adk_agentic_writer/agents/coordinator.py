"""Coordinator -- collects sub-agent tasks and routes by task_id."""

import logging
from typing import Any, Dict, List

from ..models.agent_models import AgentTask
from .base import BaseAgentService, MODEL
from .ideator import IdeatorAgent
from .writer import WriterAgent
from .reviewer import ReviewerAgent
from .refiner import RefinerAgent
from .publisher import PublisherAgent

logger = logging.getLogger(__name__)


class Coordinator(BaseAgentService):
    """Central router that delegates to sub-agent services by task_id.

    ``get_supported_tasks()`` returns the union of all sub-agent tasks.
    ``process_task(task_id, params)`` routes to the correct sub-agent.
    """

    def __init__(self, model_name: str = MODEL):
        super().__init__(model=model_name)

        self._sub_agents: List[BaseAgentService] = [
            IdeatorAgent(model_name),
            WriterAgent(model_name),
            ReviewerAgent(model_name),
            RefinerAgent(model_name),
            PublisherAgent(model_name),
        ]

        all_tasks: List[AgentTask] = []
        self._router: Dict[str, BaseAgentService] = {}
        for agent in self._sub_agents:
            for task in agent.get_supported_tasks():
                all_tasks.append(task)
                self._router[task.task_id] = agent

        self._register_tasks(all_tasks)

        logger.info(
            "Coordinator ready: tasks=%s",
            [t.task_id for t in all_tasks],
        )

    async def process_task(
        self, task_id: str, params: Dict[str, Any],
    ) -> Dict[str, Any]:
        agent = self._router.get(task_id)
        if not agent:
            raise ValueError(f"Unknown task: {task_id}")
        return await agent.process_task(task_id, params)


__all__ = ["Coordinator"]
