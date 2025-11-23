"""
Integration tests for ADK agents and coordinators.

This module tests the complete agent integration including:
- Static team coordinator
- Gemini team coordinator (if API key available)
- Content generation workflows

Requirements:
    - All dependencies installed
    - GOOGLE_API_KEY environment variable (optional, for Gemini tests)

Usage:
    pytest tests/integration/test_adk.py
    # or
    python -m pytest tests/integration/test_adk.py -v
"""

import os
import pytest

from adk_agentic_writer.agents.static import (
    CoordinatorAgent,
    StaticQuizWriterAgent,
    StoryWriterAgent,
    ReviewerAgent,
)
from adk_agentic_writer.models.agent_models import AgentStatus


# Static Team Tests

@pytest.mark.asyncio
async def test_static_coordinator_initialization():
    """Test static coordinator initialization."""
    coordinator = CoordinatorAgent()
    coordinator.register_agent(StaticQuizWriterAgent())
    coordinator.register_agent(StoryWriterAgent())
    
    assert coordinator.agent_id == "coordinator"
    assert len(coordinator.agent_registry) > 0


@pytest.mark.asyncio
async def test_static_quiz_generation():
    """Test quiz generation with static team."""
    coordinator = CoordinatorAgent()
    coordinator.register_agent(StaticQuizWriterAgent())
    
    result = await coordinator.process_task(
        "Generate quiz",
        {
            "content_type": "quiz",
            "topic": "Python Programming",
            "num_questions": 3,
        }
    )
    
    assert result is not None
    assert "content" in result
    content = result["content"]
    assert "title" in content or "questions" in content


@pytest.mark.asyncio
async def test_static_story_generation():
    """Test story generation with static team."""
    coordinator = CoordinatorAgent()
    coordinator.register_agent(StoryWriterAgent())
    
    result = await coordinator.process_task(
        "Generate story",
        {
            "content_type": "branched_narrative",
            "topic": "Space Adventure",
            "num_branches": 3,
        }
    )
    
    assert result is not None
    assert "content" in result
    content = result["content"]
    assert "title" in content or "nodes" in content


# Gemini Team Tests (require API key)

@pytest.fixture
def api_key():
    """Get API key from environment."""
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        pytest.skip("GOOGLE_API_KEY environment variable not set")
    return key


@pytest.mark.asyncio
@pytest.mark.slow
async def test_gemini_coordinator_initialization(api_key):
    """Test Gemini coordinator initialization."""
    try:
        from adk_agentic_writer.agents.gemini import (
            GeminiCoordinatorAgent,
            GeminiQuizWriterAgent,
        )
        
        coordinator = GeminiCoordinatorAgent()
        coordinator.register_agent(GeminiQuizWriterAgent())
        
        assert coordinator.agent_id == "gemini_coordinator"
        assert coordinator.adk_agent is not None
        assert coordinator.runner is not None
    except ImportError as e:
        pytest.skip(f"Google ADK not installed: {e}")


@pytest.mark.asyncio
@pytest.mark.slow
async def test_gemini_quiz_generation(api_key):
    """Test quiz generation with Gemini team."""
    try:
        from adk_agentic_writer.agents.gemini import (
            GeminiCoordinatorAgent,
            GeminiQuizWriterAgent,
            SupportedTask,
        )
        
        coordinator = GeminiCoordinatorAgent()
        coordinator.register_agent(GeminiQuizWriterAgent())
        
        result = await coordinator.process_task(
            "Generate quiz",
            {
                "task": SupportedTask.GENERATE_QUIZ,
                "topic": "Python Programming",
                "num_questions": 2,
            }
        )
        
        assert result is not None
        # Result structure may vary, just check it's not empty
        assert len(result) > 0
    except ImportError as e:
        pytest.skip(f"Google ADK not installed: {e}")
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
            pytest.skip(f"API quota exceeded: {e}")
        raise


# Utility function for manual testing
def run_manual_tests():
    """Run tests manually (for development)."""
    print("\n" + "="*60)
    print("ADK Integration Manual Test Suite")
    print("="*60)
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("\n⚠ WARNING: GOOGLE_API_KEY environment variable not set!")
        print("  Static team tests will run, but Gemini tests will be skipped.")
        print("\nTo enable Gemini tests:")
        print("  export GOOGLE_API_KEY='your-key-here'")
        print("\nGet your API key at: https://aistudio.google.com/apikey")
    else:
        print(f"✓ API key found: {api_key[:10]}...{api_key[-4:]}")
    
    print("\nRun tests with: pytest tests/integration/test_adk.py -v")
    print("Run slow tests: pytest tests/integration/test_adk.py -v -m slow")


if __name__ == "__main__":
    run_manual_tests()
