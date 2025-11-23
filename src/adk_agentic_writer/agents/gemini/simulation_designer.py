"""Gemini-powered simulation designer agent using Google ADK."""

import json
import logging
from typing import Any, Dict

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

from ...models.agent_models import AGENT_TEAM_CONFIGS, AgentRole, AgentStatus
from ...models.content_models import SimulationControl, SimulationVariable, WebSimulation
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)


class GeminiSimulationDesignerAgent(BaseAgent):
    """Agent specialized in creating web simulations using Google ADK."""

    def __init__(
        self,
        agent_id: str = "gemini_simulation_designer_1",
        config: Dict[str, Any] | None = None,
    ):
        """Initialize the Gemini simulation designer agent with Google ADK."""
        super().__init__(agent_id, AgentRole.SIMULATION_DESIGNER, config)
        
        # Get system instruction from AGENT_TEAM_CONFIGS
        agent_config = AGENT_TEAM_CONFIGS.get(AgentRole.SIMULATION_DESIGNER)
        
        # Create Google ADK Agent instance
        self.adk_agent = Agent(
            name="SimulationDesignerAgent",
            model=Gemini(model="gemini-2.0-flash-exp"),
            instruction=agent_config.system_instruction if agent_config else self._get_default_instruction(),
            output_key="simulation_content",
        )
        self.runner = InMemoryRunner(agent=self.adk_agent)
    
    def _get_default_instruction(self) -> str:
        """Default instruction if not in config."""
        return """You are an expert in creating interactive web simulations and visualizations.
Design educational and engaging simulations with clear variables and controls."""

    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a web simulation using Google ADK Agent.

        Args:
            task_description: Description of the simulation to create
            parameters: Parameters including topic, simulation_type, complexity

        Returns:
            Dict containing the generated web simulation
        """
        await self.update_status(AgentStatus.WORKING)

        topic = parameters.get("topic", "physics")
        simulation_type = parameters.get("simulation_type", "interactive")
        complexity = parameters.get("complexity", "medium")

        logger.info(f"Generating {simulation_type} simulation about {topic} using Google ADK")

        # Generate simulation using Google ADK Agent
        simulation_data = await self._generate_simulation_with_adk(topic, simulation_type, complexity)

        await self.update_status(AgentStatus.COMPLETED)

        return simulation_data

    async def _generate_simulation_with_adk(
        self, topic: str, simulation_type: str, complexity: str
    ) -> Dict[str, Any]:
        """Generate web simulation using Google ADK Agent."""
        
        prompt = f"""Create an interactive web simulation with the following specifications:

Topic: {topic}
Type: {simulation_type}
Complexity: {complexity}

Design a simulation with:
- Clear, measurable variables
- Intuitive user controls
- Accurate simulation rules
- Appropriate visualization
- Educational value

Return the simulation in the following JSON format:
{{
    "title": "Simulation title",
    "description": "What the simulation demonstrates",
    "variables": [
        {{
            "name": "variable_name",
            "initial_value": 10,
            "min_value": 0,
            "max_value": 100,
            "unit": "units",
            "description": "What this variable represents"
        }}
    ],
    "controls": [
        {{
            "control_id": "control1",
            "control_type": "slider",
            "label": "Control Label",
            "target_variable": "variable_name",
            "min_value": 0,
            "max_value": 100,
            "step": 1
        }}
    ],
    "visualization_type": "chart",
    "update_rules": "How variables interact and update",
    "educational_notes": "Key learning points"
}}

Make the simulation accurate, intuitive, and educational."""

        try:
            # Run Google ADK Agent
            result = await self.runner.run(input_data={})
            
            # Parse result
            sim_data = json.loads(result.get("simulation_content", "{}")) if isinstance(result.get("simulation_content"), str) else result.get("simulation_content", {})
            
            # Validate and create WebSimulation object
            variables = [SimulationVariable(**v) for v in sim_data.get("variables", [])]
            controls = [SimulationControl(**c) for c in sim_data.get("controls", [])]
            
            simulation = WebSimulation(
                title=sim_data.get("title", f"{topic.title()} Simulation"),
                description=sim_data.get("description", f"Interactive simulation about {topic}"),
                variables=variables,
                controls=controls,
                visualization_type=sim_data.get("visualization_type", "chart"),
                update_rules=sim_data.get("update_rules", "Variables update based on user input"),
                educational_notes=sim_data.get("educational_notes", f"Learn about {topic} through interaction"),
            )
            
            return simulation.model_dump()

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error generating simulation with Google ADK: {e}")
            return await self._generate_fallback_simulation(topic, simulation_type)

    async def _generate_fallback_simulation(self, topic: str, simulation_type: str) -> Dict[str, Any]:
        """Fallback simulation generation."""
        logger.warning("Using fallback simulation generation")
        
        variables = [
            SimulationVariable(
                name="value",
                initial_value=50,
                min_value=0,
                max_value=100,
                unit="units",
                description=f"Primary variable for {topic}",
            )
        ]
        
        controls = [
            SimulationControl(
                control_id="slider1",
                control_type="slider",
                label="Adjust Value",
                target_variable="value",
                min_value=0,
                max_value=100,
                step=1,
            )
        ]
        
        simulation = WebSimulation(
            title=f"{topic.title()} Simulation",
            description=f"Interactive {simulation_type} simulation about {topic}",
            variables=variables,
            controls=controls,
            visualization_type="chart",
            update_rules="Value updates based on slider input",
            educational_notes=f"Explore {topic} concepts through this interactive simulation",
        )
        
        return simulation.model_dump()

