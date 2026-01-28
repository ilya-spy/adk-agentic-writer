"""
Integration tests for ADK agents and coordinators.

This module tests:
- Static team coordinator
- Gemini team coordinator (stubs)
- Content generation workflows

Usage:
    pytest tests/integration/test_adk.py -v
"""

import pytest

from adk_agentic_writer.agents.static import (
    CoordinatorAgent,
    StaticQuizWriterAgent,
    StoryWriterAgent,
)


# Static Team Tests


@pytest.mark.asyncio
async def test_static_coordinator_initialization():
    """Test static coordinator initialization."""
    coordinator = CoordinatorAgent()

    assert coordinator.agent_id == "static_coordinator"
    assert coordinator.quiz_agent is not None
    assert coordinator.story_agent is not None
    assert coordinator.game_agent is not None
    assert coordinator.simulation_agent is not None


@pytest.mark.asyncio
async def test_static_quiz_generation():
    """Test quiz generation with static team."""
    coordinator = CoordinatorAgent()

    result = await coordinator.generate_content(
        content_type="quiz",
        topic="Python Programming",
        num_questions=3,
    )

    assert result is not None
    assert "content" in result
    content = result["content"]
    assert "title" in content
    assert "questions" in content
    assert len(content["questions"]) == 3


@pytest.mark.asyncio
async def test_static_story_generation():
    """Test story generation with static team."""
    coordinator = CoordinatorAgent()

    result = await coordinator.generate_content(
        content_type="story",
        topic="Space Adventure",
        genre="sci-fi",
    )

    assert result is not None
    assert "content" in result
    content = result["content"]
    assert "title" in content
    assert "nodes" in content
    assert "start" in content["nodes"]


# Gemini Team Tests (stubs)


@pytest.mark.asyncio
async def test_gemini_coordinator_initialization():
    """Test Gemini coordinator initialization (stub)."""
    from adk_agentic_writer.agents.gemini import GeminiCoordinatorAgent

    coordinator = GeminiCoordinatorAgent()

    assert coordinator.agent_id == "gemini_coordinator"
    assert coordinator.quiz_agent is not None


@pytest.mark.asyncio
async def test_gemini_quiz_generation():
    """Test quiz generation with Gemini team (stub)."""
    from adk_agentic_writer.agents.gemini import GeminiCoordinatorAgent

    coordinator = GeminiCoordinatorAgent()

    result = await coordinator.generate_content(
        content_type="quiz",
        topic="Machine Learning",
        num_questions=2,
    )

    assert result is not None
    assert "content" in result
    content = result["content"]
    assert "title" in content
    assert "questions" in content
    assert len(content["questions"]) == 2


if __name__ == "__main__":
    print("Run tests with: pytest tests/integration/test_adk.py -v")
