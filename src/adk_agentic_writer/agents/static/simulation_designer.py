"""Simulation designer agent implementing ContentProtocol with StatefulAgent framework.

This agent generates web simulations using:
- StatefulAgent: For variable/parameter management
- Tasks: Predefined content generation tasks
- ContentProtocol: Standard content generation methods
"""

import logging
import random
from typing import Any, Dict, List, Optional

from ...agents.stateful_agent import StatefulAgent
from ...models.agent_models import AgentTask, AgentStatus
from ...models.content_models import WebSimulation, SimulationVariable
from ...protocols.content_protocol import ContentBlock, ContentBlockType, ContentPattern
from ...teams.content_team import SIMULATION_WRITER

logger = logging.getLogger(__name__)

# Simulation templates
SIMULATION_INTROS = [
    "Interactive simulation exploring {topic}",
    "Hands-on model demonstrating {topic}",
    "Dynamic simulation of {topic} concepts",
]

VARIABLE_TYPES = {
    "physics": ["mass", "velocity", "acceleration", "force", "energy"],
    "chemistry": ["temperature", "pressure", "volume", "concentration", "pH"],
    "biology": ["population", "growth_rate", "resources", "predators", "prey"],
    "economics": ["price", "demand", "supply", "cost", "revenue"],
}

INTERACTION_TYPES = ["slider", "button", "input", "toggle", "dropdown"]


