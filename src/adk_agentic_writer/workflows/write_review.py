"""Write-then-review sequential workflow.

SequentialAgent: Writer -> Reviewer
State flow: user prompt -> draft_content -> review_result
"""

from google.adk.agents.sequential_agent import SequentialAgent

from ..formats import FormatSpec
from ..agents.writer import create_writer
from ..agents.reviewer import create_reviewer

MODEL = "gemini-2.5-flash"


def create_write_review_pipeline(
    fmt: FormatSpec,
    model: str = MODEL,
) -> SequentialAgent:
    """Create a Writer -> Reviewer sequential pipeline for a format."""
    writer = create_writer(fmt, model)
    reviewer = create_reviewer(model)

    return SequentialAgent(
        name=f"WriteReview_{fmt.name}",
        sub_agents=[writer, reviewer],
        description=f"Writes {fmt.label} content then reviews it for quality.",
    )
