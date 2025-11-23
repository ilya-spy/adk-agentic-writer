"""Simulation designer agent for creating interactive web simulations."""

import logging
from typing import Any, Dict

from ...models.agent_models import AgentRole, AgentStatus
from ...models.content_models import SimulationControl, SimulationVariable, WebSimulation
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SimulationDesignerAgent(BaseAgent):
    """Agent specialized in creating interactive web simulations."""

    def __init__(self, agent_id: str = "simulation_designer_1", config: Dict[str, Any] | None = None):
        """Initialize the simulation designer agent."""
        super().__init__(agent_id, AgentRole.SIMULATION_DESIGNER, config)

    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a web simulation based on the given topic and parameters.

        Args:
            task_description: Description of the simulation to create
            parameters: Parameters including topic, simulation_type

        Returns:
            Dict containing the generated simulation
        """
        await self.update_status(AgentStatus.WORKING)
        
        topic = parameters.get("topic", "physics")
        simulation_type = parameters.get("simulation_type", "chart")
        
        logger.info(f"Generating web simulation about {topic}")
        
        # Generate simulation components
        variables = await self._generate_variables(topic)
        controls = await self._generate_controls(topic, variables)
        rules = await self._generate_rules(topic)
        
        # Create simulation object
        simulation = WebSimulation(
            title=f"Interactive {topic.title()} Simulation",
            description=f"Explore the dynamics of {topic} through interactive controls",
            variables=variables,
            controls=controls,
            rules=rules,
            visualization_type=simulation_type,
        )
        
        await self.update_status(AgentStatus.COMPLETED)
        
        return simulation.model_dump()

    async def _generate_variables(self, topic: str) -> list[SimulationVariable]:
        """Generate simulation variables based on the topic."""
        # Template-based variable generation
        variables = []
        
        if "physics" in topic.lower():
            variables = [
                SimulationVariable(
                    name="velocity",
                    initial_value=0.0,
                    min_value=-100.0,
                    max_value=100.0,
                    unit="m/s",
                ),
                SimulationVariable(
                    name="acceleration",
                    initial_value=9.8,
                    min_value=-50.0,
                    max_value=50.0,
                    unit="m/s²",
                ),
                SimulationVariable(
                    name="position",
                    initial_value=0.0,
                    min_value=-1000.0,
                    max_value=1000.0,
                    unit="m",
                ),
            ]
        elif "econ" in topic.lower():
            variables = [
                SimulationVariable(
                    name="supply",
                    initial_value=100.0,
                    min_value=0.0,
                    max_value=1000.0,
                    unit="units",
                ),
                SimulationVariable(
                    name="demand",
                    initial_value=100.0,
                    min_value=0.0,
                    max_value=1000.0,
                    unit="units",
                ),
                SimulationVariable(
                    name="price",
                    initial_value=10.0,
                    min_value=0.0,
                    max_value=100.0,
                    unit="$",
                ),
            ]
        else:
            # Generic variables
            variables = [
                SimulationVariable(
                    name="input_factor",
                    initial_value=50.0,
                    min_value=0.0,
                    max_value=100.0,
                    unit="units",
                ),
                SimulationVariable(
                    name="output_result",
                    initial_value=50.0,
                    min_value=0.0,
                    max_value=100.0,
                    unit="units",
                ),
                SimulationVariable(
                    name="efficiency",
                    initial_value=1.0,
                    min_value=0.0,
                    max_value=2.0,
                    unit="ratio",
                ),
            ]
        
        return variables

    async def _generate_controls(
        self, topic: str, variables: list[SimulationVariable]
    ) -> list[SimulationControl]:
        """Generate interactive controls for the simulation."""
        controls = []
        
        # Create a control for each variable
        for var in variables:
            # Calculate safe step value
            value_range = var.max_value - var.min_value
            step = value_range / 100 if value_range > 0 else 1.0
            
            control = SimulationControl(
                control_id=f"{var.name}_slider",
                label=f"Adjust {var.name.replace('_', ' ').title()}",
                type="slider",
                affects=[var.name],
                parameters={
                    "min": var.min_value,
                    "max": var.max_value,
                    "step": step,
                    "initial": var.initial_value,
                },
            )
            controls.append(control)
        
        # Add control buttons
        controls.append(
            SimulationControl(
                control_id="reset_button",
                label="Reset Simulation",
                type="button",
                affects=[var.name for var in variables],
                parameters={"action": "reset"},
            )
        )
        
        controls.append(
            SimulationControl(
                control_id="play_pause",
                label="Play/Pause",
                type="toggle",
                affects=["simulation_state"],
                parameters={"states": ["playing", "paused"]},
            )
        )
        
        return controls

    async def _generate_rules(self, topic: str) -> list[str]:
        """Generate simulation rules/equations."""
        rules = []
        
        if "physics" in topic.lower():
            rules = [
                "velocity = velocity + acceleration * dt",
                "position = position + velocity * dt",
                "if position < 0: velocity = -velocity * 0.8  # Bounce with damping",
            ]
        elif "econ" in topic.lower():
            rules = [
                "equilibrium = (supply + demand) / 2",
                "price = equilibrium * 0.1",
                "if supply > demand: price = price * 0.95",
                "if demand > supply: price = price * 1.05",
            ]
        else:
            rules = [
                "output_result = input_factor * efficiency",
                "if output_result > 100: output_result = 100",
                "if output_result < 0: output_result = 0",
            ]
        
        return rules

    async def generate_content(self, prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate simulation content based on prompt and parameters.

        Args:
            prompt: Content generation prompt
            parameters: Generation parameters

        Returns:
            Dict containing generated simulation
        """
        return await self.process_task(prompt, parameters)

    async def validate_content(self, content: Dict[str, Any]) -> bool:
        """
        Validate generated simulation content.

        Args:
            content: Simulation content to validate

        Returns:
            True if content is valid, False otherwise
        """
        try:
            # Validate simulation structure
            simulation = WebSimulation(**content)
            
            # Check that we have variables and controls
            if not simulation.variables or not simulation.controls:
                return False
            
            # Check that we have rules
            if not simulation.rules:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Content validation failed: {e}")
            return False

    async def refine_content(self, content: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        Refine simulation content based on feedback.

        Args:
            content: Simulation content to refine
            feedback: Feedback for refinement

        Returns:
            Dict containing refined simulation
        """
        # For base implementation, just return the content
        # Subclasses can implement more sophisticated refinement
        logger.info(f"Refining simulation content based on feedback: {feedback}")
        return content
