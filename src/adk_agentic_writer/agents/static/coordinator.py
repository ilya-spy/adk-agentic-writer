"""Coordinator routes tasks to content agents.

Discovers tasks from agents and builds content_type -> task mapping dynamically.
Runs a writer → validator workflow for single-pass result validation.
Supports both ad-hoc validation (in _execute_task) and formal
ValidationEditorialWorkflow via generate_with_validation().
"""

import logging
from typing import Any, Dict, List, Optional

from ...models.agent_models import AgentModel, AgentTask
from ...teams.content_team import CONTENT_WRITER
from ...teams.editorial_team import VALIDATION_TEAM
from ...workflows.editorial_workflows import ValidationEditorialWorkflow
from ..stateful_agent import StatefulAgent
from .validator import ContentValidator
from .designer import DesignerAgent
from .writer import WriterAgent

logger = logging.getLogger(__name__)


class CoordinatorAgent(StatefulAgent):
    """Coordinator aggregates tasks from agents. Routes by task_id or content_type.

    Holds a ContentValidator reference and runs writer → validator workflow.
    Provides:
    - generate_content(): single-pass generation with inline validation
    - generate_with_validation(): formal ValidationEditorialWorkflow execution
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

        # Build content_type -> task mapping from task.content_types
        self._content_type_to_task: Dict[str, AgentTask] = {}
        for task in self.get_supported_tasks():
            for ct in task.content_types:
                self._content_type_to_task[ct] = task

        # Build validation workflow from current agents
        self._build_validation_workflow()

        logger.info(
            f"Coordinator: {len(self._task_to_agent)} tasks, "
            f"{len(self._content_type_to_task)} content types, "
            f"workflow ready"
        )

    # ------------------------------------------------------------------
    # Validation workflow setup (reusable by subclasses)
    # ------------------------------------------------------------------

    def _build_validation_workflow(self) -> None:
        """Build validation team + workflow from current _writer/_validator.

        Creates a VALIDATION_TEAM with agent IDs and a
        ValidationEditorialWorkflow, then registers both in
        model.teams/workflows and state.teams/workflows.

        Safe to call again after replacing agents (e.g. Gemini subclass).
        """
        validation_team = VALIDATION_TEAM.model_copy(
            update={
                "agent_ids": [self._writer.agent_id, self._validator.agent_id],
            }
        )

        self.validation_workflow = ValidationEditorialWorkflow(
            name="generate_validate",
            stages=[self._writer, self._validator],
        )

        self.model.teams = [validation_team]
        self.model.workflows = [self.validation_workflow]
        self.state.teams = list(self.model.teams)
        self.state.workflows = list(self.model.workflows)

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

    @staticmethod
    def _infer_content_type(task: AgentTask) -> str:
        """Infer content_type from task parameters or task_id."""
        ct = (task.parameters or {}).get("content_type")
        if ct:
            return ct
        tid = task.task_id
        if "quiz" in tid:
            return "quiz"
        if "story" in tid:
            return "story"
        if "game" in tid:
            return "quest_game"
        if "simulation" in tid:
            return "web_simulation"
        return ""

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Route task to agent, then validate (writer → validator)."""
        agent = self._task_to_agent.get(task.task_id)
        if not agent:
            return {"error": f"No agent for task: {task.task_id}", "status": "failed"}

        logger.info(f"Routing '{task.task_id}' to {agent.agent_id}")
        result = await agent.process_task(task, task.parameters)

        # Writer → Validator workflow
        content_type = self._infer_content_type(task)
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

    def _build_task(
        self, content_type: str, topic: str, **params
    ) -> Optional[AgentTask]:
        """Build an AgentTask from content_type alias. Returns None if unknown."""
        template = self.get_task_for_content_type(content_type)
        if not template:
            return None
        return AgentTask(
            task_id=template.task_id,
            agent_role=template.agent_role,
            prompt=template.prompt,
            parameters={
                **(template.parameters or {}),
                "topic": topic,
                "content_type": content_type,
                **params,
            },
            content_types=template.content_types,
            output_key=template.output_key,
        )

    async def generate_content(
        self, content_type: str, topic: str, **params
    ) -> Dict[str, Any]:
        """Generate content by content_type alias."""
        task = self._build_task(content_type, topic, **params)
        if not task:
            return {
                "error": f"Unknown content type: {content_type}",
                "status": "failed",
            }
        return await self.process_task(task, task.parameters)

    async def generate_with_validation(
        self, content_type: str, topic: str, **params
    ) -> Dict[str, Any]:
        """Generate content with ValidationEditorialWorkflow.

        Runs writer → validator sequentially.  Each agent stores its
        result in state.variables via its task's output_key:
          - writer  → state.variables["content"]
          - validator → state.variables["validation_result"]

        After execution, both are propagated to coordinator state and
        returned as a JSON dict.
        """
        task = self._build_task(content_type, topic, **params)
        if not task:
            return {
                "error": f"Unknown content type: {content_type}",
                "status": "failed",
            }

        logger.info(
            "Running validation workflow for %s (topic=%s)", content_type, topic
        )
        await self.validation_workflow.execute(
            {
                "task": task,
                "parameters": task.parameters or {},
            }
        )

        # Read results from agent states (set by task output_key)
        content = self._writer.state.variables.get("content")
        validation_result = self._validator.state.variables.get("validation_result")

        # Propagate to coordinator state for runtime access
        self.set_variable("content", content)
        self.set_variable("validation_result", validation_result)

        return {
            "content": content,
            "validation_result": validation_result,
            "status": "validated",
        }

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
