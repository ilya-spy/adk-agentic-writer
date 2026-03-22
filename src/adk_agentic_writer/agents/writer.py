"""Writer agent -- creates one LlmAgent per content format/flavor."""

import json
from typing import Any, Dict

from google.adk.agents import Agent
from google.adk.tools import google_search

from ..formats import FormatSpec, get_format, list_formats
from ..tasks import WRITE
from ..utils.callbacks import adk_before_agent, adk_after_agent, adk_before_model
from .base import BaseAgentService


_PIPELINE_SUFFIX = """

Ideation context (creative direction and reasoning for this content):
{ideation_result}

Use the creative direction and reasoning above to guide your content creation."""

_SERVICE_SUFFIX = """

The topic, creative direction, and reasoning will be provided in the user message."""


_DOMAIN_BLOCK = """

DOMAIN AWARENESS:
If domain is "realworld": Use Google Search to verify key facts before including
them. Cite specific dates, names, numbers from search results. Accuracy is critical.
If domain is "fictional": Do NOT use Google Search. Create freely from imagination.
Invent names, places, and events without external verification."""


def _build_instruction(fmt: FormatSpec) -> str:
    """Build the common base instruction (shared by pipeline and service)."""
    instruction = fmt.writer_instruction
    if fmt.schema_description:
        instruction += f"\n\n{fmt.schema_description}"
    if fmt.sample_output:
        instruction += f"\n\nExample output:\n{json.dumps(fmt.sample_output, indent=2)}"
    instruction += _DOMAIN_BLOCK
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
        tools=[google_search],
        include_contents="none",
        before_agent_callback=adk_before_agent,
        after_agent_callback=adk_after_agent,
        before_model_callback=adk_before_model,
    )


def create_writer_pipeline(
    fmt: FormatSpec, model: str = "gemini-2.5-flash",
) -> Agent:
    """Pipeline variant -- reads ideation_result from session state."""
    instruction = _build_instruction(fmt) + _PIPELINE_SUFFIX
    return create_writer(fmt, instruction, model=model, output_key="draft_content")


def create_writer_service(
    fmt: FormatSpec, model: str = "gemini-2.5-flash",
) -> Agent:
    """Service variant -- context provided in user message."""
    instruction = _build_instruction(fmt) + _SERVICE_SUFFIX
    return create_writer(fmt, instruction, model=model, output_key=None)


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
            prompt = fmt.writer_prompt.format(**merged)
        except KeyError:
            prompt = f"Generate {fmt_name} content about {topic}."

        creative_direction = params.get("creative_direction", "")
        reasoning = params.get("reasoning", "")
        if creative_direction or reasoning:
            prompt += "\n\nIdeation context:"
            if creative_direction:
                prompt += f"\nCreative direction: {creative_direction}"
            if reasoning:
                prompt += f"\nReasoning: {reasoning}"

        domain = params.get("domain", "realworld")
        prompt += f"\n\nDOMAIN: {domain}"
        return prompt

    async def run_prompt(self, prompt: str) -> Dict[str, Any]:
        fmt = getattr(self, "_last_fmt", None)
        fmt_name = fmt.name if fmt else "quiz"
        writer = self._writers.get(fmt_name) or next(iter(self._writers.values()))
        runner = self._ensure_runner(f"writer_{fmt_name}", writer)
        model_class = fmt.model_class if fmt else None
        return await self._run(runner, writer.name, prompt, model_class=model_class)
