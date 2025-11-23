"""Gemini-powered game designer agent using Google ADK."""

import json
import logging
from typing import Any, Dict

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

from ...models.agent_models import AGENT_TEAM_CONFIGS, AgentRole, AgentStatus
from ...models.content_models import QuestGame, QuestNode
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)


class GeminiGameDesignerAgent(BaseAgent):
    """Agent specialized in creating quest games using Google ADK."""

    def __init__(
        self,
        agent_id: str = "gemini_game_designer_1",
        config: Dict[str, Any] | None = None,
    ):
        """Initialize the Gemini game designer agent with Google ADK."""
        super().__init__(agent_id, AgentRole.GAME_DESIGNER, config)
        
        # Get system instruction from AGENT_TEAM_CONFIGS
        agent_config = AGENT_TEAM_CONFIGS.get(AgentRole.GAME_DESIGNER)
        
        # Create Google ADK Agent instance
        self.adk_agent = Agent(
            name="GameDesignerAgent",
            model=Gemini(model="gemini-2.0-flash-exp"),
            instruction=agent_config.system_instruction if agent_config else self._get_default_instruction(),
            output_key="game_content",
        )
        self.runner = InMemoryRunner(agent=self.adk_agent)
    
    def _get_default_instruction(self) -> str:
        """Default instruction if not in config."""
        return """You are an expert game designer specializing in quest-based adventure games.
Create engaging, balanced, and fun interactive game experiences."""

    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a quest game based on the given topic and parameters.

        Args:
            task_description: Description of the game to create
            parameters: Parameters including topic, complexity, theme

        Returns:
            Dict containing the generated quest game
        """
        await self.update_status(AgentStatus.WORKING)

        topic = parameters.get("topic", "adventure")
        complexity = parameters.get("complexity", "medium")
        theme = parameters.get("theme", "fantasy")

        logger.info(f"Generating quest game about {topic} with {complexity} complexity using Google ADK")

        # Generate game using Google ADK Agent
        game_data = await self._generate_game_with_adk(topic, complexity, theme)

        await self.update_status(AgentStatus.COMPLETED)

        return game_data

    async def _generate_game_with_adk(
        self, topic: str, complexity: str, theme: str
    ) -> Dict[str, Any]:
        """Generate quest game using Google ADK Agent."""
        
        prompt = f"""Create an interactive quest-based game with the following specifications:

Topic: {topic}
Complexity: {complexity}
Theme: {theme}

Design a game with:
- A clear starting point and objective
- Multiple quest nodes with choices
- Items/rewards to collect
- Requirements/prerequisites for certain paths
- Victory conditions
- At least 5-7 interconnected nodes

Return the game in the following JSON format:
{{
    "title": "Game title",
    "description": "Game overview and objective",
    "start_node": "start",
    "victory_conditions": ["Collect the ancient artifact", "Defeat the final boss"],
    "nodes": {{
        "start": {{
            "node_id": "start",
            "title": "The Beginning",
            "description": "You start your quest...",
            "choices": [
                {{"text": "Go to the village", "next_node_id": "village"}},
                {{"text": "Explore the forest", "next_node_id": "forest"}}
            ],
            "rewards": [],
            "requirements": []
        }},
        "village": {{
            "node_id": "village",
            "title": "Village Square",
            "description": "A bustling village...",
            "choices": [...],
            "rewards": ["sword", "map"],
            "requirements": []
        }}
    }}
}}

Make the game engaging with meaningful choices, interesting rewards, and clear progression."""

        try:
            # Run Google ADK Agent
            result = await self.runner.run(input_data={})
            
            # Parse result
            game_data = json.loads(result.get("game_content", "{}")) if isinstance(result.get("game_content"), str) else result.get("game_content", {})
            
            # Validate and create QuestGame object
            nodes_dict = {}
            for node_id, node_data in game_data.get("nodes", {}).items():
                nodes_dict[node_id] = QuestNode(**node_data)
            
            game = QuestGame(
                title=game_data.get("title", f"{topic.title()} Quest"),
                description=game_data.get("description", f"An adventure game about {topic}"),
                start_node=game_data.get("start_node", "start"),
                nodes=nodes_dict,
                victory_conditions=game_data.get("victory_conditions", ["Complete the quest"]),
            )
            
            return game.model_dump()

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error generating game with Google ADK: {e}")
            return await self._generate_fallback_game(topic, theme)

    async def _generate_fallback_game(self, topic: str, theme: str) -> Dict[str, Any]:
        """Fallback game generation."""
        logger.warning("Using fallback game generation")
        
        nodes = {
            "start": QuestNode(
                node_id="start",
                title="The Quest Begins",
                description=f"Your quest about {topic} starts here!",
                choices=[
                    {"text": "Accept the quest", "next_node_id": "quest1"},
                    {"text": "Prepare first", "next_node_id": "prepare"},
                ],
                rewards=[],
                requirements=[],
            ),
            "prepare": QuestNode(
                node_id="prepare",
                title="Preparation",
                description="You gather supplies and information.",
                choices=[{"text": "Begin the quest", "next_node_id": "quest1"}],
                rewards=["map", "supplies"],
                requirements=[],
            ),
            "quest1": QuestNode(
                node_id="quest1",
                title="The Challenge",
                description="You face the main challenge!",
                choices=[{"text": "Complete the quest", "next_node_id": "victory"}],
                rewards=[],
                requirements=[],
            ),
            "victory": QuestNode(
                node_id="victory",
                title="Victory!",
                description="You have completed the quest successfully!",
                choices=[],
                rewards=["trophy", "achievement"],
                requirements=[],
            ),
        }

        game = QuestGame(
            title=f"{topic.title()} Quest",
            description=f"An adventure game about {topic}",
            start_node="start",
            nodes=nodes,
            victory_conditions=["Reach the victory node"],
        )

        return game.model_dump()


