"""Tests for quiz writer agent."""

import pytest

from adk_agentic_writer.agents.quiz_writer import QuizWriterAgent
from adk_agentic_writer.models.agent_models import AgentStatus


@pytest.mark.asyncio
async def test_quiz_writer_initialization() -> None:
    """Test quiz writer agent initialization."""
    agent = QuizWriterAgent()
    
    assert agent.agent_id == "quiz_writer_1"
    assert agent.state.status == AgentStatus.IDLE


@pytest.mark.asyncio
async def test_quiz_writer_generate_quiz() -> None:
    """Test generating a quiz."""
    agent = QuizWriterAgent()
    
    result = await agent.process_task(
        "Create a quiz about Python programming",
        {"topic": "Python", "num_questions": 3},
    )
    
    assert "title" in result
    assert "questions" in result
    assert len(result["questions"]) == 3
    assert agent.state.status == AgentStatus.COMPLETED
