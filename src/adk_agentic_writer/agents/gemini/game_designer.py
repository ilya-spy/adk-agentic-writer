"""Gemini-powered game designer agent.

Generates quest games using LLM-powered text generation.
Inherits from ContentWriterAgent for unified structure.
"""

import logging
from typing import Any, Dict

from ...models.content_models import QuestGame, QuestNode
from ...teams.content_team import GAME_WRITER
from ..content_writer import ContentWriterAgent
from ..text_provider import GeminiTextProvider

logger = logging.getLogger(__name__)


class GeminiGameDesignerAgent(ContentWriterAgent):
    """Gemini game designer using LLM-powered generation.

    Same structure as GameDesignerAgent but uses
    GeminiTextProvider for natural language generation.
    """

    def __init__(self, agent_id: str = "gemini_game_designer"):
        """Initialize Gemini game designer.

        Args:
            agent_id: Unique agent identifier
        """
        super().__init__(
            agent_id=agent_id,
            config=GAME_WRITER,
            text_provider=GeminiTextProvider(),
        )
        logger.info(f"Initialized GeminiGameDesignerAgent {agent_id}")

    async def _build_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build quest game content using LLM.

        Args:
            context: Parameters including topic, complexity, theme

        Returns:
            QuestGame dictionary
        """
        topic = context.get("topic", "adventure")
        complexity = context.get("complexity", "medium")
        theme = context.get("theme", "fantasy")
        num_nodes = context.get("num_nodes", 5)

        logger.info(f"Generating game with Gemini: {topic}, complexity: {complexity}")

        nodes = await self._generate_nodes(topic, theme, num_nodes, complexity)

        game = QuestGame(
            title=f"{topic.title()} Quest",
            description=f"An interactive quest game about {topic}",
            start_node="start",
            nodes=nodes,
            victory_conditions=[f"Complete all quests to master {topic}"],
        )

        return game.model_dump()

    async def _generate_nodes(
        self, topic: str, theme: str, num_nodes: int, complexity: str
    ) -> Dict[str, QuestNode]:
        """Generate game quest nodes using LLM.

        Args:
            topic: Game topic
            theme: Game theme
            num_nodes: Number of nodes
            complexity: Quest complexity

        Returns:
            Dictionary of node_id -> QuestNode
        """
        nodes = {}
        ctx = {"topic": topic, "theme": theme}

        # Start node
        quest_title = await self._generate_text("game_quest", ctx)
        nodes["start"] = QuestNode(
            node_id="start",
            title=quest_title,
            description=f"Begin your journey into {topic}. Choose your path wisely.",
            choices=[
                {"text": "Explore the basics", "next_node_id": "basics"},
                {"text": "Take on a challenge", "next_node_id": "challenge"},
            ],
            rewards=[],
            requirements=[],
        )

        # Basics node
        if num_nodes >= 3:
            obj_text = await self._generate_text(
                "game_objective", {**ctx, "aspect": "fundamentals"}
            )
            nodes["basics"] = QuestNode(
                node_id="basics",
                title="Learning the Basics",
                description=obj_text,
                choices=[
                    {
                        "text": "Continue to intermediate",
                        "next_node_id": "intermediate",
                    },
                    {"text": "Try the challenge", "next_node_id": "challenge"},
                ],
                rewards=["Basic Knowledge", "50 XP"],
                requirements=[],
            )

        # Challenge node
        if num_nodes >= 4:
            obj_text = await self._generate_text(
                "game_objective", {**ctx, "aspect": "challenges"}
            )
            nodes["challenge"] = QuestNode(
                node_id="challenge",
                title="The Challenge",
                description=obj_text,
                choices=[
                    {"text": "Proceed to mastery", "next_node_id": "mastery"},
                ],
                rewards=["Challenge Badge", "100 XP"],
                requirements=["Basic Knowledge"] if complexity != "simple" else [],
            )

        # Intermediate node
        if num_nodes >= 5 and complexity in ["medium", "complex"]:
            obj_text = await self._generate_text(
                "game_objective", {**ctx, "aspect": "intermediate concepts"}
            )
            nodes["intermediate"] = QuestNode(
                node_id="intermediate",
                title="Intermediate Level",
                description=obj_text,
                choices=[
                    {"text": "Advance to mastery", "next_node_id": "mastery"},
                ],
                rewards=["Intermediate Badge", "150 XP"],
                requirements=["Basic Knowledge"],
            )

        # Mastery node
        nodes["mastery"] = QuestNode(
            node_id="mastery",
            title=f"Mastery of {topic.title()}",
            description=f"Congratulations! You have achieved mastery in {topic}.",
            choices=[],
            rewards=[f"{topic.title()} Master Badge", "500 XP"],
            requirements=["Challenge Badge"] if complexity != "simple" else [],
        )

        return nodes


__all__ = ["GeminiGameDesignerAgent"]
