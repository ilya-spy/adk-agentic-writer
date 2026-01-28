"""Static story writer agent.

Generates branched narratives using template-based text generation.
Inherits from ContentWriterAgent for unified structure.
"""

import logging
from typing import Any, Dict

from ...models.content_models import BranchedNarrative, StoryNode
from ...teams.content_team import STORY_WRITER
from ..content_writer import ContentWriterAgent
from ..text_provider import TemplateTextProvider

logger = logging.getLogger(__name__)


class StoryWriterAgent(ContentWriterAgent):
    """Static story writer using template-based generation.

    Generates interactive branched narratives with:
    - Multiple paths and choices
    - Different endings
    - Character-driven content
    """

    def __init__(self, agent_id: str = "story_writer"):
        """Initialize static story writer.

        Args:
            agent_id: Unique agent identifier
        """
        super().__init__(
            agent_id=agent_id,
            config=STORY_WRITER,
            text_provider=TemplateTextProvider(),
        )
        logger.info(f"Initialized StoryWriterAgent {agent_id}")

    async def _build_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build branched narrative content.

        Args:
            context: Parameters including topic, genre, num_nodes

        Returns:
            BranchedNarrative dictionary
        """
        topic = context.get("topic", "adventure")
        genre = context.get("genre", "fantasy")
        num_nodes = context.get("num_nodes", 7)

        logger.info(f"Generating story: {topic}, genre: {genre}, nodes: {num_nodes}")

        nodes = await self._generate_story_nodes(topic, genre, num_nodes)

        narrative = BranchedNarrative(
            title=f"The {topic.title()} Chronicles",
            synopsis=f"An interactive {genre} story about {topic}",
            genre=genre,
            start_node="start",
            nodes=nodes,
            characters=["Protagonist", "Guide", "Antagonist"],
        )

        return narrative.model_dump()

    async def _generate_story_nodes(
        self, topic: str, genre: str, num_nodes: int
    ) -> Dict[str, Dict[str, Any]]:
        """Generate story nodes with branches.

        Args:
            topic: Story topic
            genre: Story genre
            num_nodes: Target number of nodes

        Returns:
            Dictionary of node_id -> StoryNode
        """
        nodes = {}
        ctx = {"topic": topic, "genre": genre}

        # Opening node
        opening_text = await self._generate_text("story_opening", ctx)
        nodes["start"] = StoryNode(
            node_id="start",
            content=opening_text,
            branches=[
                {"text": "Take the bold path", "next_node_id": "bold_path"},
                {"text": "Proceed with caution", "next_node_id": "cautious_path"},
            ],
            tags=["opening", genre],
            is_ending=False,
        ).model_dump()

        # Path nodes
        if num_nodes >= 3:
            bold_text = await self._generate_text(
                "story_path", {**ctx, "path_type": "bold"}
            )
            nodes["bold_path"] = StoryNode(
                node_id="bold_path",
                content=bold_text,
                branches=[
                    {"text": "Face the challenge", "next_node_id": "challenge"},
                    {"text": "Find allies", "next_node_id": "allies"},
                ],
                tags=["bold"],
                is_ending=False,
            ).model_dump()

            cautious_text = await self._generate_text(
                "story_path", {**ctx, "path_type": "cautious"}
            )
            nodes["cautious_path"] = StoryNode(
                node_id="cautious_path",
                content=cautious_text,
                branches=[
                    {"text": "Continue alone", "next_node_id": "challenge"},
                    {"text": "Seek wisdom", "next_node_id": "wisdom_ending"},
                ],
                tags=["cautious"],
                is_ending=False,
            ).model_dump()

        # Intermediate nodes
        if num_nodes >= 5:
            challenge_text = await self._generate_text(
                "story_path", {**ctx, "path_type": "challenge"}
            )
            nodes["challenge"] = StoryNode(
                node_id="challenge",
                content=challenge_text,
                branches=[
                    {"text": "Claim victory", "next_node_id": "victory_ending"},
                ],
                tags=["challenge"],
                is_ending=False,
            ).model_dump()

            allies_text = await self._generate_text(
                "story_path", {**ctx, "path_type": "allies"}
            )
            nodes["allies"] = StoryNode(
                node_id="allies",
                content=allies_text,
                branches=[
                    {"text": "Continue together", "next_node_id": "alliance_ending"},
                ],
                tags=["allies"],
                is_ending=False,
            ).model_dump()

        # Ending nodes
        victory_text = await self._generate_text(
            "story_ending", {**ctx, "ending_type": "victory"}
        )
        nodes["victory_ending"] = StoryNode(
            node_id="victory_ending",
            content=victory_text,
            branches=[],
            tags=["ending", "victory"],
            is_ending=True,
        ).model_dump()

        alliance_text = await self._generate_text(
            "story_ending", {**ctx, "ending_type": "alliance"}
        )
        nodes["alliance_ending"] = StoryNode(
            node_id="alliance_ending",
            content=alliance_text,
            branches=[],
            tags=["ending", "alliance"],
            is_ending=True,
        ).model_dump()

        wisdom_text = await self._generate_text(
            "story_ending", {**ctx, "ending_type": "wisdom"}
        )
        nodes["wisdom_ending"] = StoryNode(
            node_id="wisdom_ending",
            content=wisdom_text,
            branches=[],
            tags=["ending", "wisdom"],
            is_ending=True,
        ).model_dump()

        return nodes


__all__ = ["StoryWriterAgent"]
