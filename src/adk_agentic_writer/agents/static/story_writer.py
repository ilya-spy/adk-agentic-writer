"""Story writer agent implementing ContentProtocol with StatefulAgent framework.

This agent generates branched narratives using:
- StatefulAgent: For variable/parameter management
- Tasks: Predefined content generation tasks
- ContentProtocol: Standard content generation methods
"""

import logging
import random
from typing import Any, Dict, List, Optional

from ...agents.stateful_agent import StatefulAgent
from ...models.agent_models import AgentTask, AgentStatus
from ...models.content_models import BranchedNarrative, StoryNode
from ...protocols.content_protocol import ContentBlock, ContentBlockType, ContentPattern
from ...teams.content_team import STORY_WRITER

logger = logging.getLogger(__name__)

# Story templates
STORY_OPENINGS = [
    "You find yourself at the beginning of an extraordinary journey into {topic}.",
    "As dawn breaks, you stand at the threshold of {topic}.",
    "A mysterious force draws you toward {topic}.",
    "The ancient texts spoke of {topic}, but nothing prepared you for this moment.",
]

PATH_DESCRIPTIONS = {
    "bold": "Your bold approach to {topic} leads you to unexpected discoveries.",
    "cautious": "Your careful consideration of {topic} reveals hidden details.",
    "challenge": "The challenge tests your understanding of {topic}.",
    "allies": "You find companions who share your interest in {topic}.",
}

ENDINGS = {
    "victory": "Through courage and determination, you've mastered {topic}.",
    "alliance": "Your alliance has transformed the understanding of {topic}.",
    "wisdom": "The wisdom you've gained about {topic} becomes a beacon for others.",
}


