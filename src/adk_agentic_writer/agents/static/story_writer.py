"""Story writer agent for generating branched narratives."""

import logging
import random
from typing import Any, Dict, List

from ...models.agent_models import AgentRole, AgentStatus
from ...models.content_models import BranchedNarrative, StoryNode
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Story opening scenarios pool
STORY_OPENINGS = [
    "You find yourself at the beginning of an extraordinary journey into {topic}. The world of {genre} stretches before you, full of possibilities.",
    "As dawn breaks, you stand at the threshold of {topic}. The {genre} realm ahead promises adventure and discovery.",
    "A mysterious force draws you toward {topic}. In this {genre} world, every choice shapes your destiny.",
    "The ancient texts spoke of {topic}, but nothing prepared you for this moment. The {genre} adventure begins now.",
    "You've trained for this moment - to explore {topic}. The {genre} landscape unfolds before your eyes.",
]

# Path descriptions pool
PATH_DESCRIPTIONS = {
    "bold": [
        "Your bold approach to {topic} leads you to unexpected discoveries.",
        "Courage drives you forward into {topic}, revealing hidden opportunities.",
        "Your daring decision regarding {topic} opens new pathways.",
        "Fearlessly, you dive deeper into {topic}, uncovering secrets.",
    ],
    "cautious": [
        "Your careful consideration of {topic} reveals hidden details others might miss.",
        "Patience and observation guide your exploration of {topic}.",
        "Your methodical approach to {topic} uncovers subtle clues.",
        "Wisdom leads you to examine {topic} from every angle.",
    ],
    "challenge": [
        "The challenge tests your understanding of {topic}.",
        "Obstacles related to {topic} push you to your limits.",
        "A formidable trial involving {topic} stands before you.",
        "Your mastery of {topic} is put to the ultimate test.",
    ],
    "allies": [
        "You find companions who share your interest in {topic}.",
        "Like-minded individuals join your quest regarding {topic}.",
        "A fellowship forms around the pursuit of {topic}.",
        "Others who understand {topic} rally to your cause.",
    ],
}

# Branch choice templates
BRANCH_CHOICES = {
    "bold_cautious": [
        ("Venture forth boldly", "Proceed with caution"),
        ("Take immediate action", "Plan carefully first"),
        ("Trust your instincts", "Analyze the situation"),
        ("Charge ahead", "Move strategically"),
    ],
    "challenge_allies": [
        ("Face the challenge alone", "Seek allies"),
        ("Test your skills", "Build a team"),
        ("Prove your worth", "Find companions"),
        ("Take on the trial", "Gather support"),
    ],
    "investigation_resources": [
        ("Investigate further", "Gather resources"),
        ("Seek knowledge", "Collect tools"),
        ("Research deeply", "Prepare supplies"),
        ("Study the mystery", "Stockpile assets"),
    ],
}

