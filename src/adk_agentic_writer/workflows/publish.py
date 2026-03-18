"""Publish workflow -- full ideation-to-publish pipeline.

SequentialAgent: Ideator -> Writer -> LoopAgent(Reviewer -> Refiner)
"""

from google.adk.agents.loop_agent import LoopAgent
from google.adk.agents.sequential_agent import SequentialAgent

from ..formats import FormatSpec
from ..agents.ideator import create_ideator
from ..agents.writer import create_writer
from ..agents.reviewer import create_reviewer
from ..agents.refiner import create_loop_refiner
from .tools import exit_loop

MODEL = "gemini-2.5-flash"


def create_publish_pipeline(
    fmt: FormatSpec,
    model: str = MODEL,
    max_iterations: int = 3,
) -> SequentialAgent:
    """Create the full Ideate -> Write -> Review/Refine loop pipeline."""
    ideator = create_ideator(model)
    writer = create_writer(fmt, model)
    reviewer = create_reviewer(model)
    refiner = create_loop_refiner(exit_loop, model)

    loop = LoopAgent(
        name="RefinementLoop",
        sub_agents=[reviewer, refiner],
        max_iterations=max_iterations,
    )

    return SequentialAgent(
        name=f"PublishPipeline_{fmt.name}",
        sub_agents=[ideator, writer, loop],
        description=f"Full publish flow: ideate, write {fmt.label}, review, refine.",
    )
