"""Coordinator routes tasks to content agents.

Discovers tasks from agents and builds content_type -> task mapping dynamically.
"""

import logging
from typing import Any, Dict, List, Optional

from ...models.agent_models import AgentModel, AgentTask
from ...teams.content_team import CONTENT_WRITER
from ..stateful_agent import StatefulAgent
from .designer import DesignerAgent
from .writer import WriterAgent

logger = logging.getLogger(__name__)


class CoordinatorAgent(StatefulAgent):
    """Coordinator aggregates tasks from agents. Routes by task_id or content_type."""

    def __init__(self, agent_id: str = "static_coordinator"):
        model = AgentModel(name=agent_id)
        super().__init__(agent_id=agent_id, config=CONTENT_WRITER, model=model)

        # Create one writer and one designer
        self._writer = WriterAgent("writer", "quiz")
        self._designer = DesignerAgent("designer", "quest_game")

        # Build task_id -> agent mapping
        self._task_to_agent: Dict[str, Any] = {}
        for agent in [self._writer, self._designer]:
            for task in agent.get_supported_tasks():
                self._task_to_agent[task.task_id] = agent

        # Build content_type -> task mapping from task.content_types
        self._content_type_to_task: Dict[str, AgentTask] = {}
        for task in self.get_supported_tasks():
            for ct in task.content_types:
                self._content_type_to_task[ct] = task

        logger.info(
            f"Coordinator: {len(self._task_to_agent)} tasks, {len(self._content_type_to_task)} content types"
        )

    def get_supported_tasks(self) -> List[AgentTask]:
        """Get unique tasks from all agents (excludes internal tasks)."""
        seen, tasks = set(), []
        for agent in [self._writer, self._designer]:
            for task in agent.get_supported_tasks():
                if task.task_id not in seen and task.content_types:
                    tasks.append(task)
                    seen.add(task.task_id)
        return tasks

    def get_all_content_types(self) -> Dict[str, List[str]]:
        """Get all content types grouped by task_id."""
        result = {}
        for task in self.get_supported_tasks():
            result[task.task_id] = task.content_types
        return result

    def get_task_for_content_type(self, content_type: str) -> Optional[AgentTask]:
        """Find task that handles this content type."""
        return self._content_type_to_task.get(content_type)

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Route task to agent by task_id."""
        agent = self._task_to_agent.get(task.task_id)
        if not agent:
            return {"error": f"No agent for task: {task.task_id}", "status": "failed"}

        logger.info(f"Routing '{task.task_id}' to {agent.agent_id}")
        result = await agent.process_task(task, task.parameters)
        return {
            "task_id": task.task_id,
            "content": result,
            "agent_used": agent.agent_id,
            "status": "completed",
        }

    async def generate_content(
        self, content_type: str, topic: str, **params
    ) -> Dict[str, Any]:
        """Generate content by content_type alias."""
        template = self.get_task_for_content_type(content_type)
        if not template:
            return {
                "error": f"Unknown content type: {content_type}",
                "status": "failed",
            }

        task = AgentTask(
            task_id=template.task_id,
            agent_role=template.agent_role,
            prompt=template.prompt,
            parameters={**(template.parameters or {}), "topic": topic, **params},
            content_types=template.content_types,
            output_key=template.output_key,
        )
        return await self.process_task(task, task.parameters)

    # Convenience accessors for tests
    @property
    def quiz_agent(self):
        return self._writer

    @property
    def story_agent(self):
        return self._writer

    @property
    def game_agent(self):
        return self._designer

    @property
    def simulation_agent(self):
        return self._designer


__all__ = ["CoordinatorAgent"]
