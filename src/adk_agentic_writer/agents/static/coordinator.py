"""Static coordinator agent for orchestrating content generation.

Coordinates unified WriterAgent and DesignerAgent for content generation.
Uses ContentRegistry for extensible content type support.
"""

import logging
from typing import Any, Dict, Optional

from ...models.agent_models import AgentConfig, AgentModel, AgentRole, AgentTask
from ...teams.content_team import CONTENT_WRITER, ContentRole
from ..stateful_agent import StatefulAgent
from ...utils.content_registry import CONTENT_REGISTRY
from .writer import WriterAgent
from .designer import DesignerAgent

logger = logging.getLogger(__name__)


class CoordinatorAgent(StatefulAgent):
    """Static coordinator for content generation.

    Uses unified WriterAgent and DesignerAgent with ContentRegistry
    for extensible content type support.
    """

    def __init__(self, agent_id: str = "static_coordinator"):
        """Initialize coordinator with unified agents."""
        model = AgentModel(name=agent_id)
        super().__init__(agent_id=agent_id, config=CONTENT_WRITER, model=model)

        # Unified agents - one per category
        self._writer = WriterAgent("writer")
        self._designer = DesignerAgent("designer")

        # Cache for content-type-specific agent instances
        self._agents: Dict[str, Any] = {}

        logger.info(f"Initialized CoordinatorAgent {agent_id}")

    # Agent properties
    @property
    def quiz_agent(self):
        return self._get_agent_for_type("quiz")

    @property
    def story_agent(self):
        return self._get_agent_for_type("story")

    @property
    def game_agent(self):
        return self._get_agent_for_type("game")

    @property
    def simulation_agent(self):
        return self._get_agent_for_type("simulation")

    @property
    def agent_registry(self) -> Dict[str, Any]:
        """Get agent registry."""
        return {
            ContentRole.QUIZ_WRITER.value: self.quiz_agent,
            ContentRole.STORY_WRITER.value: self.story_agent,
            ContentRole.GAME_WRITER.value: self.game_agent,
            ContentRole.SIMULATION_WRITER.value: self.simulation_agent,
        }

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute coordinator task."""
        context = self.prepare_task_context(task)
        content_type = context.get("content_type", "quiz")

        logger.info(f"Coordinator routing to {content_type} agent")

        return await self._generate_content(content_type, context)

    async def _generate_content(
        self, content_type: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate content using appropriate agent."""
        agent = self._get_agent_for_type(content_type)
        if not agent:
            return {"error": f"Unknown content type: {content_type}"}

        gen_task = AgentTask(
            task_id="generate",
            agent_role=AgentRole.WRITER,
            prompt=f"Generate {content_type} about {{topic}}",
            parameters=context,
            output_key="content",
        )

        result = await agent.process_task(gen_task, context)

        return {
            "content_type": content_type,
            "content": result,
            "agent_used": agent.agent_id,
            "status": "completed",
        }

    async def generate_content(
        self, content_type: str, topic: str, **parameters
    ) -> Dict[str, Any]:
        """Public API for content generation."""
        context = {"topic": topic, "content_type": content_type, **parameters}
        return await self._generate_content(content_type, context)

    def _get_agent_for_type(self, content_type: str) -> Optional[Any]:
        """Get or create agent for content type using registry."""
        content_type = content_type.lower().replace(" ", "_")

        if content_type in self._agents:
            return self._agents[content_type]

        config = CONTENT_REGISTRY.get(content_type)
        if not config:
            return None

        if config.category == "writer":
            agent = WriterAgent(
                agent_id=f"{content_type}_writer",
                content_type=content_type,
            )
        else:
            agent = DesignerAgent(
                agent_id=f"{content_type}_designer",
                content_type=content_type,
            )

        self._agents[content_type] = agent
        return agent

    def get_supported_content_types(self) -> list:
        """Get list of supported content types from registry."""
        return CONTENT_REGISTRY.list_types()


__all__ = ["CoordinatorAgent"]
