"""Designer agent for structural/interactive content (game, simulation)."""

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
from ...tasks.content_tasks import GENERATE_GAME, GENERATE_SIMULATION
from ...utils.content_registry import CONTENT_REGISTRY
from ...utils.text_provider import TextProvider, TemplateTextProvider
from ..content_agent import ContentWriterAgent

logger = logging.getLogger(__name__)


class DesignerAgent(ContentWriterAgent):
    """Designer publishes GENERATE_GAME and GENERATE_SIMULATION tasks."""

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
        # Publish both designer tasks
        self.supported_tasks.extend([GENERATE_GAME, GENERATE_SIMULATION])

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
            description = await self.generate_text(
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

    # Content builders - decides based on task_id in context
    async def _build_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        params = {**self._type_config.default_params, **context}
        task_id = context.get("task_id", "")
        if "game" in task_id:
            return await self._build_game(params)
        elif "simulation" in task_id:
            return await self._build_simulation(params)
        return await self._build_generic(params)

    async def _build_game(self, p: Dict[str, Any]) -> Dict[str, Any]:
        topic, complexity, num_nodes = (
            p.get("topic", "adventure"),
            p.get("complexity", "medium"),
            p.get("num_nodes", 5),
        )
        nodes = {}
        num_nodes = max(2, num_nodes)  # Min: start + mastery
        num_middle = num_nodes - 2  # Nodes between start and mastery

        # Start node
        title = await self.generate_text(
            "game_quest", {"topic": topic, "theme": p.get("theme", "fantasy")}
        )
        start_choices = []
        if num_middle > 0:
            start_choices = [{"text": "Begin quest", "next_node_id": "quest_0"}]
            if num_middle > 1:
                start_choices.append(
                    {
                        "text": "Skip to challenge",
                        "next_node_id": f"quest_{num_middle-1}",
                    }
                )
        else:
            start_choices = [{"text": "Complete quest", "next_node_id": "mastery"}]

        nodes["start"] = await self.generate_node(
            "start", title, f"Begin your journey into {topic}.", start_choices
        )

        # Generate middle quest nodes dynamically
        quest_titles = [
            "Learning Basics",
            "The Challenge",
            "Intermediate",
            "Advanced",
            "Expert Level",
            "Final Trial",
            "Hidden Path",
            "Secret Quest",
        ]
        xp_per_node = 50

        for i in range(num_middle):
            is_last = i == num_middle - 1
            node_title = quest_titles[i % len(quest_titles)]

            # Choices: next node or skip to mastery
            choices = []
            if is_last:
                choices = [{"text": "To mastery", "next_node_id": "mastery"}]
            else:
                choices = [{"text": "Continue", "next_node_id": f"quest_{i+1}"}]
                if i + 2 <= num_middle - 1:
                    choices.append(
                        {"text": "Skip ahead", "next_node_id": f"quest_{i+2}"}
                    )

            # Requirements based on complexity
            reqs = []
            if complexity != "simple" and i > 0:
                reqs = [f"Quest {i} Badge"]

            nodes[f"quest_{i}"] = await self.generate_node(
                f"quest_{i}",
                node_title,
                topic=topic,
                choices=choices,
                rewards=[f"Quest {i+1} Badge", f"{(i+1) * xp_per_node} XP"],
                requirements=reqs,
            )

        # Mastery node (ending)
        final_reqs = (
            [f"Quest {num_middle} Badge"]
            if complexity != "simple" and num_middle > 0
            else []
        )
        nodes["mastery"] = await self.generate_node(
            "mastery",
            f"Mastery of {topic.title()}",
            f"Congratulations! You mastered {topic}.",
            [],
            [f"{topic.title()} Master", f"{num_nodes * 100} XP"],
            final_reqs,
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
            description=await self.generate_text(
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
