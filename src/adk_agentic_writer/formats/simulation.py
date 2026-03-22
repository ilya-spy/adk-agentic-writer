"""Web simulation format specification."""

from ..models.content_models import WebSimulation
from .base import FormatSpec, ParamSpec

SIM_SCHEMA = """\
Output JSON Schema:
{
  "title": "string - Simulation title",
  "description": "string - 1-2 sentence overview",
  "variables": [
    {
      "name": "input_var_name",
      "initial_value": 5.0,
      "min_value": 0,
      "max_value": 10,
      "unit": "kg"
    },
    {
      "name": "output_var_name",
      "initial_value": 0,
      "min_value": 0,
      "max_value": 100,
      "unit": "%"
    }
  ],
  "controls": [
    {
      "control_id": "c1",
      "label": "Human Readable Label",
      "type": "slider",
      "affects": ["input_var_name"],
      "parameters": {"min": 0, "max": 10}
    }
  ],
  "rules": [
    "output_var_name = input_var_a * 2 + input_var_b / 3"
  ],
  "visualization_type": "dashboard"
}

CRITICAL structural rules:

1. VARIABLES — split into INPUT and OUTPUT:
   - INPUT variables: user-controllable. Each MUST have exactly one matching control.
   - OUTPUT variables: computed from rules. MUST NOT have controls.
   - Use snake_case names. Keep units short (kg, %, m/s, people, units).
   - All variables MUST have min_value and max_value set.
   - Output initial_value should be 0 (will be computed by rules).

2. VARIABLE COUNTS:
   - "basic" complexity: 2-3 inputs + 1-2 outputs = 3-5 total
   - "medium" complexity: 3-4 inputs + 2-3 outputs = 5-7 total
   - "advanced" complexity: 4-5 inputs + 3-4 outputs = 7-9 total
   - NEVER exceed 9 variables total.

3. CONTROLS — slider only:
   - One control per input variable (1:1 mapping).
   - type MUST be "slider".
   - parameters MUST have "min" and "max" matching the variable's range.
   - label should be a clean human-readable name.
   - No controls for output variables.

4. RULES — clean arithmetic formulas, one per output:
   - Format: "output_name = expression"
   - Left side: an output variable name.
   - Right side: ONLY variable names, numbers, +, -, *, /, and parentheses.
   - DO NOT use Math.max, Math.min, Math.abs, Math.round, or ANY function calls.
   - DO NOT use ternary operators (? :), conditionals, or semicolons.
   - DO NOT include comments (// or /* */) inside rules.
   - If you need clamping, design variable ranges so values stay reasonable.
   - One rule per output variable. Rules evaluated top-to-bottom,
     so an earlier output can feed a later rule.
   - Keep each rule short — one line, one output. 2-5 rules total is ideal.

5. visualization_type MUST be "dashboard"."""

SIM_SAMPLE = {
    "title": "Simple Ecosystem Balance",
    "description": "Explore how predator and prey populations interact.",
    "variables": [
        {
            "name": "prey_birth_rate",
            "initial_value": 3.0,
            "min_value": 0.5,
            "max_value": 8.0,
            "unit": "%",
        },
        {
            "name": "predator_count",
            "initial_value": 20,
            "min_value": 1,
            "max_value": 100,
            "unit": "animals",
        },
        {
            "name": "food_supply",
            "initial_value": 500,
            "min_value": 100,
            "max_value": 2000,
            "unit": "units",
        },
        {
            "name": "prey_population",
            "initial_value": 0,
            "min_value": 0,
            "max_value": 5000,
            "unit": "animals",
        },
        {
            "name": "ecosystem_health",
            "initial_value": 0,
            "min_value": 0,
            "max_value": 100,
            "unit": "%",
        },
    ],
    "controls": [
        {
            "control_id": "c1",
            "label": "Prey Birth Rate",
            "type": "slider",
            "affects": ["prey_birth_rate"],
            "parameters": {"min": 0.5, "max": 8.0},
        },
        {
            "control_id": "c2",
            "label": "Predator Count",
            "type": "slider",
            "affects": ["predator_count"],
            "parameters": {"min": 1, "max": 100},
        },
        {
            "control_id": "c3",
            "label": "Food Supply",
            "type": "slider",
            "affects": ["food_supply"],
            "parameters": {"min": 100, "max": 2000},
        },
    ],
    "rules": [
        "prey_population = food_supply * prey_birth_rate / (predator_count + 1)",
        "ecosystem_health = 100 * food_supply / (food_supply + predator_count * 10)",
    ],
    "visualization_type": "dashboard",
}

