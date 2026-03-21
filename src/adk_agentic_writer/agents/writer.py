"""Writer agent -- creates one LlmAgent per content format/flavor."""

import json
from typing import Any, Dict

from google.adk.agents import Agent

from ..formats import FormatSpec, get_format, list_formats
from ..tasks import WRITE
from .base import BaseAgentService


def _build_instruction(fmt: FormatSpec) -> str:
    instruction = fmt.writer_instruction
    if fmt.schema_description:
        instruction += f"\n\n{fmt.schema_description}"
    if fmt.sample_output:
        instruction += f"\n\nExample output:\n{json.dumps(fmt.sample_output, indent=2)}"
    return instruction


def create_writer(
    fmt: FormatSpec,
    instruction: str | None = None,
    *,
    model: str = "gemini-2.5-flash",
    output_key: str | None = "draft_content",
) -> Agent:
    """Base factory -- accepts explicit instruction and output_key."""
    if instruction is None:
        instruction = _build_instruction(fmt)
    return Agent(
        name=f"{fmt.name.capitalize()}Writer",
        model=model,
        instruction=instruction,
        description=f"Generates {fmt.label} content as structured JSON.",
        output_key=output_key,
        include_contents="none",
    )


def create_writer_pipeline(
    fmt: FormatSpec, model: str = "gemini-2.5-flash",
) -> Agent:
    """Pipeline variant -- writes result to session state via output_key."""
    return create_writer(fmt, model=model, output_key="draft_content")


def create_writer_service(
    fmt: FormatSpec, model: str = "gemini-2.5-flash",
) -> Agent:
    """Service variant -- no output_key; result returned explicitly."""
    return create_writer(fmt, model=model, output_key=None)


class WriterAgentService(BaseAgentService):
    """Routes write requests to the correct per-format ADK writer agent."""

    def __init__(self):
        super().__init__()
        self._register_tasks([WRITE])
        self._pipeline_writers: Dict[str, Agent] = {}
        self._writers: Dict[str, Agent] = {}
        for fmt in list_formats():
            pipe = create_writer_pipeline(fmt)
            svc = create_writer_service(fmt)
            self._pipeline_writers[fmt.name] = pipe
            self._writers[fmt.name] = svc
            self._pipeline_agents.append(pipe)
            self._service_agents.append(svc)

    def prepare_task(
        self,
        task_id: str,
        params: Dict[str, Any],
    ) -> str:
        fmt_name = params.get("format", "quiz")
        topic = params.get("topic", "general")

        fmt = get_format(fmt_name) or get_format("quiz")
        self._last_fmt = fmt

        merged = dict(fmt.default_params)
        merged.update(params)
        merged["topic"] = topic
        merged.setdefault("flavor", fmt_name)

        try:
            return fmt.writer_prompt.format(**merged)
        except KeyError:
            return f"Generate {fmt_name} content about {topic}."

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        fmt = getattr(self, "_last_fmt", None)
        fmt_name = fmt.name if fmt else "quiz"
        writer = self._writers.get(fmt_name) or next(iter(self._writers.values()))
        runner = self._ensure_runner(f"writer_{fmt_name}", writer)
        return await self._run(runner, writer.name, prompt)
