"""Stateful agent with variable and parameter management.

StatefulAgent maintains runtime state including variables and parameters,
and can execute tasks using predefined workflows and teams.
"""

import logging
from typing import Any, Dict, List, Optional

from ..models.agent_models import (
    AgentConfig,
    AgentRole,
    AgentState,
    AgentStatus,
    AgentTask,
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
        workflows: Optional[List[WorkflowMetadata]] = None,
    ):
        """Initialize stateful agent.

        Args:
            agent_id: Unique identifier for this agent
            config: Agent configuration with role, instructions, etc.
            workflows: Available workflows this agent can execute
        """
        # Initialize base agent
        super().__init__(
            agent_id=agent_id,
            role=(
                config.role if isinstance(config.role, AgentRole) else AgentRole.WRITER
            ),
            config=config.model_dump(),
        )

        # Store configuration
        self.agent_config = config
        self.workflows = (
            workflows.append(config.workflows) if workflows else config.workflows or []
        )

        # Initialize stateful storage
        self.state.variables = {}  # Runtime variables (content_block, feedback, etc.)
        self.state.metadata["parameters"] = {}  # Configuration parameters

        logger.info(
            f"Initialized StatefulAgent {agent_id} with role {config.role} "
            f"and {len(self.workflows)} workflows"
        )

    @property
    def variables(self) -> Dict[str, Any]:
        """Get runtime variables dict."""
        return self.state.variables

    @variables.setter
    def variables(self, value: Dict[str, Any]) -> None:
        """Set runtime variables dict."""
        self.state.variables = value

    @property
    def parameters(self) -> Dict[str, Any]:
        """Get configuration parameters dict."""
        return self.state.metadata.get("parameters", {})

    @parameters.setter
    def parameters(self, value: Dict[str, Any]) -> None:
        """Set configuration parameters dict."""
        self.state.metadata["parameters"] = value

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

    def set_parameter(self, key: str, value: Any) -> None:
        """Set a configuration parameter.

        Args:
            key: Parameter name
            value: Parameter value
        """
        params = self.state.metadata.get("parameters", {})
        params[key] = value
        self.state.metadata["parameters"] = params
        logger.debug(f"Agent {self.agent_id} set parameter '{key}'")

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get a configuration parameter.

        Args:
            key: Parameter name
            default: Default value if not found

        Returns:
            Parameter value or default
        """
        return self.parameters.get(key, default)

    def update_variables(self, updates: Dict[str, Any]) -> None:
        """Update multiple variables at once.

        Args:
            updates: Dictionary of variable updates
        """
        self.state.variables.update(updates)
        logger.debug(f"Agent {self.agent_id} updated {len(updates)} variables")

    def update_parameters(self, updates: Dict[str, Any]) -> None:
        """Update multiple parameters at once.

        Args:
            updates: Dictionary of parameter updates
        """
        params = self.state.metadata.get("parameters", {})
        params.update(updates)
        self.state.metadata["parameters"] = params
        logger.debug(f"Agent {self.agent_id} updated {len(updates)} parameters")

    def clear_variables(self) -> None:
        """Clear all runtime variables."""
        self.state.variables.clear()
        logger.debug(f"Agent {self.agent_id} cleared all variables")

    def prepare_task_context(self, task: AgentTask) -> Dict[str, Any]:
        """Prepare context for task execution by merging variables and parameters.

        Args:
            task: Task to prepare context for

        Returns:
            Merged context dictionary with precedence: parameters < variables < task.parameters
        """
        # Start with parameters (configuration)
        context = {**self.parameters}
        # Add variables (runtime state takes precedence over config parameters)
        context.update(self.variables)
        # Task parameters override everything
        if task.parameters:
            context.update(task.parameters)

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

        Implements AgentProtocol.

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

    def get_workflow(self, name: str) -> Optional[WorkflowMetadata]:
        """Get workflow by name.

        Args:
            name: Workflow name

        Returns:
            Workflow metadata or None
        """
        for workflow in self.workflows:
            if workflow.name == name:
                return workflow
        return None

    def list_workflows(self) -> List[str]:
        """List available workflow names.

        Returns:
            List of workflow names
        """
        return [w.name for w in self.workflows]


__all__ = ["StatefulAgent"]
