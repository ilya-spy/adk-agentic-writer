"""Tests for quiz writer agent."""

import pytest

from adk_agentic_writer.agents import StaticQuizWriterAgent
from adk_agentic_writer.models.agent_models import AgentStatus


@pytest.mark.asyncio
async def test_quiz_writer_initialization() -> None:
    """Test quiz writer agent initialization."""
    agent = StaticQuizWriterAgent()
    
    assert agent.agent_id == "static_quiz_writer"
    assert agent.state.status == AgentStatus.IDLE


@pytest.mark.asyncio
async def test_quiz_writer_generate_quiz() -> None:
    """Test generating a quiz."""
    agent = StaticQuizWriterAgent()
    
    result = await agent.process_task(
        "Create a quiz about Python programming",
        {"topic": "Python", "num_questions": 3},
    )
    
    assert "title" in result
    assert "questions" in result
    assert len(result["questions"]) == 3
    assert agent.state.status == AgentStatus.COMPLETED