class StoryWriterAgent(StatefulAgent):
    """Story writer agent using StatefulAgent framework.
    
    Implements:
    - AgentProtocol: process_task, update_status
    - ContentProtocol: generate_block, generate_sequential_blocks, etc.
    """

    def __init__(self, agent_id: str = "story_writer"):
        """Initialize story writer agent."""
        super().__init__(
            agent_id=agent_id,
            config=STORY_WRITER,
        )
        logger.info(f"Initialized StoryWriterAgent {agent_id}")

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute task based on task_id."""
        # Extract context
        context = self.prepare_task_context(task)
        
        if task.task_id == "generate_block":
            block = await self.generate_block(ContentBlockType.NODE, context)
            return block.content
        elif task.task_id == "generate_sequential_blocks":
            num_blocks = context.get("num_blocks", 3)
            blocks = await self.generate_sequential_blocks(
                num_blocks, ContentBlockType.NODE, context
            )
            return {"blocks": [b.content for b in blocks]}
        elif task.task_id == "generate_branched_blocks":
            branch_points = context.get("branch_points", [])
            blocks = await self.generate_branched_blocks(branch_points, context)
            return {"blocks": [b.content for b in blocks]}
        else:
            # Default: generate story
            return await self._generate_story_content(resolved_prompt, context)

    # ========================================================================
    # ContentProtocol Implementation
    # ========================================================================

    async def generate_block(
        self,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        previous_blocks: Optional[List[ContentBlock]] = None,
    ) -> ContentBlock:
        """Generate a single story content block."""
        topic = context.get("topic", "adventure")
        genre = context.get("genre", "fantasy")
        
        story_data = await self._generate_story_data(topic, genre, num_nodes=5)
        
        return ContentBlock(
            block_id=f"story_{topic.replace(' ', '_')}",
            block_type=block_type,
            content=story_data,
            pattern=ContentPattern.BRANCHED,
        )

    async def generate_sequential_blocks(
        self,
        num_blocks: int,
        block_type: ContentBlockType,
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate sequential story chapters."""
        blocks = []
        topic = context.get("topic", "adventure")
        
        for i in range(num_blocks):
            chapter_topic = f"{topic} - Chapter {i+1}"
            story_data = await self._generate_story_data(chapter_topic, context.get("genre", "fantasy"), 3)
            
            block = ContentBlock(
                block_id=f"chapter_{i+1}",
                block_type=block_type,
                content=story_data,
                pattern=ContentPattern.SEQUENTIAL,
                navigation={
                    "next": f"chapter_{i+2}" if i < num_blocks - 1 else None,
                    "prev": f"chapter_{i}" if i > 0 else None,
                },
            )
            blocks.append(block)
        
        return blocks

    async def generate_looped_blocks(
        self,
        num_blocks: int,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        exit_condition: Dict[str, Any],
        allow_back: bool = True,
    ) -> List[ContentBlock]:
        """Generate looped story blocks (e.g., story practice/replay)."""
        blocks = []
        topic = context.get("topic", "adventure")
        
        for i in range(num_blocks):
            story_data = await self._generate_story_data(topic, context.get("genre", "fantasy"), 3)
            
            block = ContentBlock(
                block_id=f"replay_{i+1}",
                block_type=block_type,
                content=story_data,
                pattern=ContentPattern.LOOPED,
                navigation={
                    "next": f"replay_{(i+1) % num_blocks + 1}",
                    "prev": f"replay_{i}" if allow_back and i > 0 else None,
                    "exit": "check_exit_condition",
                },
                exit_condition=exit_condition,
            )
            blocks.append(block)
        
        return blocks

    async def generate_branched_blocks(
        self,
        branch_points: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate branched narrative blocks."""
        blocks = []
        topic = context.get("topic", "adventure")
        genre = context.get("genre", "fantasy")
        
        # Generate full branched narrative
        story_data = await self._generate_story_data(topic, genre, num_nodes=7)
        nodes = story_data["nodes"]
        
        # Convert nodes to content blocks
        for node_id, node in nodes.items():
            choices = [
                {"text": branch["text"], "next_block": branch["next_node_id"]}
                for branch in node.get("branches", [])
            ]
            
            block = ContentBlock(
                block_id=node_id,
                block_type=ContentBlockType.NODE,
                content={"text": node["content"], "node": node},
                pattern=ContentPattern.BRANCHED,
                choices=choices,
            )
            blocks.append(block)
        
        return blocks

    async def generate_conditional_blocks(
        self,
        blocks_config: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate conditional story blocks."""
        blocks = []
        topic = context.get("topic", "adventure")
        
        for config in blocks_config:
            condition = config.get("condition", {})
            story_data = await self._generate_story_data(topic, context.get("genre", "fantasy"), 3)
            
            block = ContentBlock(
                block_id=config.get("block_id", f"conditional_{len(blocks)}"),
                block_type=ContentBlockType.NODE,
                content=story_data,
                pattern=ContentPattern.CONDITIONAL,
                metadata={"display_condition": condition},
            )
            blocks.append(block)
        
        return blocks

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _generate_story_content(
        self, resolved_prompt: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate story content from resolved prompt."""
        topic = context.get("topic", "adventure")
        genre = context.get("genre", "fantasy")
        num_nodes = context.get("num_nodes", 7)
        
        return await self._generate_story_data(topic, genre, num_nodes)

    async def _generate_story_data(
        self, topic: str, genre: str, num_nodes: int
    ) -> Dict[str, Any]:
        """Generate branched narrative story data."""
        logger.info(f"Generating story: {topic}, genre: {genre}, nodes: {num_nodes}")
        
        # Generate story nodes
        nodes = {}
        
        # Opening node
        opening = random.choice(STORY_OPENINGS).format(topic=topic)
        nodes["start"] = StoryNode(
            node_id="start",
            content=opening,
            branches=[
                {"text": "Take the bold path", "next_node_id": "bold_path"},
                {"text": "Proceed with caution", "next_node_id": "cautious_path"},
            ],
            tags=["opening", genre],
            is_ending=False,
        ).model_dump()
        
        # Path nodes
        if num_nodes >= 3:
            nodes["bold_path"] = StoryNode(
                node_id="bold_path",
                content=PATH_DESCRIPTIONS["bold"].format(topic=topic),
                branches=[
                    {"text": "Face the challenge", "next_node_id": "challenge"},
                    {"text": "Find allies", "next_node_id": "allies"},
                ],
                tags=["bold"],
                is_ending=False,
            ).model_dump()
            
            nodes["cautious_path"] = StoryNode(
                node_id="cautious_path",
                content=PATH_DESCRIPTIONS["cautious"].format(topic=topic),
                branches=[
                    {"text": "Continue alone", "next_node_id": "challenge"},
                    {"text": "Seek wisdom", "next_node_id": "wisdom_ending"},
                ],
                tags=["cautious"],
                is_ending=False,
            ).model_dump()
        
        # Intermediate nodes
        if num_nodes >= 5:
            nodes["challenge"] = StoryNode(
                node_id="challenge",
                content=PATH_DESCRIPTIONS["challenge"].format(topic=topic),
                branches=[
                    {"text": "Claim victory", "next_node_id": "victory_ending"},
                ],
                tags=["challenge"],
                is_ending=False,
            ).model_dump()
            
            nodes["allies"] = StoryNode(
                node_id="allies",
                content=PATH_DESCRIPTIONS["allies"].format(topic=topic),
                branches=[
                    {"text": "Continue together", "next_node_id": "alliance_ending"},
                ],
                tags=["allies"],
                is_ending=False,
            ).model_dump()
        
        # Ending nodes
        nodes["victory_ending"] = StoryNode(
            node_id="victory_ending",
            content=ENDINGS["victory"].format(topic=topic),
            branches=[],
            tags=["ending", "victory"],
            is_ending=True,
        ).model_dump()
        
        nodes["alliance_ending"] = StoryNode(
            node_id="alliance_ending",
            content=ENDINGS["alliance"].format(topic=topic),
            branches=[],
            tags=["ending", "alliance"],
            is_ending=True,
        ).model_dump()
        
        nodes["wisdom_ending"] = StoryNode(
            node_id="wisdom_ending",
            content=ENDINGS["wisdom"].format(topic=topic),
            branches=[],
            tags=["ending", "wisdom"],
            is_ending=True,
        ).model_dump()
        
        # Create narrative
        narrative = BranchedNarrative(
            title=f"The {topic.title()} Chronicles",
            synopsis=f"An interactive {genre} story about {topic}",
            genre=genre,
            start_node="start",
            nodes=nodes,
            characters=["Protagonist", "Guide", "Antagonist"],
        )
        
        return narrative.model_dump()


__all__ = ["StoryWriterAgent"]
