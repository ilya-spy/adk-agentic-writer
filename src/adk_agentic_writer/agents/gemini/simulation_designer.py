"""Gemini-powered simulation designer agent.

Generates web simulations using LLM-powered text generation.
Inherits from ContentWriterAgent for unified structure.
"""

import logging
from typing import Any, Dict, List

from ...models.content_models import (
    WebSimulation,
    SimulationVariable,
    SimulationControl,
)
from ...teams.content_team import SIMULATION_WRITER
from ..content_writer import ContentWriterAgent
from ..text_provider import GeminiTextProvider

logger = logging.getLogger(__name__)


class GeminiSimulationDesignerAgent(ContentWriterAgent):
    """Gemini simulation designer using LLM-powered generation.

    Same structure as SimulationDesignerAgent but uses
    GeminiTextProvider for natural language generation.
    """

    def __init__(self, agent_id: str = "gemini_simulation_designer"):
        """Initialize Gemini simulation designer.

        Args:
            agent_id: Unique agent identifier
        """
        super().__init__(
            agent_id=agent_id,
            config=SIMULATION_WRITER,
            text_provider=GeminiTextProvider(),
        )
        logger.info(f"Initialized GeminiSimulationDesignerAgent {agent_id}")

    async def _build_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build web simulation content using LLM.

        Args:
            context: Parameters including topic, simulation_type, complexity

        Returns:
            WebSimulation dictionary
        """
        topic = context.get("topic", "physics")
        simulation_type = context.get("simulation_type", "interactive")
        complexity = context.get("complexity", "medium")

        logger.info(
            f"Generating simulation with Gemini: {topic}, type: {simulation_type}"
        )

        description = await self._generate_text(
            "simulation_description", {"topic": topic}
        )
        variables = self._generate_variables(topic, complexity)
        controls = self._generate_controls(topic, variables)
        rules = self._generate_rules(topic, variables)

        simulation = WebSimulation(
            title=f"{topic.title()} Simulation",
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
        """Generate simulation variables.

        Args:
            topic: Simulation topic
            complexity: Complexity level

        Returns:
            List of SimulationVariable objects
        """
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
        """Generate simulation controls.

        Args:
            topic: Simulation topic
            variables: Available variables

        Returns:
            List of SimulationControl objects
        """
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
        """Generate simulation rules.

        Args:
            topic: Simulation topic
            variables: Available variables

        Returns:
            List of rule strings
        """
        var_names = [v.name for v in variables]

        rules = [
            (
                f"{var_names[0]} changes based on rate"
                if len(var_names) > 1
                else f"Primary value changes over time"
            ),
            f"When values reach boundaries, they reflect or stop",
            f"Rate determines the speed of changes in {topic}",
        ]

        if "modifier" in var_names:
            rules.append("Modifier scales the rate of change")

        if "threshold" in var_names:
            rules.append("Special effects trigger when primary value exceeds threshold")

        return rules

    def _get_visualization_type(self, topic: str) -> str:
        """Determine appropriate visualization type.

        Args:
            topic: Simulation topic

        Returns:
            Visualization type string
        """
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


__all__ = ["GeminiSimulationDesignerAgent"]
