"""Coordinator routes tasks to content agents.

Discovers tasks from agents and builds content_type -> task mapping dynamically.
Publishes tasks via get_supported_tasks() and workflows via get_supported_workflows().

API callers use resolve_task() / resolve_workflow() to find and execute.
"""

import logging
from typing import Any, Dict, List

from ...models.agent_models import AgentModel, AgentTask
from ...teams.content_team import CONTENT_WRITER
from ...teams.editorial_team import VALIDATION_TEAM
from ...workflows.editorial_workflows import ValidationEditorialWorkflow
from ..stateful_agent import StatefulAgent
from .validator import ContentValidator
from .designer import DesignerAgent
from .writer import WriterAgent
from ...tasks import editorial_tasks

logger = logging.getLogger(__name__)


class CoordinatorAgent(StatefulAgent):
    """Coordinator aggregates tasks from agents. Routes by task_id or content_type.

    Discovery API (for callers):
    - get_supported_tasks() -> list of AgentTask templates
    - resolve_workflow(task_id, content_type) -> single Workflow (inherited)
    - resolve_task(task_id, content_type) -> AgentTask template
    - process_task(task, params) -> result dict
    """

    def __init__(self, agent_id: str = "static_coordinator"):
        model = AgentModel(name=agent_id)
        super().__init__(agent_id=agent_id, config=CONTENT_WRITER, model=model)

        # Validator (shared across all content types)
        self._validator = ContentValidator(f"{agent_id}_validator")

        # Create one writer and one designer
        self._writer = WriterAgent("writer", "quiz")
        self._designer = DesignerAgent("designer", "quest_game")

        # Build task_id -> agent mapping
        self._task_to_agent: Dict[str, Any] = {}
        for agent in [self._writer, self._designer]:
            for task in agent.get_supported_tasks():
                self._task_to_agent[task.task_id] = agent

        # Build validation workflow from current agents
        self._build_validation_workflow()

        all_ct = sum(len(v) for v in self.get_all_content_types().values())
        logger.info(
            f"Coordinator: {len(self._task_to_agent)} tasks, "
            f"{all_ct} content types, workflow ready"
        )

    # ------------------------------------------------------------------
    # Validation workflow setup (reusable by subclasses)
    # ------------------------------------------------------------------

    def _build_validation_workflow(self) -> None:
        """Build validation team + workflow from current _writer/_validator.

        Creates a VALIDATION_TEAM with agent IDs and a
        ValidationEditorialWorkflow, then registers both in
        model.teams and model.workflows (single source of truth).

        Default tasks: [None, VALIDATE_CONTENT].
        None for writer = filled at runtime from input_data["tasks"].

        Safe to call again after replacing agents (e.g. Gemini subclass).
        """
        validation_team = VALIDATION_TEAM.model_copy(
            update={
                "agent_ids": [self._writer.agent_id, self._validator.agent_id],
            }
        )

        workflow = ValidationEditorialWorkflow(
            name="generate_then_validate",
            agents=[self._writer, self._validator],
        )

        self.model.teams = [validation_team]
        self.model.workflows = [workflow]

    def get_supported_tasks(self) -> List[AgentTask]:
        """Aggregate tasks from child agents + workflow-sourced tasks (via super)."""
        seen, tasks = set(), []
        # Content-specific tasks from child agents
        for agent in [self._writer, self._designer]:
            for task in agent.get_supported_tasks():
                if task.task_id not in seen and task.content_types:
                    tasks.append(task)
                    seen.add(task.task_id)
        # Workflow-sourced tasks (from StatefulAgent base)
        for task in super().get_supported_tasks():
            if task.task_id not in seen:
                tasks.append(task)
                seen.add(task.task_id)
        return tasks

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Route task to the appropriate agent, then validate.

        Forwards coordinator's model.parameters (which include caller
        overrides from process_task) to the agent, so runtime params
        take precedence over task template defaults.
        """
        agent = self._task_to_agent.get(task.task_id)
        if not agent:
            return {"error": f"No agent for task: {task.task_id}", "status": "failed"}

        logger.info(f"Routing '{task.task_id}' to {agent.agent_id}")
        result = await agent.process_task(task, self.model.parameters)

        # Inline validation using first content_type alias from the task
        content_type = task.content_types[0] if task.content_types else ""
        if content_type and self._validator:
            warnings = self._validator.validate(result, content_type)
            if warnings:
                logger.info(
                    "Validator: %d warning(s) for %s", len(warnings), content_type
                )

        return {
            "task_id": task.task_id,
            "content": result,
            "agent_used": agent.agent_id,
            "status": "completed",
        }

    # ------------------------------------------------------------------
    # Convenience wrappers (backward compat for tests/examples)
    # ------------------------------------------------------------------

    async def generate_content(
        self, content_type: str, topic: str, **params
    ) -> Dict[str, Any]:
        """Convenience: resolve task from content_type alias and execute.

        Prefer using resolve_task() + process_task() directly in new code.
        """
        task = self.get_task_for_content_type(content_type)
        if not task:
            return {
                "error": f"Unknown content type: {content_type}",
                "status": "failed",
            }
        return await self.process_task(task, {"topic": topic, **params})

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