class SimulationDesignerAgent(StatefulAgent):
    """Simulation designer agent using StatefulAgent framework.

    Implements:
    - AgentProtocol: process_task, update_status
    - ContentProtocol: generate_block, generate_sequential_blocks, etc.
    """

    def __init__(self, agent_id: str = "simulation_designer"):
        """Initialize simulation designer agent."""
        super().__init__(
            agent_id=agent_id,
            config=SIMULATION_WRITER,
        )
        logger.info(f"Initialized SimulationDesignerAgent {agent_id}")

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute task based on task_id."""
        # Extract context
        context = self.prepare_task_context(task)

        if task.task_id == "generate_block":
            block = await self.generate_block(ContentBlockType.CUSTOM, context)
            return block.content
        elif task.task_id == "generate_sequential_blocks":
            num_blocks = context.get("num_blocks", 3)
            blocks = await self.generate_sequential_blocks(
                num_blocks, ContentBlockType.CUSTOM, context
            )
            return {"blocks": [b.content for b in blocks]}
        else:
            # Default: generate simulation
            return await self._generate_simulation_content(resolved_prompt, context)

    # ========================================================================
    # ContentProtocol Implementation
    # ========================================================================

    async def generate_block(
        self,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        previous_blocks: Optional[List[ContentBlock]] = None,
    ) -> ContentBlock:
        """Generate a single simulation content block."""
        topic = context.get("topic", "physics")
        num_variables = context.get("num_variables", 5)

        simulation_data = await self._generate_simulation_data(
            topic, num_variables, "medium"
        )

        return ContentBlock(
            block_id=f"simulation_{topic.replace(' ', '_')}",
            block_type=block_type,
            content=simulation_data,
            pattern=ContentPattern.SEQUENTIAL,
        )

    async def generate_sequential_blocks(
        self,
        num_blocks: int,
        block_type: ContentBlockType,
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate sequential simulation modules."""
        blocks = []
        topic = context.get("topic", "physics")

        for i in range(num_blocks):
            module_topic = f"{topic} - Module {i+1}"
            simulation_data = await self._generate_simulation_data(
                module_topic, 3, "medium"
            )

            block = ContentBlock(
                block_id=f"module_{i+1}",
                block_type=block_type,
                content=simulation_data,
                pattern=ContentPattern.SEQUENTIAL,
                navigation={
                    "next": f"module_{i+2}" if i < num_blocks - 1 else None,
                    "prev": f"module_{i}" if i > 0 else None,
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
        """Generate looped simulation blocks (e.g., experiments)."""
        blocks = []
        topic = context.get("topic", "physics")

        for i in range(num_blocks):
            simulation_data = await self._generate_simulation_data(topic, 3, "medium")

            block = ContentBlock(
                block_id=f"experiment_{i+1}",
                block_type=block_type,
                content=simulation_data,
                pattern=ContentPattern.LOOPED,
                navigation={
                    "next": f"experiment_{(i+1) % num_blocks + 1}",
                    "prev": f"experiment_{i}" if allow_back and i > 0 else None,
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
        """Generate branched simulation blocks (e.g., scenario variations)."""
        blocks = []
        topic = context.get("topic", "physics")

        # Main simulation
        main_sim = await self._generate_simulation_data(topic, 4, "medium")
        main_block = ContentBlock(
            block_id="main_simulation",
            block_type=ContentBlockType.CUSTOM,
            content=main_sim,
            pattern=ContentPattern.BRANCHED,
            choices=[
                {"text": "Basic scenario", "next_block": "basic"},
                {"text": "Advanced scenario", "next_block": "advanced"},
            ],
        )
        blocks.append(main_block)

        # Variations
        for scenario in ["basic", "advanced"]:
            sim_data = await self._generate_simulation_data(
                f"{topic} ({scenario})", 3, scenario
            )
            block = ContentBlock(
                block_id=scenario,
                block_type=ContentBlockType.CUSTOM,
                content=sim_data,
                pattern=ContentPattern.BRANCHED,
            )
            blocks.append(block)

        return blocks

    async def generate_conditional_blocks(
        self,
        blocks_config: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate conditional simulation blocks."""
        blocks = []
        topic = context.get("topic", "physics")

        for config in blocks_config:
            condition = config.get("condition", {})
            simulation_data = await self._generate_simulation_data(topic, 3, "medium")

            block = ContentBlock(
                block_id=config.get("block_id", f"conditional_{len(blocks)}"),
                block_type=ContentBlockType.CUSTOM,
                content=simulation_data,
                pattern=ContentPattern.CONDITIONAL,
                metadata={"display_condition": condition},
            )
            blocks.append(block)

        return blocks

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _generate_simulation_content(
        self, resolved_prompt: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate simulation content from resolved prompt."""
        topic = context.get("topic", "physics")
        num_variables = context.get("num_variables", 5)
        complexity = context.get("complexity", "medium")

        return await self._generate_simulation_data(topic, num_variables, complexity)

    async def _generate_simulation_data(
        self, topic: str, num_variables: int, complexity: str
    ) -> Dict[str, Any]:
        """Generate web simulation data."""
        logger.info(
            f"Generating simulation: {topic}, variables: {num_variables}, complexity: {complexity}"
        )

        # Determine domain
        domain = "physics"
        topic_lower = topic.lower()
        for key in VARIABLE_TYPES.keys():
            if key in topic_lower:
                domain = key
                break

        # Generate variables
        variables = []
        available_vars = VARIABLE_TYPES.get(domain, VARIABLE_TYPES["physics"])
        selected_vars = random.sample(
            available_vars, min(num_variables, len(available_vars))
        )

        for i, var_name in enumerate(selected_vars):
            var = SimulationVariable(
                name=var_name,
                initial_value=50.0 + i * 10,
                min_value=0.0,
                max_value=100.0,
                unit=self._get_unit(var_name),
            )
            variables.append(var.model_dump())

        # Generate controls
        controls = []
        for i, var_name in enumerate(selected_vars[:3]):  # Max 3 controls
            controls.append(
                {
                    "id": f"control_{var_name}",
                    "type": random.choice(INTERACTION_TYPES),
                    "label": f"Adjust {var_name}",
                    "variable": var_name,
                }
            )

        # Create simulation
        from ...models.content_models import SimulationControl

        description = random.choice(SIMULATION_INTROS).format(topic=topic)

        # Create controls for variables
        controls = []
        for var in variables:
            control = SimulationControl(
                control_id=f"ctrl_{var['name']}",
                label=var["name"].replace("_", " ").title(),
                type="slider",
                affects=[var["name"]],
                parameters={
                    "min": var.get("min_value", 0),
                    "max": var.get("max_value", 100),
                    "step": var.get("step", 1.0),
                },
            )
            controls.append(control)

        # Create simulation rules
        rules = [
            f"{var['name']} affects outcome based on its value" for var in variables[:3]
        ]

        simulation = WebSimulation(
            title=f"{topic.title()} Simulation",
            description=description,
            variables=variables,
            controls=controls,
            rules=rules,
            visualization_type="chart",
            metadata={
                "complexity": complexity,
                "initial_state": {
                    var["name"]: var.get(
                        "initial_value", var.get("default_value", 50.0)
                    )
                    for var in variables
                },
                "axes": {
                    "x": selected_vars[0] if len(selected_vars) > 0 else "time",
                    "y": selected_vars[1] if len(selected_vars) > 1 else "value",
                },
            },
        )

        return simulation.model_dump()

    def _get_unit(self, variable_name: str) -> str:
        """Get unit for a variable."""
        units = {
            "mass": "kg",
            "velocity": "m/s",
            "acceleration": "m/s²",
            "force": "N",
            "energy": "J",
            "temperature": "°C",
            "pressure": "Pa",
            "volume": "L",
            "concentration": "mol/L",
            "pH": "",
            "population": "individuals",
            "growth_rate": "%",
            "resources": "units",
            "price": "$",
            "demand": "units",
            "supply": "units",
        }
        return units.get(variable_name, "units")


__all__ = ["SimulationDesignerAgent"]
