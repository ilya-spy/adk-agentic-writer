"""Publish workflow -- full ideation-to-publish pipeline.

Pure composer: accepts pre-built ADK agents, returns SequentialAgent:
  Ideator -> Writer -> Parallel(Reviewer, Verifier) -> Loop(Refiner, Reviewer)
"""

from google.adk.agents import Agent
from google.adk.agents.sequential_agent import SequentialAgent

from .refine import create_refinement_pipeline
from .verify import create_review_verify_parallel


def create_publish_pipeline(
    ideator: Agent,
    writer: Agent,
    reviewer: Agent,
    refiner: Agent,
    verifier: Agent,
    max_iterations: int = 3,
    loop_reviewer: Agent | None = None,
) -> SequentialAgent:
    """Compose a full publish pipeline from pre-built ADK agents.

    ADK agents can only belong to one parent, so the parallel step and
    the refinement loop need separate reviewer instances. Pass
    ``loop_reviewer`` for the loop; if omitted a new one is created.
    """
    from ..agents.reviewer import create_reviewer_pipeline

    parallel_review = create_review_verify_parallel(reviewer, verifier)
    loop_rev = loop_reviewer or create_reviewer_pipeline()
    loop = create_refinement_pipeline(refiner, loop_rev, max_iterations)
    return SequentialAgent(
        name="PublishPipeline",
        sub_agents=[ideator, writer, parallel_review, loop],
        description=(
            "Full publish flow: ideate, write, "
            "parallel review+verify, refine/review loop."
        ),
    )
