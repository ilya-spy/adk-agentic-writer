"""Web simulation format specification."""

from ..models.content_models import WebSimulation
from ..utils.schema import build_schema_instruction
from .base import FormatSpec, ParamSpec

SIMULATION_FORMAT = FormatSpec(
    name="simulation",
    label="Web Simulation",
    model_class=WebSimulation,
    default_params={"complexity": "medium", "simulation_type": "interactive"},
    parameter_specs=[
        ParamSpec("complexity", "str", "medium", "Simulation complexity: basic, medium, advanced"),
        ParamSpec("simulation_type", "str", "interactive", "Type of simulation"),
    ],
    schema_description=build_schema_instruction(WebSimulation),
    writer_instruction="""\
You are an expert content creator specializing in interactive and engaging content.
You are a simulation design specialist creating educational and engaging
interactive web simulations with accurate models, intuitive controls,
and realistic variable interactions.

CRITICAL: Respond with valid JSON only. No markdown, no explanations, no code blocks.
The JSON must exactly match the schema structure provided.""",
    writer_prompt="""\
Create an interactive simulation about "{topic}".

Requirements:
- Define key variables with realistic ranges
- Create intuitive controls (sliders, buttons, toggles)
- Define rules/equations for variable interactions
- Specify visualization type (chart, animation, 3d)""",
    reviewer_prompt="""\
Review this simulation. Check:
- Variables have realistic ranges and units
- Controls properly reference existing variables
- Rules/equations are logically consistent
- Visualization type is appropriate""",
    refiner_prompt="""\
Refine this simulation. Fix any issues from the review. Ensure:
- Variable interactions are realistic
- Controls are intuitive and well-labeled
- Rules are scientifically plausible
- Overall design is educational and engaging""",
    aliases=["web_simulation", "interactive", "simulator"],
    temperature=0.65,
    max_tokens=2048,
)
