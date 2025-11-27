"""Game designer agent implementing ContentProtocol with StatefulAgent framework.

This agent generates quest-based games using:
- StatefulAgent: For variable/parameter management
- Tasks: Predefined content generation tasks
- ContentProtocol: Standard content generation methods
"""

import logging
import random
from typing import Any, Dict, List, Optional

from ...agents.stateful_agent import StatefulAgent
from ...models.agent_models import AgentTask, AgentStatus
from ...models.content_models import QuestGame, QuestNode
from ...protocols.content_protocol import ContentBlock, ContentBlockType, ContentPattern
from ...teams.content_team import GAME_WRITER

logger = logging.getLogger(__name__)

# Game templates
GAME_INTROS = [
    "Welcome to the world of {topic}! Your quest begins here.",
    "The realm of {topic} awaits your arrival. Are you ready?",
    "A new adventure in {topic} starts now. Prepare yourself!",
]

QUEST_DESCRIPTIONS = {
    "explore": "You explore the mysteries of {topic}, discovering new paths forward.",
    "combat": "You face challenges related to {topic}, testing your skills.",
    "puzzle": "A puzzle about {topic} blocks your way. Can you solve it?",
    "treasure": "You've found valuable knowledge about {topic}!",
}

VICTORY_MESSAGES = [
    "Congratulations! You've mastered {topic} and completed the quest!",
    "Victory! Your journey through {topic} has reached a triumphant end!",
    "Quest complete! You are now an expert in {topic}!",
]


