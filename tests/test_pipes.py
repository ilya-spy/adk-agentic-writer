"""Pipeline construction tests -- no LLM calls, offline only."""

from google.adk.agents.loop_agent import LoopAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.sequential_agent import SequentialAgent

from adk_agentic_writer.agents import (
    create_ideator_pipeline,
    create_reviewer_pipeline,
    create_refiner_pipeline,
    create_verifier_pipeline,
    create_writer_pipeline,
)
from adk_agentic_writer.formats import get_format
from adk_agentic_writer.workflows import (
    create_refinement_pipeline,
    create_publish_pipeline,
    exit_loop,
)


def test_refinement_pipeline_structure():
    refiner = create_refiner_pipeline(exit_loop)
    reviewer = create_reviewer_pipeline()

    loop = create_refinement_pipeline(refiner, reviewer, max_iterations=3)

    assert isinstance(loop, LoopAgent)
    assert loop.max_iterations == 3
    assert len(loop.sub_agents) == 2
    assert loop.sub_agents[0].name == "RefinerAgent"
    assert loop.sub_agents[1].name == "ReviewerAgent"


def test_publish_pipeline_structure():
    ideator = create_ideator_pipeline()
    fmt = get_format("quiz")
    writer = create_writer_pipeline(fmt)
    reviewer = create_reviewer_pipeline()
    refiner = create_refiner_pipeline(exit_loop)
    verifier = create_verifier_pipeline()

    pipeline = create_publish_pipeline(ideator, writer, reviewer, refiner, verifier)

    assert isinstance(pipeline, SequentialAgent)
    assert len(pipeline.sub_agents) == 4
    assert pipeline.sub_agents[0].name == "IdeatorAgent"
    assert pipeline.sub_agents[1].name == "QuizWriter"

    parallel = pipeline.sub_agents[2]
    assert isinstance(parallel, ParallelAgent)
    assert len(parallel.sub_agents) == 2
    assert parallel.sub_agents[0].name == "ReviewerAgent"
    assert parallel.sub_agents[1].name == "VerifierAgent"

    inner_loop = pipeline.sub_agents[3]
    assert isinstance(inner_loop, LoopAgent)
    assert len(inner_loop.sub_agents) == 2
    assert inner_loop.sub_agents[0].name == "RefinerAgent"
    assert inner_loop.sub_agents[1].name == "ReviewerAgent"
