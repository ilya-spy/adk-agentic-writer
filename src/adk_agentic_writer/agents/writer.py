"""Writer agent factory -- creates one LlmAgent per content format.

Uses output_key="draft_content" to store results in ADK session state.
"""

import json

from google.adk.agents import Agent

from ..formats import FormatSpec

MODEL = "gemini-2.5-flash"


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
