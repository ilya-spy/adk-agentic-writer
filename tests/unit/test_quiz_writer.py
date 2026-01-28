"""Tests for quiz writer agent."""

import pytest

from adk_agentic_writer.agents import StaticQuizWriterAgent
from adk_agentic_writer.models.agent_models import AgentStatus


@pytest.mark.asyncio
async def test_quiz_writer_initialization() -> None:
    """Test quiz writer agent initialization."""
    agent = StaticQuizWriterAgent()

    # Default agent_id is now "quiz_writer"
    assert agent.agent_id == "quiz_writer"
    assert agent.state.status == AgentStatus.IDLE


@pytest.mark.asyncio
async def test_quiz_writer_generate_quiz() -> None:
    """Test generating a quiz using the generate method."""
    agent = StaticQuizWriterAgent()

    # Use the new generate() convenience method
    result = await agent.generate(
        topic="Python",
        num_questions=3,
        difficulty="medium",
    )

    assert "title" in result
    assert "questions" in result
    assert len(result["questions"]) == 3
