"""Refinement loop workflow.

SequentialAgent: Writer -> LoopAgent(Reviewer -> Refiner)
The refiner calls exit_loop when quality is sufficient.
"""

from google.adk.agents import Agent
from google.adk.agents.loop_agent import LoopAgent
from google.adk.agents.sequential_agent import SequentialAgent

from ..formats import FormatSpec
from ..agents.writer import create_writer
from ..agents.reviewer import create_reviewer
from ..agents.refiner import create_loop_refiner
from .tools import exit_loop

MODEL = "gemini-2.5-flash"


def create_refinement_pipeline(
    fmt: FormatSpec,
    model: str = MODEL,
    max_iterations: int = 3,
) -> SequentialAgent:
    """Create a Writer -> (Reviewer <-> Refiner loop) pipeline."""
    writer = create_writer(fmt, model)
    reviewer = create_reviewer(model)
    refiner = create_loop_refiner(exit_loop, model)

    loop = LoopAgent(
        name="RefinementLoop",
        sub_agents=[reviewer, refiner],
        max_iterations=max_iterations,
    )

    return SequentialAgent(
        name=f"WriteAndRefine_{fmt.name}",
        sub_agents=[writer, loop],
        description=f"Writes {fmt.label} content then iteratively refines it.",
    )
