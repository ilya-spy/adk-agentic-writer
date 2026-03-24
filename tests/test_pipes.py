"""Pipeline construction tests -- no LLM calls, offline only."""

from google.adk.agents.loop_agent import LoopAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.sequential_agent import SequentialAgent

from adk_agentic_writer.agents import (
    create_ideator_pipeline,
    create_reviewer_pipeline,
    create_refiner_pipeline,
    create_verifier_pipeline,
    create_lead_writer_pipeline,
)
from adk_agentic_writer.workflows import (
    create_refinement_pipeline,
    create_publish_pipeline,
    exit_loop,
)


def test_refinement_pipeline_structure():
    reviewer = create_reviewer_pipeline()
    verifier = create_verifier_pipeline()
    refiner = create_refiner_pipeline(exit_loop)

    loop = create_refinement_pipeline(reviewer, verifier, refiner, max_iterations=3)

    assert isinstance(loop, LoopAgent)
    assert loop.max_iterations == 3
    assert len(loop.sub_agents) == 2

    parallel = loop.sub_agents[0]
    assert isinstance(parallel, ParallelAgent)
    assert parallel.sub_agents[0].name == "ReviewerAgent"
    assert parallel.sub_agents[1].name == "VerifierAgent"

    assert loop.sub_agents[1].name == "RefinerAgent"


def test_publish_pipeline_structure():
    ideator = create_ideator_pipeline()
    writer = create_lead_writer_pipeline()
    reviewer = create_reviewer_pipeline()
    refiner = create_refiner_pipeline(exit_loop)
    verifier = create_verifier_pipeline()

    pipeline = create_publish_pipeline(ideator, writer, reviewer, refiner, verifier)

    assert isinstance(pipeline, SequentialAgent)
    assert len(pipeline.sub_agents) == 3
    assert pipeline.sub_agents[0].name == "IdeatorAgent"
    assert pipeline.sub_agents[1].name == "LeadWriter"

    inner_loop = pipeline.sub_agents[2]
    assert isinstance(inner_loop, LoopAgent)
    assert len(inner_loop.sub_agents) == 2

    parallel = inner_loop.sub_agents[0]
    assert isinstance(parallel, ParallelAgent)
    assert parallel.sub_agents[0].name == "ReviewerAgent"
    assert parallel.sub_agents[1].name == "VerifierAgent"

    assert inner_loop.sub_agents[1].name == "RefinerAgent"