# Ending variations
ENDINGS = {
    "victory": [
        "Through courage and determination, you've mastered {topic}. Your victory inspires others.",
        "Your triumph over {topic} becomes legendary. Songs will be sung of your deeds.",
        "Success! Your understanding of {topic} has reached its peak, and the world takes notice.",
        "Victory is yours. The challenges of {topic} have been conquered completely.",
    ],
    "alliance": [
        "Your alliance has transformed the understanding of {topic}. Together, you've achieved greatness.",
        "The bonds forged through {topic} create a legacy that will endure for generations.",
        "United in purpose around {topic}, your team accomplishes the impossible.",
        "The fellowship you built around {topic} becomes a beacon of cooperation.",
    ],
    "wisdom": [
        "The wisdom you've gained about {topic} becomes a beacon for others.",
        "Your insights into {topic} revolutionize the field and enlighten many.",
        "The knowledge of {topic} you've acquired changes the course of history.",
        "Your understanding of {topic} transcends mere facts, becoming true wisdom.",
    ],
    "prosperity": [
        "Your careful preparation regarding {topic} leads to lasting prosperity.",
        "The resources you built around {topic} create opportunities for all.",
        "Your strategic approach to {topic} yields abundant rewards.",
        "Prosperity flows from your mastery of {topic}, benefiting many.",
    ],
}


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
        """Generate story nodes for the branched narrative with randomized content."""
        nodes = {}
        
        # Randomly select story elements
        opening = random.choice(STORY_OPENINGS).format(topic=topic, genre=genre)
        bold_desc = random.choice(PATH_DESCRIPTIONS["bold"]).format(topic=topic)
        cautious_desc = random.choice(PATH_DESCRIPTIONS["cautious"]).format(topic=topic)
        challenge_desc = random.choice(PATH_DESCRIPTIONS["challenge"]).format(topic=topic)
        allies_desc = random.choice(PATH_DESCRIPTIONS["allies"]).format(topic=topic)
        
        # Select branch choices
        initial_choices = random.choice(BRANCH_CHOICES["bold_cautious"])
        bold_choices = random.choice(BRANCH_CHOICES["challenge_allies"])
        cautious_choices = random.choice(BRANCH_CHOICES["investigation_resources"])
        
        # Select endings
        victory_ending = random.choice(ENDINGS["victory"]).format(topic=topic)
        alliance_ending = random.choice(ENDINGS["alliance"]).format(topic=topic)
        wisdom_ending = random.choice(ENDINGS["wisdom"]).format(topic=topic)
        prosperity_ending = random.choice(ENDINGS["prosperity"]).format(topic=topic)
        
        # Create start node
        nodes["start"] = StoryNode(
            node_id="start",
            content=opening,
            branches=[
                {"text": initial_choices[0], "next_node_id": "bold_path"},
                {"text": initial_choices[1], "next_node_id": "cautious_path"},
            ],
            tags=["beginning", topic, genre],
        )
        
        # Create bold path
        nodes["bold_path"] = StoryNode(
            node_id="bold_path",
            content=f"{bold_desc} The path ahead splits into two distinct routes.",
            branches=[
                {"text": bold_choices[0], "next_node_id": "challenge"},
                {"text": bold_choices[1], "next_node_id": "allies"},
            ],
            tags=["bold", topic],
        )
        
        # Create cautious path
        nodes["cautious_path"] = StoryNode(
            node_id="cautious_path",
            content=f"{cautious_desc} You notice two opportunities.",
            branches=[
                {"text": cautious_choices[0], "next_node_id": "investigation"},
                {"text": cautious_choices[1], "next_node_id": "resources"},
            ],
            tags=["cautious", topic],
        )
        
        # Create challenge node
        nodes["challenge"] = StoryNode(
            node_id="challenge",
            content=f"{challenge_desc} Through determination, you overcome the obstacles.",
            branches=[
                {"text": "Claim your victory", "next_node_id": "victory_ending"},
            ],
            tags=["challenge", topic],
        )
        
        # Create allies node
        nodes["allies"] = StoryNode(
            node_id="allies",
            content=f"{allies_desc} Together, you're stronger.",
            branches=[
                {"text": "Continue together", "next_node_id": "alliance_ending"},
            ],
            tags=["allies", topic],
        )
        
        # Create investigation node
        nodes["investigation"] = StoryNode(
            node_id="investigation",
            content=f"Your investigation into {topic} uncovers profound truths. Knowledge becomes your greatest asset.",
            branches=[
                {"text": "Share your discoveries", "next_node_id": "wisdom_ending"},
            ],
            tags=["investigation", topic],
        )
        
        # Create resources node
        nodes["resources"] = StoryNode(
            node_id="resources",
            content=f"The resources you've gathered about {topic} prove invaluable. You're well-prepared for what comes next.",
            branches=[
                {"text": "Put resources to use", "next_node_id": "prosperity_ending"},
            ],
            tags=["resources", topic],
        )
        
        # Create multiple endings with randomized content
        nodes["victory_ending"] = StoryNode(
            node_id="victory_ending",
            content=victory_ending,
            branches=[],
            tags=["ending", "victory", topic],
            is_ending=True,
        )
        
        nodes["alliance_ending"] = StoryNode(
            node_id="alliance_ending",
            content=alliance_ending,
            branches=[],
            tags=["ending", "alliance", topic],
            is_ending=True,
        )
        
        nodes["wisdom_ending"] = StoryNode(
            node_id="wisdom_ending",
            content=wisdom_ending,
            branches=[],
            tags=["ending", "wisdom", topic],
            is_ending=True,
        )
        
        nodes["prosperity_ending"] = StoryNode(
            node_id="prosperity_ending",
            content=prosperity_ending,
            branches=[],
            tags=["ending", "prosperity", topic],
            is_ending=True,
        )
        
        return nodes

    async def generate_content(self, prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate story content based on prompt and parameters.

        Args:
            prompt: Content generation prompt
            parameters: Generation parameters

        Returns:
            Dict containing generated story
        """
        return await self.process_task(prompt, parameters)

    async def validate_content(self, content: Dict[str, Any]) -> bool:
        """
        Validate generated story content.

        Args:
            content: Story content to validate

        Returns:
            True if content is valid, False otherwise
        """
        try:
            # Validate story structure
            narrative = BranchedNarrative(**content)
            
            # Check that we have nodes
            if not narrative.nodes:
                return False
            
            # Check that start node exists
            if narrative.start_node not in narrative.nodes:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Content validation failed: {e}")
            return False

    async def refine_content(self, content: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        Refine story content based on feedback.

        Args:
            content: Story content to refine
            feedback: Feedback for refinement

        Returns:
            Dict containing refined story
        """
        # For base implementation, just return the content
        # Subclasses can implement more sophisticated refinement
        logger.info(f"Refining story content based on feedback: {feedback}")
        return content
