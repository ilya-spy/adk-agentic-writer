"""Writer agent -- format-specific writers + lead writer with AgentTool routing."""

import json
from typing import Any, Dict

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

from ..formats import FormatSpec, get_format, list_formats
from ..tasks import WRITE
from ..utils.callbacks import adk_before_agent, adk_after_agent, adk_before_model, adk_after_model
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
        after_model_callback=adk_after_model,
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


# ---------------------------------------------------------------------------
# Lead Writer -- single agent routing to format-specific AgentTools
# ---------------------------------------------------------------------------

def _build_tool_list_docs() -> str:
    """Build a description of available writer tools for the lead instruction."""
    lines = []
    for fmt in list_formats():
        lines.append(f"- {fmt.name.capitalize()}Writer: use for '{fmt.name}' format ({fmt.label})")
    return "\n".join(lines)


_LEAD_INSTRUCTION = """\
You are the Lead Writer agent. Your job is to analyze the ideation result,
determine the correct content format, and delegate writing to the appropriate
format-specific writer tool.

IDEATION RESULT (from previous pipeline step):
{ideation_result}

AVAILABLE WRITER TOOLS:
{tool_list}

STEPS:
1. Parse the ideation result to extract chosen_format, topic_statement,
   params (including domain, flavor, and format-specific parameters),
   creative_direction, and reasoning.
2. Select the writer tool whose name matches the chosen_format.
3. Call that tool with a detailed writing brief that includes ALL of:
   - The topic statement
   - All format-specific parameters (num_questions, num_nodes, difficulty, etc.)
   - The creative direction and reasoning
   - The domain (realworld or fictional)
   - The flavor
4. Return the tool's JSON output EXACTLY as-is. Do NOT modify, summarize,
   or wrap the output. The raw JSON from the writer tool is your final answer.

CRITICAL: You MUST call exactly one writer tool. Do not generate content yourself.
Output the writer tool's response verbatim as valid JSON."""


def create_lead_writer_pipeline(model: str = "gemini-2.5-flash") -> Agent:
    """Create lead writer that routes to format-specific writer AgentTools.

    Used in the publish pipeline. Reads {ideation_result} from session state
    and delegates to the matching format writer.
    """
    format_tools = []
    for fmt in list_formats():
        writer_instruction = _build_instruction(fmt)
        writer = Agent(
            name=f"{fmt.name.capitalize()}Writer",
            model=model,
            instruction=writer_instruction,
            description=f"Generates {fmt.label} content as structured JSON. Call this for '{fmt.name}' format.",
            tools=[google_search],
            include_contents="none",
            before_agent_callback=adk_before_agent,
            after_agent_callback=adk_after_agent,
            before_model_callback=adk_before_model,
            after_model_callback=adk_after_model,
        )
        format_tools.append(AgentTool(agent=writer, skip_summarization=True))

    instruction = _LEAD_INSTRUCTION.replace("{tool_list}", _build_tool_list_docs())
    return Agent(
        name="LeadWriter",
        model=model,
        instruction=instruction,
        description="Routes to the correct format-specific writer based on ideation result.",
        output_key="draft_content",
        tools=format_tools,
        include_contents="none",
        before_agent_callback=adk_before_agent,
        after_agent_callback=adk_after_agent,
        before_model_callback=adk_before_model,
        after_model_callback=adk_after_model,
    )


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