class GameDesignerAgent(StatefulAgent):
    """Game designer agent using StatefulAgent framework.

    Implements:
    - AgentProtocol: process_task, update_status
    - ContentProtocol: generate_block, generate_sequential_blocks, etc.
    """

    def __init__(self, agent_id: str = "game_designer"):
        """Initialize game designer agent."""
        super().__init__(
            agent_id=agent_id,
            config=GAME_WRITER,
        )
        logger.info(f"Initialized GameDesignerAgent {agent_id}")

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
            # Default: generate game
            return await self._generate_game_content(resolved_prompt, context)

    # ========================================================================
    # ContentProtocol Implementation
    # ========================================================================

    async def generate_block(
        self,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        previous_blocks: Optional[List[ContentBlock]] = None,
    ) -> ContentBlock:
        """Generate a single game content block."""
        topic = context.get("topic", "adventure")
        difficulty = context.get("difficulty", "medium")

        game_data = await self._generate_game_data(
            topic, num_nodes=5, difficulty=difficulty
        )

        return ContentBlock(
            block_id=f"game_{topic.replace(' ', '_')}",
            block_type=block_type,
            content=game_data,
            pattern=ContentPattern.BRANCHED,
        )

    async def generate_sequential_blocks(
        self,
        num_blocks: int,
        block_type: ContentBlockType,
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate sequential game levels."""
        blocks = []
        topic = context.get("topic", "adventure")

        for i in range(num_blocks):
            level_topic = f"{topic} - Level {i+1}"
            game_data = await self._generate_game_data(
                level_topic, num_nodes=3, difficulty="medium"
            )

            block = ContentBlock(
                block_id=f"level_{i+1}",
                block_type=block_type,
                content=game_data,
                pattern=ContentPattern.SEQUENTIAL,
                navigation={
                    "next": f"level_{i+2}" if i < num_blocks - 1 else None,
                    "prev": f"level_{i}" if i > 0 else None,
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
        """Generate looped game blocks (e.g., endless mode)."""
        blocks = []
        topic = context.get("topic", "adventure")

        for i in range(num_blocks):
            game_data = await self._generate_game_data(
                topic, num_nodes=3, difficulty="medium"
            )

            block = ContentBlock(
                block_id=f"round_{i+1}",
                block_type=block_type,
                content=game_data,
                pattern=ContentPattern.LOOPED,
                navigation={
                    "next": f"round_{(i+1) % num_blocks + 1}",
                    "prev": f"round_{i}" if allow_back and i > 0 else None,
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
        """Generate branched game quest blocks."""
        blocks = []
        topic = context.get("topic", "adventure")

        # Generate full game with branches
        game_data = await self._generate_game_data(
            topic, num_nodes=7, difficulty="medium"
        )
        nodes = game_data["nodes"]

        # Convert nodes to content blocks
        for node_id, node in nodes.items():
            choices = [
                {"text": choice["text"], "next_block": choice["next_node_id"]}
                for choice in node.get("choices", [])
            ]

            block = ContentBlock(
                block_id=node_id,
                block_type=ContentBlockType.NODE,
                content={"description": node["description"], "node": node},
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
        """Generate conditional game blocks (e.g., bonus levels)."""
        blocks = []
        topic = context.get("topic", "adventure")

        for config in blocks_config:
            condition = config.get("condition", {})
            game_data = await self._generate_game_data(
                topic, num_nodes=3, difficulty="hard"
            )

            block = ContentBlock(
                block_id=config.get("block_id", f"bonus_{len(blocks)}"),
                block_type=ContentBlockType.NODE,
                content=game_data,
                pattern=ContentPattern.CONDITIONAL,
                metadata={"display_condition": condition},
            )
            blocks.append(block)

        return blocks

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _generate_game_content(
        self, resolved_prompt: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate game content from resolved prompt."""
        topic = context.get("topic", "adventure")
        num_nodes = context.get("num_nodes", 7)
        difficulty = context.get("difficulty", "medium")

        return await self._generate_game_data(topic, num_nodes, difficulty)

    async def _generate_game_data(
        self, topic: str, num_nodes: int, difficulty: str
    ) -> Dict[str, Any]:
        """Generate quest game data."""
        logger.info(
            f"Generating game: {topic}, nodes: {num_nodes}, difficulty: {difficulty}"
        )

        # Generate quest nodes
        nodes = {}

        # Starting node
        intro = random.choice(GAME_INTROS).format(topic=topic)
        nodes["start"] = QuestNode(
            node_id="start",
            title="Quest Begins",
            description=intro,
            choices=[
                {"text": "Begin exploration", "next_node_id": "explore_1"},
                {"text": "Seek information", "next_node_id": "explore_2"},
            ],
            rewards=[],
            requirements=[],
        ).model_dump()

        # Exploration nodes
        if num_nodes >= 3:
            nodes["explore_1"] = QuestNode(
                node_id="explore_1",
                title="Exploration Path",
                description=QUEST_DESCRIPTIONS["explore"].format(topic=topic),
                choices=[
                    {"text": "Face the challenge", "next_node_id": "combat"},
                    {"text": "Solve the puzzle", "next_node_id": "puzzle"},
                ],
                rewards=["experience_10", "knowledge_5"],
                requirements=[],
            ).model_dump()

            nodes["explore_2"] = QuestNode(
                node_id="explore_2",
                title="Alternative Route",
                description=QUEST_DESCRIPTIONS["explore"].format(topic=topic),
                choices=[
                    {"text": "Continue quest", "next_node_id": "treasure"},
                ],
                rewards=["experience_10"],
                requirements=[],
            ).model_dump()

        # Challenge nodes
        if num_nodes >= 5:
            nodes["combat"] = QuestNode(
                node_id="combat",
                title="Combat Challenge",
                description=QUEST_DESCRIPTIONS["combat"].format(topic=topic),
                choices=[
                    {"text": "Claim victory", "next_node_id": "victory"},
                ],
                rewards=["experience_25", "skill_10"],
                requirements=["experience_10"],
            ).model_dump()

            nodes["puzzle"] = QuestNode(
                node_id="puzzle",
                title="Puzzle Challenge",
                description=QUEST_DESCRIPTIONS["puzzle"].format(topic=topic),
                choices=[
                    {"text": "Find treasure", "next_node_id": "treasure"},
                ],
                rewards=["knowledge_20"],
                requirements=[],
            ).model_dump()

            nodes["treasure"] = QuestNode(
                node_id="treasure",
                title="Treasure Found",
                description=QUEST_DESCRIPTIONS["treasure"].format(topic=topic),
                choices=[
                    {"text": "Complete quest", "next_node_id": "victory"},
                ],
                rewards=["treasure_100", "experience_15"],
                requirements=[],
            ).model_dump()

        # Victory node
        nodes["victory"] = QuestNode(
            node_id="victory",
            title="Victory!",
            description=random.choice(VICTORY_MESSAGES).format(topic=topic),
            choices=[],
            rewards=["mastery_100"],
            requirements=[],
        ).model_dump()

        # Create game
        game = QuestGame(
            title=f"Quest for {topic.title()}",
            description=f"An interactive quest game about {topic}",
            start_node="start",
            nodes=nodes,
            victory_conditions=["reach_victory_node"],
            metadata={"difficulty": difficulty},
        )

        return game.model_dump()


__all__ = ["GameDesignerAgent"]
