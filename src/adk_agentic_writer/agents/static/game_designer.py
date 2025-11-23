"""Game designer agent for creating quest games."""

import logging
from typing import Any, Dict

from ...models.agent_models import AgentRole, AgentStatus
from ...models.content_models import QuestGame, QuestNode
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)


class GameDesignerAgent(BaseAgent):
    """Agent specialized in creating quest-based games."""

    def __init__(self, agent_id: str = "game_designer_1", config: Dict[str, Any] | None = None):
        """Initialize the game designer agent."""
        super().__init__(agent_id, AgentRole.GAME_DESIGNER, config)

    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a quest game based on the given topic and parameters.

        Args:
            task_description: Description of the game to create
            parameters: Parameters including topic, complexity

        Returns:
            Dict containing the generated quest game
        """
        await self.update_status(AgentStatus.WORKING)
        
        topic = parameters.get("topic", "mystery")
        complexity = parameters.get("complexity", "medium")
        
        logger.info(f"Generating quest game about {topic} with {complexity} complexity")
        
        # Generate quest nodes
        nodes = await self._generate_quest_nodes(topic, complexity)
        
        # Create game object
        game = QuestGame(
            title=f"Quest for {topic.title()}",
            description=f"Embark on an epic quest to master {topic}",
            start_node="entrance",
            nodes=nodes,
            victory_conditions=[
                "Collect all key items",
                f"Complete understanding of {topic}",
                "Reach the final chamber",
            ],
        )
        
        await self.update_status(AgentStatus.COMPLETED)
        
        return game.model_dump()

    async def _generate_quest_nodes(self, topic: str, complexity: str) -> Dict[str, QuestNode]:
        """Generate quest nodes for the game."""
        nodes = {}
        
        # Entrance
        nodes["entrance"] = QuestNode(
            node_id="entrance",
            title="The Entrance",
            description=f"You stand at the entrance to the realm of {topic}. "
            "Three paths lie before you, each promising different challenges.",
            choices=[
                {"text": "Enter through the Ancient Portal", "next_node_id": "portal"},
                {"text": "Take the Forest Path", "next_node_id": "forest"},
                {"text": "Descend the Stone Steps", "next_node_id": "steps"},
            ],
            rewards=[],
            requirements=[],
        )
        
        # Portal path
        nodes["portal"] = QuestNode(
            node_id="portal",
            title="The Ancient Portal",
            description=f"The portal shimmers with energy related to {topic}. "
            "You discover ancient wisdom inscribed on the archway.",
            choices=[
                {"text": "Study the inscriptions", "next_node_id": "library"},
                {"text": "Step through the portal", "next_node_id": "chamber"},
            ],
            rewards=["Ancient Scroll"],
            requirements=[],
        )
        
        # Forest path
        nodes["forest"] = QuestNode(
            node_id="forest",
            title="The Whispering Forest",
            description=f"The forest seems alive with knowledge of {topic}. "
            "You hear whispers guiding you forward.",
            choices=[
                {"text": "Follow the whispers", "next_node_id": "grove"},
                {"text": "Search for the source", "next_node_id": "spring"},
            ],
            rewards=["Forest Token"],
            requirements=[],
        )
        
        # Steps path
        nodes["steps"] = QuestNode(
            node_id="steps",
            title="The Descending Steps",
            description=f"Each step down reveals more about {topic}. "
            "The path grows clearer with each descent.",
            choices=[
                {"text": "Continue descending", "next_node_id": "vault"},
                {"text": "Investigate the walls", "next_node_id": "library"},
            ],
            rewards=["Stone Key"],
            requirements=[],
        )
        
        # Library
        nodes["library"] = QuestNode(
            node_id="library",
            title="The Library of Knowledge",
            description=f"Countless volumes about {topic} line the shelves. "
            "You could spend a lifetime here.",
            choices=[
                {"text": "Take the essential texts", "next_node_id": "chamber"},
            ],
            rewards=["Knowledge Tome"],
            requirements=["Ancient Scroll"],
        )
        
        # Grove
        nodes["grove"] = QuestNode(
            node_id="grove",
            title="The Sacred Grove",
            description=f"The grove pulses with the essence of {topic}. "
            "Nature itself seems to teach you.",
            choices=[
                {"text": "Meditate in the grove", "next_node_id": "spring"},
            ],
            rewards=["Nature's Blessing"],
            requirements=["Forest Token"],
        )
        
        # Spring
        nodes["spring"] = QuestNode(
            node_id="spring",
            title="The Eternal Spring",
            description=f"Clear water reflects truths about {topic}. "
            "You gain clarity and purpose.",
            choices=[
                {"text": "Drink from the spring", "next_node_id": "chamber"},
            ],
            rewards=["Crystal Vial"],
            requirements=["Nature's Blessing"],
        )
        
        # Vault
        nodes["vault"] = QuestNode(
            node_id="vault",
            title="The Ancient Vault",
            description=f"The vault contains artifacts related to {topic}. "
            "Each one tells a story of mastery.",
            choices=[
                {"text": "Claim the artifacts", "next_node_id": "chamber"},
            ],
            rewards=["Master's Artifact"],
            requirements=["Stone Key"],
        )
        
        # Final chamber
        nodes["chamber"] = QuestNode(
            node_id="chamber",
            title="The Final Chamber",
            description=f"You've reached the heart of {topic}. "
            "All your collected wisdom comes together here. "
            "You have completed the quest!",
            choices=[],
            rewards=["Master's Crown", "Complete Understanding"],
            requirements=[],
        )
        
        return nodes

    async def generate_content(self, prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate game content based on prompt and parameters.

        Args:
            prompt: Content generation prompt
            parameters: Generation parameters

        Returns:
            Dict containing generated game
        """
        return await self.process_task(prompt, parameters)

    async def validate_content(self, content: Dict[str, Any]) -> bool:
        """
        Validate generated game content.

        Args:
            content: Game content to validate

        Returns:
            True if content is valid, False otherwise
        """
        try:
            # Validate game structure
            game = QuestGame(**content)
            
            # Check that we have nodes
            if not game.nodes:
                return False
            
            # Check that start node exists
            if game.start_node not in game.nodes:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Content validation failed: {e}")
            return False

    async def refine_content(self, content: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        Refine game content based on feedback.

        Args:
            content: Game content to refine
            feedback: Feedback for refinement

        Returns:
            Dict containing refined game
        """
        # For base implementation, just return the content
        # Subclasses can implement more sophisticated refinement
        logger.info(f"Refining game content based on feedback: {feedback}")
        return content
