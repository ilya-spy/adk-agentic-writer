"""Writer agent -- creates one LlmAgent per content format/flavor."""

import json
from typing import Any, Dict

from google.adk.agents import Agent

from ..formats import FormatSpec, get_format, list_formats
from ..tasks import WRITE
from .base import BaseAgentService, MODEL


def create_writer(fmt: FormatSpec, model: str = MODEL) -> Agent:
    """Create a writer LlmAgent for a specific content format."""
    instruction = fmt.writer_instruction
    if fmt.schema_description:
        instruction += f"\n\n{fmt.schema_description}"
    if fmt.sample_output:
        instruction += f"\n\nExample output:\n{json.dumps(fmt.sample_output, indent=2)}"

    return Agent(
        name=f"{fmt.name.capitalize()}Writer",
        model=model,
        instruction=instruction,
        description=f"Generates {fmt.label} content as structured JSON.",
        output_key="draft_content",
        include_contents="none",
    )


class WriterAgent(BaseAgentService):
    """Creates writer agents per format on demand, routes by flavor/format."""

    def __init__(self, model: str = MODEL):
        super().__init__(model=model)
        self._register_tasks([WRITE])
        self._writers: Dict[str, Agent] = {}
        for fmt in list_formats():
            self._writers[fmt.name] = create_writer(fmt, model)

    async def process_task(
        self, task_id: str, params: Dict[str, Any],
    ) -> Dict[str, Any]:
        flavor = params.get("flavor", params.get("format", "quiz"))
        topic = params.get("topic", "general")

        fmt = get_format(flavor) or get_format("quiz")
        writer = self._writers.get(fmt.name)
        if not writer:
            writer = self._writers.get("quiz")

        merged = dict(fmt.default_params)
        merged.update(params)
        merged["topic"] = topic
        merged.setdefault("flavor", flavor)

        try:
            prompt_text = fmt.writer_prompt.format(**merged)
        except KeyError:
            prompt_text = f"Generate {flavor} content about {topic}."

        runner = self._ensure_runner(f"writer_{fmt.name}", writer)
        return await self._run(runner, writer.name, prompt_text)
