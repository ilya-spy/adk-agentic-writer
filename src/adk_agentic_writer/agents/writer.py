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


class WriterAgentService(BaseAgentService):
    """Creates writer agents per format on demand, routes by flavor/format."""

    def __init__(self, model: str = MODEL):
        super().__init__(model=model)
        self._register_tasks([WRITE])
        self._writers: Dict[str, Agent] = {}
        for fmt in list_formats():
            self._writers[fmt.name] = create_writer(fmt, model)

    def prepare_task(
        self, task_id: str, params: Dict[str, Any],
    ) -> str:
        flavor = params.get("flavor", params.get("format", "quiz"))
        topic = params.get("topic", "general")

        fmt = get_format(flavor) or get_format("quiz")
        self._last_fmt = fmt

        merged = dict(fmt.default_params)
        merged.update(params)
        merged["topic"] = topic
        merged.setdefault("flavor", flavor)

        try:
            return fmt.writer_prompt.format(**merged)
        except KeyError:
            return f"Generate {flavor} content about {topic}."

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        fmt = getattr(self, "_last_fmt", None)
        fmt_name = fmt.name if fmt else "quiz"
        writer = self._writers.get(fmt_name) or next(iter(self._writers.values()))
        runner = self._ensure_runner(f"writer_{fmt_name}", writer)
        return await self._run(runner, writer.name, prompt)
