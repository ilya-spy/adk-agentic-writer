"""Base class for content-generating agents.

Inheritance: BaseAgent → StatefulAgent → ContentWriterAgent → WriterAgent/DesignerAgent

Call flow:
    agent.generate(**kwargs)
        → process_task(task)          [StatefulAgent]
            → _execute_task(task)     [ContentWriterAgent]
                → _build_content(ctx) [WriterAgent/DesignerAgent]
"""

import logging
from typing import Any, Dict, Optional

from ..models.agent_models import AgentConfig, AgentModel, AgentTask
from ..utils.text_provider import TextProvider, TemplateTextProvider
from .stateful_agent import StatefulAgent

logger = logging.getLogger(__name__)


class ContentWriterAgent(StatefulAgent):
    """Base class for content-generating agents.

    Adds TextProvider integration to StatefulAgent.
    Subclasses implement _build_content().
    """

    def __init__(
        self,
        agent_id: str,
        config: AgentConfig,
        model: Optional[AgentModel] = None,
        text_provider: Optional[TextProvider] = None,
    ):
        """Initialize content agent.

        Args:
            agent_id: Unique agent identifier
            config: Agent configuration (role, instruction)
            model: Agent model (tools, workflows, teams)
            text_provider: Text generation provider
        """
        # Create default model if not provided
        if model is None:
            model = AgentModel(name=agent_id)

        super().__init__(agent_id=agent_id, config=config, model=model)
        self.text_provider = text_provider or TemplateTextProvider()

        logger.info(
            f"Initialized ContentWriterAgent {agent_id} "
            f"with {type(self.text_provider).__name__}"
        )

    async def _generate_text(
        self, prompt_key: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate text using the text provider."""
        full_context = {**self.parameters}
        if context:
            full_context.update(context)
        return await self.text_provider.generate_text(prompt_key, full_context)

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute task by calling _build_content()."""
        context = self.prepare_task_context(task)
        return await self._build_content(context)

    async def _build_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build content. Subclasses must implement."""
        raise NotImplementedError("Subclasses must implement _build_content()")

    async def generate(self, **kwargs) -> Dict[str, Any]:
        """Main API for content generation."""
        self.update_parameters(kwargs)

        task = AgentTask(
            task_id="generate",
            agent_role=self.config.role,
            prompt="Generate content about {topic}",
            parameters=kwargs,
            output_key="content",
        )

        return await self.process_task(task, kwargs)


__all__ = ["ContentWriterAgent"]
