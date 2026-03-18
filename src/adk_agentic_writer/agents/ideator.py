"""Ideator agent -- brainstorms topic, selects format, sets params.

Creates a native ADK LlmAgent that analyzes a user prompt and
requested content types to produce a structured ideation result.
"""

from google.adk.agents import Agent

from ..formats import list_formats

MODEL = "gemini-2.5-flash"

_INSTRUCTION = """\
You are a professional content brainstormer and ideation specialist.

Your job is to analyze a user's creative prompt and their selected content format(s),
then produce a clear, actionable brief for the content writer.

AVAILABLE FORMATS:
{format_list}

TASK:
1. Read the user prompt and any requested content types.
2. If multiple formats are requested, pick the BEST primary format.
3. Craft a refined topic statement that is specific and engaging.
4. Suggest optimal parameter values for the chosen format.
5. Provide a short creative direction note.

OUTPUT (valid JSON only, no markdown):
{{
  "chosen_format": "quiz",
  "topic_statement": "A refined, specific topic description",
  "params": {{"num_questions": 5, "difficulty": "medium"}},
  "creative_direction": "Brief note on tone, angle, or approach",
  "reasoning": "Why this format and approach was chosen"
}}
"""


def _build_format_list() -> str:
    lines = []
    for fmt in list_formats():
        params = ", ".join(f"{p.name}={p.default}" for p in fmt.parameter_specs)
        lines.append(f"- {fmt.name} ({fmt.label}): params=[{params}]")
    return "\n".join(lines)


def create_ideator(model: str = MODEL) -> Agent:
    instruction = _INSTRUCTION.replace("{format_list}", _build_format_list())
    return Agent(
        name="IdeatorAgent",
        model=model,
        instruction=instruction,
        description="Brainstorms topic, selects format, and sets optimal parameters.",
        output_key="ideation_result",
        include_contents="none",
    )
