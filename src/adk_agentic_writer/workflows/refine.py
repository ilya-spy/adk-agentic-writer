"""Refinement loop workflow.

Pure composer: accepts pre-built ADK reviewer and refiner agents,
returns a LoopAgent that iteratively reviews and refines content.
The refiner calls exit_loop when quality is sufficient.
"""

from google.adk.agents import Agent
from google.adk.agents.loop_agent import LoopAgent


def create_refinement_pipeline(
    reviewer: Agent,
    refiner: Agent,
    max_iterations: int = 3,
) -> LoopAgent:
    """Compose a Reviewer <-> Refiner loop from pre-built ADK agents."""
    return LoopAgent(
        name="RefinementLoop",
        sub_agents=[reviewer, refiner],
        max_iterations=max_iterations,
    )
