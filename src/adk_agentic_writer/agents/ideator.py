"""Ideator agent -- brainstorms topic, selects format, sets params."""

from typing import Any, Dict

from google.adk.agents import Agent

from ..formats import list_formats
from ..tasks import IDEATE
from .base import BaseAgentService, MODEL


def _build_format_list() -> str:
    lines = []
    for fmt in list_formats():
        flavors = ", ".join(fmt.flavors) if fmt.flavors else fmt.name
        params = ", ".join(f"{p.name}={p.default}" for p in fmt.parameter_specs)
        lines.append(
            f"- {fmt.name} ({fmt.label}) flavors=[{flavors}] params=[{params}]"
        )
    return "\n".join(lines)


_INSTRUCTION = """\
You are a professional content brainstormer and ideation specialist.

Your job is to analyze a user's creative prompt and their hints about the content format(s),
then produce a clear, actionable brief for the content writer.

AVAILABLE FORMATS:
{format_list}

TASK:
1. Read the user prompt and any requested content types.
2. If multiple formats are requested, pick the BEST primary format.
3. Craft a refined topic statement that is specific and engaging.
4. Suggest optimal parameter values for the chosen format.
5. Provide a short creative direction note.

EXAMPLE OUTPUT (valid JSON only, no markdown):
{{
  "chosen_format": "quiz",
  "topic_statement": "A refined, specific topic description",
  "params": {{
    "num_questions": 5 (think about how many is appropriate for the topic),
    "difficulty": "medium" (think about what difficulty is appropriate for the topic)}},
  "creative_direction": "Brief note on tone, angle, or approach",
  "reasoning": "Why this format and approach was chosen"
}}
"""


class IdeatorAgentService(BaseAgentService):
    """Brainstorms topic, selects format, sets optimal parameters."""

    def __init__(self, model: str = MODEL):
        super().__init__(model=model)
        self._register_tasks([IDEATE])
        instruction = _INSTRUCTION.replace("{format_list}", _build_format_list())
        self._agent = Agent(
            name="IdeatorAgent",
            model=model,
            instruction=instruction,
            description="Brainstorms topic, selects format, and sets optimal parameters.",
            output_key="ideation_result",
            include_contents="none",
        )

    def prepare_task(
        self, task_id: str, params: Dict[str, Any],
    ) -> str:
        prompt = params.get("prompt", "")
        formats = params.get("formats", [])
        if formats:
            prompt += f"\nRequested formats: {', '.join(formats)}"
        return prompt

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        runner = self._ensure_runner("ideator", self._agent)
        return await self._run(runner, "IdeatorAgent", prompt)


def create_ideator(model: str = MODEL) -> Agent:
    """Standalone factory kept for workflow composition."""
    instruction = _INSTRUCTION.replace("{format_list}", _build_format_list())
    return Agent(
        name="IdeatorAgent",
        model=model,
        instruction=instruction,
        description="Brainstorms topic, selects format, and sets optimal parameters.",
        output_key="ideation_result",
        include_contents="none",
    )
