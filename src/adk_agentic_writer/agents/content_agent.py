"""Base class for content-generating agents.

ContentWriterAgent is the base class for all agents that generate content
(quiz, story, game, simulation). It provides:

1. TextProvider integration for text generation
2. Unified task execution flow: generate() → process_task() → _build_content()
3. Inherits state management from StatefulAgent

Inheritance hierarchy:
    BaseAgent → StatefulAgent → ContentWriterAgent → WriterAgent/DesignerAgent

Call flow:
    agent.generate(**kwargs)
        → process_task(task)          [from StatefulAgent]
            → _execute_task(task)     [overridden here]
                → _build_content(ctx) [implemented by subclass]
"""

import logging
from typing import Any, Dict, Optional

from ..models.agent_models import AgentConfig, AgentTask
from ..utils.text_provider import TextProvider, TemplateTextProvider
from .stateful_agent import StatefulAgent

logger = logging.getLogger(__name__)


class ContentWriterAgent(StatefulAgent):
    """Base class for content-generating agents.

    Provides:
    - TextProvider integration for text generation
    - Unified generate() convenience method
    - _execute_task() that calls _build_content()

    Subclasses must implement:
    - _build_content(context) → Dict: Build content from context
    """

    def __init__(
        self,
        agent_id: str,
        config: AgentConfig,
        text_provider: Optional[TextProvider] = None,
    ):
        """Initialize content agent.

        Args:
            agent_id: Unique agent identifier
            config: Agent configuration
            text_provider: Text generation provider (defaults to TemplateTextProvider)
        """
        super().__init__(agent_id=agent_id, config=config)
        self.text_provider = text_provider or TemplateTextProvider()
        logger.info(
            f"Initialized ContentWriterAgent {agent_id} with {type(self.text_provider).__name__}"
        )

    async def _generate_text(
        self, prompt_key: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate text using the text provider.

        Args:
            prompt_key: Key identifying text type (quiz_question, story_opening, etc.)
            context: Optional context variables (merged with parameters)

        Returns:
            Generated text string
        """
        full_context = {**self.parameters}
        if context:
            full_context.update(context)
        return await self.text_provider.generate_text(prompt_key, full_context)

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute task by building content.

        This is called by StatefulAgent.process_task().
        Routes to _build_content() which subclasses implement.

        Args:
            task: Task to execute
            resolved_prompt: Prompt with variables substituted

        Returns:
            Generated content dictionary
        """
        context = self.prepare_task_context(task)
        return await self._build_content(context)

    async def _build_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build content based on context.

        Subclasses must implement this method.

        Args:
            context: Merged parameters and task variables

        Returns:
            Content dictionary (Quiz, Story, Game, or Simulation)
        """
        raise NotImplementedError("Subclasses must implement _build_content()")

    async def generate(self, **kwargs) -> Dict[str, Any]:
        """Convenience method for direct content generation.

        This is the main public API for generating content.

        Args:
            **kwargs: Parameters for content generation (topic, num_questions, etc.)

        Returns:
            Generated content dictionary
        """
        self.update_parameters(kwargs)

        task = AgentTask(
            task_id="generate",
            agent_role=self.agent_config.role,
            prompt="Generate content about {topic}",
            parameters=kwargs,
            output_key="content",
        )

        return await self.process_task(task, kwargs)


__all__ = ["ContentWriterAgent"]
