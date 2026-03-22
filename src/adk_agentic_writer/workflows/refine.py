"""Refinement loop workflow.

Pure composer: accepts pre-built ADK refiner and reviewer agents,
returns a LoopAgent that iteratively refines then re-reviews content.
The refiner calls exit_loop when quality is sufficient.

Loop order: Refiner -> Reviewer
  - Refiner applies fixes from both review_result and verification_result
  - Reviewer re-evaluates the updated draft
"""

from google.adk.agents import Agent
from google.adk.agents.loop_agent import LoopAgent


def create_refinement_pipeline(
    refiner: Agent,
    reviewer: Agent,
    max_iterations: int = 3,
) -> LoopAgent:
    """Compose a Refiner -> Reviewer loop from pre-built ADK agents."""
    return LoopAgent(
        name="RefinementLoop",
        sub_agents=[refiner, reviewer],
        max_iterations=max_iterations,
    )
