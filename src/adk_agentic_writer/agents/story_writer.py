"""Story writer agent for generating branched narratives."""

import logging
from typing import Any, Dict

from ..models.agent_models import AgentRole, AgentStatus
from ..models.content_models import BranchedNarrative, StoryNode
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class StoryWriterAgent(BaseAgent):
    """Agent specialized in creating branched narrative stories."""

    def __init__(self, agent_id: str = "story_writer_1", config: Dict[str, Any] | None = None):
        """Initialize the story writer agent."""
        super().__init__(agent_id, AgentRole.STORY_WRITER, config)

    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a branched narrative based on the given topic and parameters.

        Args:
            task_description: Description of the story to create
            parameters: Parameters including topic, genre, num_branches

        Returns:
            Dict containing the generated branched narrative
        """
        await self.update_status(AgentStatus.WORKING)
        
        topic = parameters.get("topic", "adventure")
        genre = parameters.get("genre", "fantasy")
        num_nodes = parameters.get("num_nodes", 7)
        
        logger.info(f"Generating branched narrative about {topic} in {genre} genre")
        
        # Generate story nodes
        nodes = await self._generate_story_nodes(topic, genre, num_nodes)
        
        # Create narrative object
        narrative = BranchedNarrative(
            title=f"The {topic.title()} Chronicles",
            synopsis=f"An interactive {genre} story about {topic}",
            genre=genre,
            start_node="start",
            nodes=nodes,
            characters=parameters.get("characters", ["Protagonist", "Guide", "Antagonist"]),
        )
        
        await self.update_status(AgentStatus.COMPLETED)
        
        return narrative.model_dump()

    async def _generate_story_nodes(
        self, topic: str, genre: str, num_nodes: int
    ) -> Dict[str, StoryNode]:
        """Generate story nodes for the branched narrative."""
        nodes = {}
        
        # Create start node
        nodes["start"] = StoryNode(
            node_id="start",
            content=f"You find yourself at the beginning of an extraordinary journey into {topic}. "
            f"The world of {genre} stretches before you, full of possibilities.",
            branches=[
                {"text": "Venture forth boldly", "next_node_id": "bold_path"},
                {"text": "Proceed with caution", "next_node_id": "cautious_path"},
            ],
            tags=["beginning", topic, genre],
        )
        
        # Create bold path
        nodes["bold_path"] = StoryNode(
            node_id="bold_path",
            content=f"Your bold approach to {topic} leads you to unexpected discoveries. "
            "The path ahead splits into two distinct routes.",
            branches=[
                {"text": "Take the challenging route", "next_node_id": "challenge"},
                {"text": "Seek allies", "next_node_id": "allies"},
            ],
            tags=["bold", topic],
        )
        
        # Create cautious path
        nodes["cautious_path"] = StoryNode(
            node_id="cautious_path",
            content=f"Your careful consideration of {topic} reveals hidden details others might miss. "
            "You notice two opportunities.",
            branches=[
                {"text": "Investigate further", "next_node_id": "investigation"},
                {"text": "Gather resources", "next_node_id": "resources"},
            ],
            tags=["cautious", topic],
        )
        
        # Create challenge node
        nodes["challenge"] = StoryNode(
            node_id="challenge",
            content=f"The challenge tests your understanding of {topic}. "
            "Through determination, you overcome the obstacles.",
            branches=[
                {"text": "Claim your victory", "next_node_id": "victory_ending"},
            ],
            tags=["challenge", topic],
        )
        
        # Create allies node
        nodes["allies"] = StoryNode(
            node_id="allies",
            content=f"You find companions who share your interest in {topic}. "
            "Together, you're stronger.",
            branches=[
                {"text": "Continue together", "next_node_id": "alliance_ending"},
            ],
            tags=["allies", topic],
        )
        
        # Create investigation node
        nodes["investigation"] = StoryNode(
            node_id="investigation",
            content=f"Your investigation into {topic} uncovers profound truths. "
            "Knowledge becomes your greatest asset.",
            branches=[
                {"text": "Share your discoveries", "next_node_id": "wisdom_ending"},
            ],
            tags=["investigation", topic],
        )
        
        # Create resources node
        nodes["resources"] = StoryNode(
            node_id="resources",
            content=f"The resources you've gathered about {topic} prove invaluable. "
            "You're well-prepared for what comes next.",
            branches=[
                {"text": "Put resources to use", "next_node_id": "prosperity_ending"},
            ],
            tags=["resources", topic],
        )
        
        # Create multiple endings
        nodes["victory_ending"] = StoryNode(
            node_id="victory_ending",
            content=f"Through courage and determination, you've mastered {topic}. "
            "Your victory inspires others to follow in your footsteps.",
            branches=[],
            tags=["ending", "victory", topic],
            is_ending=True,
        )
        
        nodes["alliance_ending"] = StoryNode(
            node_id="alliance_ending",
            content=f"Your alliance has transformed the understanding of {topic}. "
            "Together, you've achieved what none could alone.",
            branches=[],
            tags=["ending", "alliance", topic],
            is_ending=True,
        )
        
        nodes["wisdom_ending"] = StoryNode(
            node_id="wisdom_ending",
            content=f"The wisdom you've gained about {topic} becomes a beacon for others. "
            "Your discoveries change the world.",
            branches=[],
            tags=["ending", "wisdom", topic],
            is_ending=True,
        )
        
        nodes["prosperity_ending"] = StoryNode(
            node_id="prosperity_ending",
            content=f"Your careful preparation regarding {topic} leads to lasting prosperity. "
            "The resources you built create opportunities for all.",
            branches=[],
            tags=["ending", "prosperity", topic],
            is_ending=True,
        )
        
        return nodes
