"""Static coordinator agent for orchestrating content generation.

Coordinates specialized agents for content generation.
Inherits from StatefulAgent for unified structure.
"""

import logging
from typing import Any, Dict, List, Optional

from ...models.agent_models import AgentConfig, AgentRole, AgentTask
from ...teams.content_team import CONTENT_WRITER, ContentRole
from ..stateful_agent import StatefulAgent
from .game_designer import GameDesignerAgent
from .quiz_writer import StaticQuizWriterAgent
from .reviewer import ReviewerAgent
from .simulation_designer import SimulationDesignerAgent
from .story_writer import StoryWriterAgent

logger = logging.getLogger(__name__)

# Content type to agent mapping
CONTENT_TYPE_MAP = {
    "quiz": StaticQuizWriterAgent,
    "story": StoryWriterAgent,
    "branched_narrative": StoryWriterAgent,
    "game": GameDesignerAgent,
    "quest_game": GameDesignerAgent,
    "simulation": SimulationDesignerAgent,
    "web_simulation": SimulationDesignerAgent,
}


class CoordinatorAgent(StatefulAgent):
    """Static coordinator for content generation.

    Provides:
    - Task routing to specialized agents
    - Content generation coordination
    - Simple workflow support
    """

    def __init__(self, agent_id: str = "static_coordinator"):
        """Initialize coordinator with specialized agents.

        Args:
            agent_id: Unique agent identifier
        """
        super().__init__(agent_id=agent_id, config=CONTENT_WRITER)

        # Initialize specialized agents
        self.quiz_agent = StaticQuizWriterAgent("quiz_writer")
        self.story_agent = StoryWriterAgent("story_writer")
        self.game_agent = GameDesignerAgent("game_designer")
        self.simulation_agent = SimulationDesignerAgent("simulation_designer")
        self.reviewer_agent = ReviewerAgent("reviewer")

        # Build agent registry
        self.agent_registry = {
            ContentRole.QUIZ_WRITER.value: self.quiz_agent,
            ContentRole.STORY_WRITER.value: self.story_agent,
            ContentRole.GAME_WRITER.value: self.game_agent,
            ContentRole.SIMULATION_WRITER.value: self.simulation_agent,
            "reviewer": self.reviewer_agent,
        }

        logger.info(f"Initialized CoordinatorAgent {agent_id} with specialized agents")

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute coordinator task.

        Routes to appropriate agent based on content type.

        Args:
            task: Task to execute
            resolved_prompt: Resolved prompt string

        Returns:
            Task result dictionary
        """
        context = self.prepare_task_context(task)
        content_type = context.get("content_type", "quiz")

        logger.info(f"Coordinator routing to {content_type} agent")

        return await self._generate_content(content_type, context)

    async def _generate_content(
        self, content_type: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate content using appropriate agent.

        Args:
            content_type: Type of content to generate
            context: Generation parameters

        Returns:
            Generated content dictionary
        """
        agent = self._get_agent_for_type(content_type)
        if not agent:
            return {"error": f"Unknown content type: {content_type}"}

        # Create task for the agent (use AgentRole.WRITER for all content tasks)
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
        """Public API for content generation.

        Args:
            content_type: Type of content
            topic: Content topic
            **parameters: Additional parameters

        Returns:
            Generated content dictionary
        """
        context = {"topic": topic, "content_type": content_type, **parameters}
        return await self._generate_content(content_type, context)

    async def generate_and_review(
        self, content_type: str, topic: str, **parameters
    ) -> Dict[str, Any]:
        """Generate content and review it.

        Args:
            content_type: Type of content
            topic: Content topic
            **parameters: Additional parameters

        Returns:
            Result with content and review
        """
        # Generate
        gen_result = await self.generate_content(content_type, topic, **parameters)

        if "error" in gen_result:
            return gen_result

        content = gen_result.get("content", {})

        # Review
        review_task = AgentTask(
            task_id="review_content",
            agent_role=AgentRole.REVIEWER,
            prompt="Review content",
            parameters={"content": content, "content_type": content_type},
            output_key="review",
        )

        review_result = await self.reviewer_agent.process_task(review_task)

        return {
            "content_type": content_type,
            "content": content,
            "review": review_result,
            "agents_involved": [
                gen_result.get("agent_used"),
                self.reviewer_agent.agent_id,
            ],
            "status": "completed",
        }

    def _get_agent_for_type(self, content_type: str) -> Optional[StatefulAgent]:
        """Get agent for content type.

        Args:
            content_type: Type of content

        Returns:
            Agent instance or None
        """
        # Normalize content type
        content_type = content_type.lower().replace(" ", "_")

        # Direct mapping
        type_to_agent = {
            "quiz": self.quiz_agent,
            "story": self.story_agent,
            "branched_narrative": self.story_agent,
            "game": self.game_agent,
            "quest_game": self.game_agent,
            "simulation": self.simulation_agent,
            "web_simulation": self.simulation_agent,
        }

        return type_to_agent.get(content_type)

    def get_registered_agents(self) -> Dict[str, str]:
        """Get summary of registered agents.

        Returns:
            Dict of role -> agent_id
        """
        return {role: agent.agent_id for role, agent in self.agent_registry.items()}

    def _get_reviewer(self) -> ReviewerAgent:
        """Get the reviewer agent instance.

        Returns:
            ReviewerAgent instance
        """
        return self.reviewer_agent


__all__ = ["CoordinatorAgent"]
