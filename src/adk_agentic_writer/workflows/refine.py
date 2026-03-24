"""Refinement loop workflow.

Pure composer: accepts pre-built ADK agents, returns a LoopAgent:
  Loop(Parallel(Reviewer, Verifier), Refiner)

Each iteration:
  1. Parallel reviewer + verifier evaluate the current draft
  2. Refiner applies fixes based on both review_result and verification_result
  3. Refiner calls exit_loop when quality is sufficient
"""

from google.adk.agents import Agent
from google.adk.agents.loop_agent import LoopAgent

from .verify import create_review_verify_parallel


def create_refinement_pipeline(
    reviewer: Agent,
    verifier: Agent,
    refiner: Agent,
    max_iterations: int = 2,
) -> LoopAgent:
    """Compose a Parallel(Reviewer, Verifier) -> Refiner loop."""
    parallel = create_review_verify_parallel(reviewer, verifier)
    return LoopAgent(
        name="RefinementLoop",
        sub_agents=[parallel, refiner],
        max_iterations=max_iterations,
    )
