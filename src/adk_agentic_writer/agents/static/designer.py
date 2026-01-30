"""Designer agent for structural/interactive content with universal block generators."""

import logging
from typing import Any, Dict, List, Optional

from ...models.content_models import (
    ContentBlock,
    ContentBlockType,
    ContentPattern,
    QuestGame,
    QuestNode,
    SimulationControl,
    SimulationVariable,
    WebSimulation,
)
from ...utils.content_registry import CONTENT_REGISTRY
from ...utils.text_provider import TextProvider, TemplateTextProvider
from ..content_agent import ContentWriterAgent

logger = logging.getLogger(__name__)


class DesignerAgent(ContentWriterAgent):
    """Designer implementing ContentProtocol with universal block generators."""

    def __init__(
        self,
        agent_id: str = "designer",
        content_type: str = "game",
        text_provider: Optional[TextProvider] = None,
    ):
        self._content_type = content_type
        config = CONTENT_REGISTRY.get(content_type)
        if not config:
            raise ValueError(f"Unknown content type: {content_type}")
        if config.category != "designer":
            raise ValueError(f"Content type '{content_type}' is not a designer type")
        self._type_config = config
        super().__init__(
            agent_id,
            config.agent_config,
            text_provider=text_provider or TemplateTextProvider(),
        )

    @property
    def content_type(self) -> str:
        return self._content_type

    # ContentProtocol
    async def generate_block(
        self,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        previous_blocks: Optional[List[ContentBlock]] = None,
    ) -> ContentBlock:
        """Generate a single content block."""
        block_id = context.get("block_id", f"{block_type.value}_{id(context)}")

        if block_type == ContentBlockType.NODE:
            content = (await self.generate_node(**context)).model_dump()
        elif block_type == ContentBlockType.CARD:
            content = self.generate_variable(**context).model_dump()
        elif block_type == ContentBlockType.SECTION:
            content = self.generate_control(**context).model_dump()
        else:
            content = {"data": context}

        return ContentBlock(
            block_id=block_id,
            block_type=block_type,
            content=content,
            pattern=context.get("pattern", ContentPattern.SEQUENTIAL),
            metadata=context.get("metadata", {}),
        )

    async def generate_patterned_blocks(
        self,
        block_type: ContentBlockType,
        pattern: ContentPattern,
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate blocks with navigation based on pattern."""
        count, blocks = context.get("count", 3), []
        for i in range(count):
            block = await self.generate_block(
                block_type,
                {**context, "block_id": f"{block_type.value}_{i}", "index": i},
            )
            block.pattern = pattern
            if pattern == ContentPattern.SEQUENTIAL and i < count - 1:
                block.navigation = {"next": f"{block_type.value}_{i + 1}"}
            elif pattern == ContentPattern.LOOPED:
                block.navigation = {"next": f"{block_type.value}_{(i + 1) % count}"}
                block.exit_condition = context.get(
                    "exit_condition", {"max_iterations": 3}
                )
            elif pattern == ContentPattern.BRANCHED:
                block.choices = [
                    {"text": f"Go to {j}", "target": f"{block_type.value}_{j}"}
                    for j in range(count)
                    if j != i
                ]
            blocks.append(block)
        return blocks

    # Universal Block Generators
    def generate_variable(
        self,
        name: str,
        initial_value: float = 50.0,
        min_value: float = 0.0,
        max_value: float = 100.0,
        unit: str = "units",
        **_,
    ) -> SimulationVariable:
        """Create a controllable variable."""
        return SimulationVariable(
            name=name,
            initial_value=initial_value,
            min_value=min_value,
            max_value=max_value,
            unit=unit,
        )

    def generate_control(
        self,
        control_id: str,
        label: str,
        control_type: str = "slider",
        affects: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        **_,
    ) -> SimulationControl:
        """Create a user control (slider, button, toggle)."""
        return SimulationControl(
            control_id=control_id,
            label=label,
            type=control_type,
            affects=affects or [],
            parameters=parameters or {},
        )

    def generate_rule(
        self,
        description: str,
        variables: Optional[List[str]] = None,
        condition: Optional[str] = None,
        **_,
    ) -> Dict[str, Any]:
        """Create a behavior rule."""
        return {
            "description": description,
            "variables": variables or [],
            "condition": condition,
        }

    async def generate_node(
        self,
        node_id: str,
        title: str,
        description: Optional[str] = None,
        choices: Optional[List[Dict[str, str]]] = None,
        rewards: Optional[List[str]] = None,
        requirements: Optional[List[str]] = None,
        **kwargs,
    ) -> QuestNode:
        """Create a navigation node with choices."""
        if description is None:
            description = await self._generate_text(
                "game_objective",
                {"topic": kwargs.get("topic", "adventure"), "aspect": title},
            )
        return QuestNode(
            node_id=node_id,
            title=title,
            description=description,
            choices=choices or [],
            rewards=rewards or [],
            requirements=requirements or [],
        )

    # Batch generators
    def generate_variables_set(
        self, topic: str, complexity: str = "medium"
    ) -> List[SimulationVariable]:
        """Generate related variables based on complexity."""
        name = f"primary_{topic.replace(' ', '_')}"
        vars = [
            self.generate_variable(name, 50, 0, 100, "units"),
            self.generate_variable("rate", 1, 0.1, 10, "per second"),
        ]
        if complexity in ("medium", "complex"):
            vars.append(self.generate_variable("modifier", 1, 0.5, 2, "x"))
        if complexity == "complex":
            vars.append(self.generate_variable("threshold", 75, 0, 100, "units"))
        return vars

    def generate_controls_for_variables(
        self, variables: List[SimulationVariable], include_playback: bool = True
    ) -> List[SimulationControl]:
        """Generate controls for variables with optional playback buttons."""
        controls = []
        if include_playback:
            controls.append(
                self.generate_control(
                    "start_stop",
                    "Start/Stop",
                    "button",
                    ["simulation_running"],
                    {"action": "toggle"},
                )
            )
            controls.append(
                self.generate_control(
                    "reset",
                    "Reset",
                    "button",
                    [v.name for v in variables],
                    {"action": "reset"},
                )
            )
        for v in variables:
            controls.append(
                self.generate_control(
                    f"slider_{v.name}",
                    f"Adjust {v.name.replace('_', ' ').title()}",
                    "slider",
                    [v.name],
                    {"min": v.min_value, "max": v.max_value, "step": 1.0},
                )
            )
        return controls

    def generate_rules_for_variables(
        self, topic: str, variables: List[SimulationVariable]
    ) -> List[str]:
        """Generate rule descriptions for variables."""
        names = [v.name for v in variables]
        rules = [
            (
                f"{names[0]} changes based on rate"
                if len(names) > 1
                else "Primary value changes over time"
            ),
            "Values reflect or stop at boundaries",
            f"Rate controls speed of {topic} changes",
        ]
        if "modifier" in names:
            rules.append("Modifier scales rate of change")
        if "threshold" in names:
            rules.append("Special effects when primary exceeds threshold")
        return rules

    # Content builders
    async def _build_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        params = {**self._type_config.default_params, **context}
        if self._content_type in ("quest_game", "game"):
            return await self._build_game(params)
        elif self._content_type in ("web_simulation", "simulation"):
            return await self._build_simulation(params)
        return await self._build_generic(params)

    async def _build_game(self, p: Dict[str, Any]) -> Dict[str, Any]:
        topic, complexity, num_nodes = (
            p.get("topic", "adventure"),
            p.get("complexity", "medium"),
            p.get("num_nodes", 5),
        )
        nodes = {}

        # Start
        title = await self._generate_text(
            "game_quest", {"topic": topic, "theme": p.get("theme", "fantasy")}
        )
        nodes["start"] = await self.generate_node(
            "start",
            title,
            f"Begin your journey into {topic}.",
            [
                {"text": "Explore basics", "next_node_id": "basics"},
                {"text": "Take challenge", "next_node_id": "challenge"},
            ],
        )

        # Progressive nodes
        if num_nodes >= 3:
            nodes["basics"] = await self.generate_node(
                "basics",
                "Learning Basics",
                topic=topic,
                choices=[
                    {"text": "To intermediate", "next_node_id": "intermediate"},
                    {"text": "Try challenge", "next_node_id": "challenge"},
                ],
                rewards=["Basic Knowledge", "50 XP"],
            )
        if num_nodes >= 4:
            nodes["challenge"] = await self.generate_node(
                "challenge",
                "The Challenge",
                topic=topic,
                choices=[{"text": "To mastery", "next_node_id": "mastery"}],
                rewards=["Challenge Badge", "100 XP"],
                requirements=["Basic Knowledge"] if complexity != "simple" else [],
            )
        if num_nodes >= 5 and complexity != "simple":
            nodes["intermediate"] = await self.generate_node(
                "intermediate",
                "Intermediate",
                topic=topic,
                choices=[{"text": "To mastery", "next_node_id": "mastery"}],
                rewards=["Intermediate Badge", "150 XP"],
                requirements=["Basic Knowledge"],
            )

        # Mastery (ending)
        nodes["mastery"] = await self.generate_node(
            "mastery",
            f"Mastery of {topic.title()}",
            f"Congratulations! You mastered {topic}.",
            [],
            [f"{topic.title()} Master", "500 XP"],
            ["Challenge Badge"] if complexity != "simple" else [],
        )

        return QuestGame(
            title=self._type_config.title_template.format(topic=topic.title()),
            description=self._type_config.description_template.format(topic=topic),
            start_node="start",
            nodes={k: v.model_dump() for k, v in nodes.items()},
            victory_conditions=[f"Complete all quests to master {topic}"],
        ).model_dump()

    async def _build_simulation(self, p: Dict[str, Any]) -> Dict[str, Any]:
        topic, complexity = p.get("topic", "physics"), p.get("complexity", "medium")
        variables = self.generate_variables_set(topic, complexity)
        return WebSimulation(
            title=self._type_config.title_template.format(topic=topic.title()),
            description=await self._generate_text(
                "simulation_description", {"topic": topic}
            ),
            variables=variables,
            controls=self.generate_controls_for_variables(variables),
            rules=self.generate_rules_for_variables(topic, variables),
            visualization_type=self._get_viz_type(topic),
        ).model_dump()

    def _get_viz_type(self, topic: str) -> str:
        t = topic.lower()
        if any(w in t for w in ("graph", "chart", "data")):
            return "chart"
        if any(w in t for w in ("physics", "motion", "wave")):
            return "animation"
        if any(w in t for w in ("3d", "space", "volume")):
            return "3d"
        return "chart"

    async def _build_generic(self, p: Dict[str, Any]) -> Dict[str, Any]:
        topic = p.get("topic", "general")
        return self._type_config.model_class(
            title=self._type_config.title_template.format(topic=topic.title()),
            description=self._type_config.description_template.format(topic=topic),
            **{k: v for k, v in p.items() if k != "topic"},
        ).model_dump()


# Aliases
class GameDesignerAgent(DesignerAgent):
    def __init__(self, agent_id: str = "game_designer"):
        super().__init__(agent_id, "game")


class SimulationDesignerAgent(DesignerAgent):
    def __init__(self, agent_id: str = "simulation_designer"):
        super().__init__(agent_id, "simulation")


def create_game_designer(agent_id: str = "game_designer") -> DesignerAgent:
    return DesignerAgent(agent_id, "game")


def create_simulation_designer(agent_id: str = "simulation_designer") -> DesignerAgent:
    return DesignerAgent(agent_id, "simulation")


__all__ = [
    "DesignerAgent",
    "GameDesignerAgent",
    "SimulationDesignerAgent",
    "create_game_designer",
    "create_simulation_designer",
]
