"""Unified designer agent for structural/interactive content.

Handles multiple content types (Game, Simulation) using a registry pattern.
New structural content types can be added via the content registry
without creating new agent classes.
"""

import logging
from typing import Any, Dict, List, Optional

from ...models.content_models import (
    QuestGame,
    QuestNode,
    WebSimulation,
    SimulationVariable,
    SimulationControl,
)
from ..content_agent import ContentWriterAgent
from ...utils.content_registry import CONTENT_REGISTRY, ContentTypeConfig
from ...utils.text_provider import TextProvider, TemplateTextProvider

logger = logging.getLogger(__name__)


class DesignerAgent(ContentWriterAgent):
    """Unified designer agent for structural content generation.

    Supports multiple content types via the content registry:
    - quest_game/game: Interactive quest-based games
    - web_simulation/simulation: Interactive simulations

    New content types can be registered without modifying this class.
    """

    def __init__(
        self,
        agent_id: str = "designer",
        content_type: str = "game",
        text_provider: Optional[TextProvider] = None,
    ):
        """Initialize unified designer agent.

        Args:
            agent_id: Unique agent identifier
            content_type: Type of content to generate (game, simulation, etc.)
            text_provider: Optional custom text provider
        """
        self._content_type = content_type
        config = CONTENT_REGISTRY.get(content_type)

        if not config:
            raise ValueError(f"Unknown content type: {content_type}")
        if config.category != "designer":
            raise ValueError(f"Content type '{content_type}' is not a designer type")

        self._type_config = config

        super().__init__(
            agent_id=agent_id,
            config=config.agent_config,
            text_provider=text_provider or TemplateTextProvider(),
        )
        logger.info(f"Initialized DesignerAgent {agent_id} for {content_type}")

    @property
    def content_type(self) -> str:
        """Get the content type this designer handles."""
        return self._content_type

    async def _build_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build content based on registered type.

        Args:
            context: Parameters for content generation

        Returns:
            Content dictionary
        """
        # Merge default params with provided context
        params = {**self._type_config.default_params, **context}
        topic = params.get("topic", "general")

        logger.info(f"Building {self._content_type} content for: {topic}")

        # Route to appropriate builder
        if self._content_type in ("quest_game", "game"):
            return await self._build_game(params)
        elif self._content_type in ("web_simulation", "simulation"):
            return await self._build_simulation(params)
        else:
            # Generic fallback
            return await self._build_generic(params)

    # =========================================================================
    # Game Builder
    # =========================================================================

    async def _build_game(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build quest game content.

        Args:
            params: Parameters including topic, complexity, theme, num_nodes

        Returns:
            QuestGame dictionary
        """
        topic = params.get("topic", "adventure")
        complexity = params.get("complexity", "medium")
        theme = params.get("theme", "fantasy")
        num_nodes = params.get("num_nodes", 5)

        logger.info(f"Generating game: {topic}, complexity: {complexity}")

        nodes = await self._generate_game_nodes(topic, theme, num_nodes, complexity)

        game = QuestGame(
            title=self._type_config.title_template.format(topic=topic.title()),
            description=self._type_config.description_template.format(topic=topic),
            start_node="start",
            nodes=nodes,
            victory_conditions=[f"Complete all quests to master {topic}"],
        )

        return game.model_dump()

    async def _generate_game_nodes(
        self, topic: str, theme: str, num_nodes: int, complexity: str
    ) -> Dict[str, QuestNode]:
        """Generate game quest nodes."""
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
                choices=[{"text": "Proceed to mastery", "next_node_id": "mastery"}],
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
                choices=[{"text": "Advance to mastery", "next_node_id": "mastery"}],
                rewards=["Intermediate Badge", "150 XP"],
                requirements=["Basic Knowledge"],
            )

        # Mastery node (ending)
        nodes["mastery"] = QuestNode(
            node_id="mastery",
            title=f"Mastery of {topic.title()}",
            description=f"Congratulations! You have achieved mastery in {topic}.",
            choices=[],
            rewards=[f"{topic.title()} Master Badge", "500 XP"],
            requirements=["Challenge Badge"] if complexity != "simple" else [],
        )

        return nodes

    # =========================================================================
    # Simulation Builder
    # =========================================================================

    async def _build_simulation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build web simulation content.

        Args:
            params: Parameters including topic, simulation_type, complexity

        Returns:
            WebSimulation dictionary
        """
        topic = params.get("topic", "physics")
        simulation_type = params.get("simulation_type", "interactive")
        complexity = params.get("complexity", "medium")

        logger.info(f"Generating simulation: {topic}, type: {simulation_type}")

        description = await self._generate_text(
            "simulation_description", {"topic": topic}
        )
        variables = self._generate_variables(topic, complexity)
        controls = self._generate_controls(topic, variables)
        rules = self._generate_rules(topic, variables)

        simulation = WebSimulation(
            title=self._type_config.title_template.format(topic=topic.title()),
            description=description,
            variables=variables,
            controls=controls,
            rules=rules,
            visualization_type=self._get_visualization_type(topic),
        )

        return simulation.model_dump()

    def _generate_variables(
        self, topic: str, complexity: str
    ) -> List[SimulationVariable]:
        """Generate simulation variables."""
        variables = [
            SimulationVariable(
                name=f"primary_{topic.replace(' ', '_')}",
                initial_value=50.0,
                min_value=0.0,
                max_value=100.0,
                unit="units",
            ),
            SimulationVariable(
                name="rate",
                initial_value=1.0,
                min_value=0.1,
                max_value=10.0,
                unit="per second",
            ),
        ]

        if complexity in ["medium", "complex"]:
            variables.append(
                SimulationVariable(
                    name="modifier",
                    initial_value=1.0,
                    min_value=0.5,
                    max_value=2.0,
                    unit="x",
                )
            )

        if complexity == "complex":
            variables.append(
                SimulationVariable(
                    name="threshold",
                    initial_value=75.0,
                    min_value=0.0,
                    max_value=100.0,
                    unit="units",
                )
            )

        return variables

    def _generate_controls(
        self, topic: str, variables: List[SimulationVariable]
    ) -> List[SimulationControl]:
        """Generate simulation controls."""
        controls = [
            SimulationControl(
                control_id="start_stop",
                label="Start/Stop",
                type="button",
                affects=["simulation_running"],
                parameters={"action": "toggle"},
            ),
            SimulationControl(
                control_id="reset",
                label="Reset",
                type="button",
                affects=[v.name for v in variables],
                parameters={"action": "reset"},
            ),
        ]

        # Add sliders for numeric variables
        for var in variables:
            controls.append(
                SimulationControl(
                    control_id=f"slider_{var.name}",
                    label=f"Adjust {var.name.replace('_', ' ').title()}",
                    type="slider",
                    affects=[var.name],
                    parameters={
                        "min": var.min_value,
                        "max": var.max_value,
                        "step": 1.0,
                    },
                )
            )

        return controls

    def _generate_rules(
        self, topic: str, variables: List[SimulationVariable]
    ) -> List[str]:
        """Generate simulation rules."""
        var_names = [v.name for v in variables]

        rules = [
            (
                f"{var_names[0]} changes based on rate"
                if len(var_names) > 1
                else "Primary value changes over time"
            ),
            "When values reach boundaries, they reflect or stop",
            f"Rate determines the speed of changes in {topic}",
        ]

        if "modifier" in var_names:
            rules.append("Modifier scales the rate of change")

        if "threshold" in var_names:
            rules.append("Special effects trigger when primary value exceeds threshold")

        return rules

    def _get_visualization_type(self, topic: str) -> str:
        """Determine appropriate visualization type."""
        topic_lower = topic.lower()

        if any(
            word in topic_lower for word in ["graph", "chart", "data", "statistics"]
        ):
            return "chart"
        elif any(
            word in topic_lower for word in ["physics", "motion", "particle", "wave"]
        ):
            return "animation"
        elif any(word in topic_lower for word in ["3d", "space", "volume"]):
            return "3d"
        else:
            return "chart"

    # =========================================================================
    # Generic Builder (for future extensibility)
    # =========================================================================

    async def _build_generic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generic builder for new content types."""
        topic = params.get("topic", "general")
        model_class = self._type_config.model_class

        return model_class(
            title=self._type_config.title_template.format(topic=topic.title()),
            description=self._type_config.description_template.format(topic=topic),
            **{k: v for k, v in params.items() if k not in ("topic",)},
        ).model_dump()


# Convenience factory functions
def create_game_designer(agent_id: str = "game_designer") -> DesignerAgent:
    """Create a designer agent configured for games."""
    return DesignerAgent(agent_id=agent_id, content_type="game")


def create_simulation_designer(agent_id: str = "simulation_designer") -> DesignerAgent:
    """Create a designer agent configured for simulations."""
    return DesignerAgent(agent_id=agent_id, content_type="simulation")


# Backward-compatible class aliases
class GameDesignerAgent(DesignerAgent):
    """Backward-compatible alias for game designer."""

    def __init__(self, agent_id: str = "game_designer"):
        super().__init__(agent_id=agent_id, content_type="game")


class SimulationDesignerAgent(DesignerAgent):
    """Backward-compatible alias for simulation designer."""

    def __init__(self, agent_id: str = "simulation_designer"):
        super().__init__(agent_id=agent_id, content_type="simulation")


__all__ = [
    "DesignerAgent",
    "GameDesignerAgent",
    "SimulationDesignerAgent",
    "create_game_designer",
    "create_simulation_designer",
]
