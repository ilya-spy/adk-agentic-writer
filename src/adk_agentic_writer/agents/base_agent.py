"""Base agent class - single source of truth for all agents.

Both static/ and gemini/ agents inherit from this base class.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ..models.agent_models import AgentConfig, AgentModel, AgentTask

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all agents.

    Stores:
    - id: Agent identifier
    - config: AgentConfig (role, instruction, temperature, prompts)
    - model: AgentModel (name, tools, parameters, workflows, teams)
    - _supported_tasks: List of tasks this agent can handle

    Provides prompt building methods that operate on config data.
    Subclasses (StatefulAgent) add runtime state management.
    """

    def __init__(
        self,
        agent_id: str,
        config: AgentConfig,
        model: AgentModel,
    ) -> None:
        """Initialize base agent.

        Args:
            agent_id: Unique identifier
            config: Agent configuration (role, instruction, prompts)
            model: Agent model (tools, workflows, teams)
        """
        self.id = agent_id
        self.config = config
        self.model = model
        self.supported_tasks: List[AgentTask] = []

        logger.info(f"Initialized BaseAgent {agent_id} with role {config.role}")

    @property
    def agent_id(self) -> str:
        """Backward-compatible alias for id."""
        return self.id

    @property
    def agent_config(self) -> AgentConfig:
        """Backward-compatible alias for config."""
        return self.config

    @property
    def parameters(self) -> Dict[str, Any]:
        """Get parameters from model."""
        return self.model.parameters

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get a parameter value."""
        return self.parameters.get(key, default)

    def update_parameters(self, updates: Dict[str, Any]) -> None:
        """Update parameters."""
        self.model.parameters.update(updates)
        logger.debug(f"Agent {self.id} updated {len(updates)} parameters")

    # =========================================================================
    # Prompt Building Methods
    # =========================================================================
    def get_prompt(self, key: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Get a prompt template from config with variable substitution.

        Args:
            key: Prompt template key (e.g., 'quiz_question', 'story_opening')
            context: Variables for substitution

        Returns:
            Formatted prompt string
        """
        template = self.config.prompt_templates.get(key, "")
        if not template:
            return ""

        full_context = {**self.parameters}
        if context:
            full_context.update(context)

        try:
            return template.format(**full_context)
        except KeyError:
            return template

    def build_generation_prompt(
        self,
        context: Optional[Dict[str, Any]] = None,
        schema_description: str = "",
        sample_output: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build the full generation prompt with optional schema.

        Uses config.generation_prompt as base template.
        Appends schema_description and sample_output if provided.

        Args:
            context: Variables for substitution
            schema_description: JSON schema description (from content registry)
            sample_output: Sample output dict for model guidance

        Returns:
            Complete generation prompt
        """
        full_context = {**self.parameters}
        if context:
            full_context.update(context)

        try:
            prompt = self.config.generation_prompt.format(**full_context)
        except KeyError:
            prompt = self.config.generation_prompt

        if schema_description:
            prompt += f"\n\n{schema_description}"

        if sample_output:
            prompt += f"\n\nExample output:\n{json.dumps(sample_output, indent=2)}"

        return prompt

    def apply_prompt_modifiers(
        self, prompt: str, modifiers: Optional[List[str]] = None
    ) -> str:
        """Apply modifiers from config to a prompt.

        Args:
            prompt: Base prompt
            modifiers: List of modifier keys to apply

        Returns:
            Prompt with modifiers applied
        """
        if not modifiers:
            return prompt

        parts = [prompt]
        for mod_key in modifiers:
            if mod_key in self.config.prompt_modifiers:
                parts.append(self.config.prompt_modifiers[mod_key])
        return "\n".join(parts)

    def get_supported_tasks(self) -> List[AgentTask]:
        """Get list of tasks this agent can handle.

        Subclasses should override to publish their capabilities.
        """
        return self.supported_tasks

    def supports_task(self, task_id: str) -> bool:
        """Check if agent supports a specific task."""
        return any(t.task_id == task_id for t in self.get_supported_tasks())

    def get_task_by_id(self, task_id: str) -> Optional[AgentTask]:
        """Get task template by ID."""
        for task in self.get_supported_tasks():
            if task.task_id == task_id:
                return task
        return None

    async def receive_message(
        self, message: str, sender: str, data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Receive a message from another agent."""
        logger.info(f"Agent {self.id} received message from {sender}: {message}")
        return None


__all__ = ["BaseAgent"]
