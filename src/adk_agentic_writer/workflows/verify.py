"""Parallel review + verification workflow.

Runs reviewer and verifier concurrently using ADK ParallelAgent.
Both write their results to session state (review_result, verification_result)
for consumption by the downstream refiner.
"""

from google.adk.agents import Agent
from google.adk.agents.parallel_agent import ParallelAgent


def create_review_verify_parallel(
    reviewer: Agent,
    verifier: Agent,
) -> ParallelAgent:
    """Run reviewer and verifier concurrently via ADK ParallelAgent."""
    return ParallelAgent(
        name="ReviewVerifyParallel",
        sub_agents=[reviewer, verifier],
        description=(
            "Runs quality review and fact-check verification in parallel. "
            "Reviewer writes review_result; verifier writes verification_result."
        ),
    )
