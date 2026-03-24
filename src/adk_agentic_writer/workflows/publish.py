"""Publish workflow -- full ideation-to-publish pipeline.

Pure composer: accepts pre-built ADK agents, returns SequentialAgent:
  Ideator -> Writer -> Loop(Parallel(Reviewer, Verifier), Refiner)
"""

from google.adk.agents import Agent
from google.adk.agents.sequential_agent import SequentialAgent

from .refine import create_refinement_pipeline


def create_publish_pipeline(
    ideator: Agent,
    writer: Agent,
    reviewer: Agent,
    refiner: Agent,
    verifier: Agent,
    max_iterations: int = 3,
) -> SequentialAgent:
    """Compose a full publish pipeline from pre-built ADK agents.

    Pipeline: Ideator -> Writer -> Loop(Parallel(Reviewer, Verifier), Refiner)
    """
    loop = create_refinement_pipeline(reviewer, verifier, refiner, max_iterations)
    return SequentialAgent(
        name="PublishPipeline",
        sub_agents=[ideator, writer, loop],
        description=(
            "Full publish flow: ideate, write, then iteratively "
            "review+verify in parallel and refine until quality is sufficient."
        ),
    )
