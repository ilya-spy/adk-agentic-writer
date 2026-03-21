"""Ideator agent -- brainstorms topic, selects format, sets params."""

from typing import Any, Dict

from google.adk.agents import Agent

from ..formats import list_formats
from ..tasks import IDEATE
from .base import BaseAgentService


_PARAM_RANGES = {
    "num_questions": "2-15",
    "num_options": "2-6",
    "num_nodes": "4-30",
    "difficulty": "easy / medium / hard",
    "complexity": "basic / medium / advanced",
    "genre": "fantasy / scifi / mystery / adventure / horror / romance",
    "theme": "fantasy / scifi / historical / modern / mythological",
    "simulation_type": "interactive / guided / sandbox / web app",
}


def _build_format_list() -> str:
    lines = []
    for fmt in list_formats():
        flavors = ", ".join(fmt.flavors) if fmt.flavors else fmt.name
        parts = []
        for p in fmt.parameter_specs:
            if p.name in ("topic", "flavor"):
                continue
            rng = _PARAM_RANGES.get(p.name, str(p.default))
            parts.append(f"{p.name} (range: {rng})")
        lines.append(
            f"- {fmt.name} ({fmt.label}) flavors=[{flavors}] params=[{', '.join(parts)}]"
        )
    return "\n".join(lines)


_INSTRUCTION = """\
You are a professional content brainstormer and ideation specialist.

Your job is to analyze a user's creative prompt and their hints about the content format(s),
then produce a clear, actionable brief for the content writer.

AVAILABLE FORMATS:
{format_list}

TASK:
1. Read the user prompt and understand the user's intent.
2. Check for REQUESTED FORMATS at the end of the prompt, and decide the best fit for user goal.
3. Craft a refined topic statement that is specific and engaging.
4. Choose a flavor from the format's available flavors that best matches the user's intent.
5. Set parameter values that best serve this SPECIFIC idea.
   USE THE FULL RANGE of each parameter — do NOT default to middle/average values.
   A challenging trivia quiz might have 10-15 questions; a quick warm-up quiz might have 3-4.
   A sprawling adventure story might need 12-20 nodes; a tight mystery might need 5-6.
   Match the parameters to the content concept, not to generic defaults.
6. Provide a short creative direction note.
7. Provide a brief reasoning for the key decisions made.

CRITICAL: Be creative and varied with parameter values. Every idea should feel distinct.
Avoid the trap of always picking middle-of-the-road values. Surprise the user.

OUTPUT FORMAT (valid JSON only, no markdown):
The example below shows ONLY the JSON structure. The values are PLACEHOLDERS, not
recommended defaults. Your actual values MUST be tailored to the specific idea.
{
  "chosen_format": "<format name>",
  "topic_statement": "<specific, engaging topic description>",
  "params": {
    "format": "<format name>",
    "flavor": "<chosen flavor>",
    ...format-specific params with values from the allowed ranges...
  },
  "creative_direction": "<tone, angle, or unique approach>",
  "reasoning": "<why this format, flavor, and parameter choices>"
}
"""


def create_ideator(
    instruction: str | None = None,
    *,
    model: str = "gemini-2.5-flash",
    output_key: str | None = "ideation_result",
) -> Agent:
    """Base factory -- accepts explicit instruction and output_key."""
    if instruction is None:
        instruction = _INSTRUCTION.replace("{format_list}", _build_format_list())
    return Agent(
        name="IdeatorAgent",
        model=model,
        instruction=instruction,
        description="Brainstorms topic, selects format, and sets optimal parameters.",
        output_key=output_key,
        include_contents="none",
    )


def create_ideator_pipeline(model: str = "gemini-2.5-flash") -> Agent:
    """Pipeline variant -- writes result to session state via output_key."""
    return create_ideator(model=model, output_key="ideation_result")


def create_ideator_service(model: str = "gemini-2.5-flash") -> Agent:
    """Service variant -- no output_key; result returned explicitly."""
    return create_ideator(model=model, output_key=None)


class IdeatorAgentService(BaseAgentService):
    """Brainstorms topic, selects format, sets optimal parameters."""

    def __init__(self):
        super().__init__()
        self._register_tasks([IDEATE])
        self._pipeline_agents.append(create_ideator_pipeline())
        self._service_agents.append(create_ideator_service())

    def prepare_task(
        self,
        task_id: str,
        params: Dict[str, Any],
    ) -> str:
        prompt = params.get("prompt", "")
        formats = params.get("formats", [])
        if formats:
            prompt += f"\nREQUESTED FORMATS: {', '.join(formats)}"
        return prompt

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        agent = self._service_agents[0]
        runner = self._ensure_runner("ideator", agent)
        return await self._run(runner, "IdeatorAgent", prompt)
