"""Stateful agent with variable and parameter management.

StatefulAgent maintains runtime state including variables and parameters,
and can execute tasks using predefined workflows and teams.
"""

import logging
from typing import Any, Dict, List, Optional

from ..models.agent_models import (
    AgentConfig,
    AgentModel,
    AgentRole,
    AgentState,
    AgentStatus,
    AgentTask,
    TeamMetadata,
    WorkflowMetadata,
)
from ..utils.variable_substitution import substitute_variables, validate_variables
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class StatefulAgent(BaseAgent):
    """Agent with stateful variable and parameter management.

    Features:
    - Maintains variables dict for data flow between tasks
    - Maintains parameters dict for configuration
    - Executes tasks with variable substitution
    - Supports workflow-based orchestration
    - Integrates with teams for collaborative work

    Variables vs Parameters:
    - Variables: Runtime data that flows between tasks (content_block, feedback, etc.)
    - Parameters: Configuration values (topic, num_questions, difficulty, etc.)
    """

    def __init__(
        self,
        agent_id: str,
        config: AgentConfig,
        model: AgentModel,
    ):
        """Initialize stateful agent.

        Args:
            agent_id: Unique identifier for this agent
            config: Agent configuration with role, instructions, etc.
            model: Agent model, tools and workflows to use
        """
        # Initialize base agent
        super().__init__(
            agent_id=agent_id,
            config=config,
            model=model,
        )

        self.state = AgentState(
            agent_id=agent_id,
            status=AgentStatus.IDLE,
        )

        logger.info(
            f"Initialized StatefulAgent {agent_id} with role {config.role} "
            f"and {len(model.workflows)} workflows"
        )

    @property
    def variables(self) -> Dict[str, Any]:
        """Get runtime variables dict."""
        return self.state.variables

    @variables.setter
    def variables(self, value: Dict[str, Any]) -> None:
        """Set runtime variables dict."""
        self.state.variables = value

    def set_variable(self, key: str, value: Any) -> None:
        """Set a runtime variable.

        Args:
            key: Variable name
            value: Variable value
        """
        self.state.variables[key] = value
        logger.debug(f"Agent {self.agent_id} set variable '{key}'")

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a runtime variable.

        Args:
            key: Variable name
            default: Default value if not found

        Returns:
            Variable value or default
        """
        return self.state.variables.get(key, default)

    def update_variables(self, updates: Dict[str, Any]) -> None:
        """Update multiple variables at once.

        Args:
            updates: Dictionary of variable updates
        """
        self.state.variables.update(updates)
        logger.debug(f"Agent {self.agent_id} updated {len(updates)} variables")

    def clear_variables(self) -> None:
        """Clear all runtime variables."""
        self.state.variables.clear()
        logger.debug(f"Agent {self.agent_id} cleared all variables")

    async def update_status(self, status: AgentStatus) -> None:
        """Update agent status."""
        self.state.status = status
        logger.debug(f"Agent {self.agent_id} status: {status}")

    # ------------------------------------------------------------------
    # Task & workflow discovery
    # ------------------------------------------------------------------

    def get_supported_tasks(self) -> List[AgentTask]:
        """Get tasks from model.tasks plus tasks referenced by workflows.

        Subclasses may override to add tasks from child agents, but
        should call super() to include workflow-sourced tasks.
        """
        seen: set[str] = set()
        tasks: List[AgentTask] = []
        # Tasks explicitly registered on the agent
        for t in super().get_supported_tasks():
            if t.task_id not in seen:
                tasks.append(t)
                seen.add(t.task_id)
        # Tasks referenced by registered workflows
        for wf in self.model.workflows:
            for t in getattr(wf, "tasks", []):
                if t is not None and t.task_id not in seen:
                    tasks.append(t)
                    seen.add(t.task_id)
        return tasks

    def get_task_for_content_type(self, content_type: str) -> Optional[AgentTask]:
        """Find task that handles a content_type alias."""
        for task in self.get_supported_tasks():
            if content_type in (task.content_types or []):
                return task
        return None

    def get_all_content_types(self) -> Dict[str, List[str]]:
        """Get all content types grouped by task_id."""
        result: Dict[str, List[str]] = {}
        for task in self.get_supported_tasks():
            if task.content_types:
                result[task.task_id] = task.content_types
        return result

    def resolve_task(
        self,
        task_id: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Optional[AgentTask]:
        """Resolve a task by task_id or content_type alias.

        task_id takes priority over content_type.
        Returns the task template or None.
        """
        if task_id:
            return self.get_task_by_id(task_id)
        if content_type:
            return self.get_task_for_content_type(content_type)
        return None

    def get_supported_workflows(self) -> List[Any]:
        """Get all workflows registered in model.workflows."""
        return list(self.model.workflows)

    def resolve_workflow(
        self,
        task_id: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Optional[Any]:
        """Resolve a single workflow by task_id or content_type.

        Searches model.workflows for the first workflow whose tasks
        list contains a matching task.

        Args:
            task_id: Match workflow containing a task with this task_id.
            content_type: Match workflow containing a task whose
                          content_types includes this alias.

        Returns:
            First matching Workflow, or None.
        """
        for wf in self.model.workflows:
            for t in getattr(wf, "tasks", []):
                if t is None:
                    continue
                if task_id and t.task_id == task_id:
                    return wf
                if content_type and content_type in (t.content_types or []):
                    return wf
        return None

    # ------------------------------------------------------------------
    # Task context and execution
    # ------------------------------------------------------------------

    def prepare_task_context(self, task: AgentTask) -> Dict[str, Any]:
        """Prepare context for task execution.

        Merge order (last wins):
        1. state.variables  – inter-task data flow (lowest priority)
        2. task.parameters  – template defaults
        3. model.parameters – runtime params from caller (highest priority)
        4. task_id injected for content-type routing
        """
        context: Dict[str, Any] = {}
        context.update(self.state.variables)
        if task.parameters:
            context.update(task.parameters)
        context.update(self.model.parameters)
        context["task_id"] = task.task_id
        return context

    def substitute_task_prompt(self, task: AgentTask) -> str:
        """Substitute variables in task prompt.

        Args:
            task: Task with prompt containing {variable} placeholders

        Returns:
            Prompt with variables substituted
        """
        context = self.prepare_task_context(task)
        return substitute_variables(task.prompt, context)

    def validate_task_requirements(self, task: AgentTask) -> tuple[bool, List[str]]:
        """Validate that task has all required variables.

        Args:
            task: Task to validate

        Returns:
            Tuple of (is_valid, missing_variables)
        """
        context = self.prepare_task_context(task)
        return validate_variables(task.prompt, context)

    async def process_task(
        self, task: AgentTask, parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a task with variable substitution and state management.

        Core task execution entry point.

        Args:
            task: Task to process
            parameters: Optional additional parameters

        Returns:
            Task result dictionary
        """
        await self.update_status(AgentStatus.WORKING)
        self.state.current_task = task.task_id

        # Update parameters if provided
        if parameters:
            self.update_parameters(parameters)

        # Validate task requirements
        is_valid, missing = self.validate_task_requirements(task)
        if not is_valid:
            logger.warning(
                f"Task {task.task_id} missing variables: {missing}. "
                "Proceeding with available context."
            )

        # Substitute variables in prompt
        resolved_prompt = self.substitute_task_prompt(task)
        logger.info(f"Agent {self.agent_id} processing task: {task.task_id}")
        logger.debug(f"Resolved prompt: {resolved_prompt[:100]}...")

        # Execute task (subclasses override this)
        result = await self._execute_task(task, resolved_prompt)

        # Store result in variables if output_key specified
        if task.output_key:
            self.set_variable(task.output_key, result)

        # Mark task as completed
        self.state.completed_tasks.append(task.task_id)
        self.state.current_task = None
        await self.update_status(AgentStatus.COMPLETED)

        return result

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute the actual task logic.

        Subclasses should override this method to implement specific behavior.

        Args:
            task: Task to execute
            resolved_prompt: Prompt with variables substituted

        Returns:
            Task result
        """
        # Default implementation - subclasses override
        logger.warning(
            f"Agent {self.agent_id} using default _execute_task. "
            "Subclasses should override this method."
        )
        return {
            "task_id": task.task_id,
            "prompt": resolved_prompt,
            "status": "completed",
        }


__all__ = ["StatefulAgent"]
