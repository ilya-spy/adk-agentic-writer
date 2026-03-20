"""Publish workflow -- full ideation-to-publish pipeline.

Pure composer: accepts pre-built ADK agents,
returns SequentialAgent: Ideator -> Writer -> LoopAgent(Reviewer -> Refiner)
"""

from google.adk.agents import Agent
from google.adk.agents.sequential_agent import SequentialAgent

from .refine import create_refinement_pipeline


def create_publish_pipeline(
    ideator: Agent,
    writer: Agent,
    reviewer: Agent,
    refiner: Agent,
    max_iterations: int = 3,
) -> SequentialAgent:
    """Compose a full publish pipeline from pre-built ADK agents."""
    loop = create_refinement_pipeline(reviewer, refiner, max_iterations)
    return SequentialAgent(
        name="PublishPipeline",
        sub_agents=[ideator, writer, loop],
        description="Full publish flow: ideate, write, review/refine loop.",
    )