SIMULATION_FORMAT = FormatSpec(
    name="simulation",
    label="Web Simulation",
    model_class=WebSimulation,
    default_params={"complexity": "medium", "simulation_type": "interactive"},
    parameter_specs=[
        ParamSpec("topic", "str", "", "Content topic"),
        ParamSpec("flavor", "str", "simulation", "Content flavor"),
        ParamSpec(
            "complexity",
            "str",
            "medium",
            "Simulation complexity: basic, medium, advanced",
        ),
        ParamSpec("simulation_type", "str", "interactive", "Type of simulation"),
    ],
    schema_description=SIM_SCHEMA,
    sample_output=SIM_SAMPLE,
    writer_instruction="""\
You are an expert content creator specializing in interactive and engaging content.
You design concise, educational web simulations where a small set of input
variables drive computed outputs via clear arithmetic formulas.
Let the topic dictate the simulation's tone and framing.
If creative direction and reasoning are provided, use them to guide your approach.

CRITICAL: Respond with valid JSON only. No markdown, no explanations, no code blocks.
Do NOT include any commentary, analysis, or discussion of search results.
Your entire response must be a single JSON object matching the schema structure provided.""",
    writer_prompt="""\
Create an interactive {flavor} about "{topic}".

STYLE — adapt to the "{flavor}" format:
- "simulation": Standard educational simulation with clear learning goals.
- "web_simulation": Browser-focused; emphasize interactivity.
- "interactive": Hands-on exploration; let the user experiment freely.
- "simulator": Realistic model; accuracy over simplicity.

COMPLEXITY — the complexity is "{complexity}":
- "basic": 2-3 input variables, 1-2 computed outputs.
- "medium": 3-4 input variables, 2-3 computed outputs.
- "advanced": 4-5 input variables, 3-4 computed outputs.

RULES:
- Keep total variables under 9. Fewer is better.
- Every input variable MUST have exactly one slider control.
- Output variables MUST NOT have controls — they are computed by rules.
- Each rule MUST be a short arithmetic formula: "output = expression".
  Only use: variable names, numbers, +, -, *, /, parentheses.
  DO NOT use Math.max, Math.min, ternary (?:), comments, or any function calls.
- Rules are evaluated top-to-bottom so earlier outputs can feed later rules.
- Aim for 2-5 clear formulas. Each should reveal an interesting relationship.
- Use realistic ranges and short units.
- visualization_type must be "dashboard".

TONE AWARENESS:
Analyze the topic before writing. Derive your tone, vocabulary, and atmosphere
from what the subject matter demands. Serious or sensitive topics require
a respectful, measured approach. Lighthearted topics allow a more casual,
playful voice. Never impose a default "fun" or "upbeat" tone -- let the topic lead.""",
    reviewer_prompt="""\
Review this simulation for runtime correctness. Check EVERY rule:

RULE VALIDATION (most important):
- Each rule MUST be "output_name = expression" with ONLY: variable names,
  numbers, +, -, *, /, parentheses. Nothing else.
- REJECT any rule containing: Math.max, Math.min, Math.abs, Math.round,
  or any function call (anything with parentheses after a name like func()).
- REJECT any rule containing: ternary (? :), semicolons, comments (//).
- REJECT any rule longer than ~80 characters — it should be simplified.
- If ANY rule fails these checks, flag it as a critical error with the exact
  offending text and say what arithmetic equivalent would fix it.

STRUCTURAL CHECKS:
- Input variables each have exactly one slider control (1:1)
- Output variables have NO controls
- Total variable count is within limits (max 9)
- Rules only reference defined variable names
- Controls parameters.min/max match variable min_value/max_value
- visualization_type is "dashboard"

Be strict. Simpler formulas are better. Provide concrete fix suggestions.""",
    refiner_prompt="""\
Refine this simulation based on the review feedback. Priority actions:

1. REWRITE any rule that uses Math.*, ternary (?:), comments, or function calls.
   Convert to pure arithmetic using only: variable names, numbers, +, -, *, /, ().
   Example: instead of "Math.max(0, x - 5)" use "(x - 5)" and adjust variable
   min_value to prevent negative results.
2. SIMPLIFY long formulas. Split complex expressions into intermediate outputs
   if needed, but keep total output count under 4.
3. Remove excess variables — keep only the essentials.
4. Ensure 1:1 mapping between input variables and controls.
5. Ensure rule ordering: if output A feeds into rule for output B, A comes first.
6. Verify all variable names in rules match defined variables.
7. Set visualization_type to "dashboard".""",
    flavors=["web_simulation", "interactive", "simulator"],
    temperature=0.65,
    max_tokens=2048,
)
