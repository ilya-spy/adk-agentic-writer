"""Integration tests for Gemini Writer Agent.

These tests require GOOGLE_API_KEY to be set for full ADK testing.
Without API key, tests verify fallback to static templates works.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from adk_agentic_writer.agents.gemini.writer import (
    GeminiWriterAgent,
    GeminiQuizWriterAgent,
    GeminiStoryWriterAgent,
    ADKAgentWrapper,
    GeminiTextProvider,
)
from adk_agentic_writer.agents.gemini.prompts import (
    build_quiz_prompt,
    build_story_prompt,
    get_system_instruction,
    QUIZ_SYSTEM_INSTRUCTION,
    STORY_SYSTEM_INSTRUCTION,
)
from adk_agentic_writer.models.content_models import Quiz, BranchedNarrative
from adk_agentic_writer.tasks.content_tasks import GENERATE_QUIZ, GENERATE_STORY


class TestGeminiPrompts:
    """Test prompt building functions."""

    def test_build_quiz_prompt(self):
        """Test quiz prompt generation."""
        prompt = build_quiz_prompt(topic="Python", num_questions=5, difficulty="medium")
        assert "Python" in prompt
        assert "5" in prompt
        assert "medium" in prompt
        assert "JSON" in prompt  # Schema description included

    def test_build_story_prompt(self):
        """Test story prompt generation."""
        prompt = build_story_prompt(topic="Dragons", num_nodes=7, genre="fantasy")
        assert "Dragons" in prompt
        assert "7" in prompt
        assert "fantasy" in prompt
        assert "JSON" in prompt

    def test_get_system_instruction_quiz(self):
        """Test system instruction for quiz types."""
        for content_type in ["quiz", "trivia", "test"]:
            instruction = get_system_instruction(content_type)
            assert instruction == QUIZ_SYSTEM_INSTRUCTION

    def test_get_system_instruction_story(self):
        """Test system instruction for story types."""
        for content_type in ["story", "narrative", "adventure"]:
            instruction = get_system_instruction(content_type)
            assert instruction == STORY_SYSTEM_INSTRUCTION


class TestGeminiWriterAgentInit:
    """Test GeminiWriterAgent initialization."""

    def test_init_quiz_writer(self):
        """Test quiz writer initialization."""
        agent = GeminiWriterAgent(agent_id="test_quiz", content_type="quiz")
        assert agent.agent_id == "test_quiz"
        assert agent.content_type == "quiz"
        assert GENERATE_QUIZ in agent.supported_tasks

    def test_init_story_writer(self):
        """Test story writer initialization."""
        agent = GeminiWriterAgent(agent_id="test_story", content_type="story")
        assert agent.content_type == "story"
        assert GENERATE_STORY in agent.supported_tasks

    def test_init_with_custom_model(self):
        """Test initialization with custom model name."""
        agent = GeminiWriterAgent(
            agent_id="custom",
            content_type="quiz",
            model_name="gemini-2.0-flash",
        )
        assert agent._model_name == "gemini-2.0-flash"

    def test_init_invalid_content_type(self):
        """Test initialization with invalid content type."""
        with pytest.raises(ValueError, match="Unknown content type"):
            GeminiWriterAgent(content_type="invalid_type")

    def test_init_wrong_category(self):
        """Test initialization with non-writer content type."""
        with pytest.raises(ValueError, match="not a writer type"):
            GeminiWriterAgent(content_type="game")


class TestGeminiWriterAliases:
    """Test backward-compatible alias classes."""

    def test_quiz_writer_alias(self):
        """Test GeminiQuizWriterAgent alias."""
        agent = GeminiQuizWriterAgent()
        assert agent.content_type == "quiz"
        assert "quiz" in agent.agent_id

    def test_story_writer_alias(self):
        """Test GeminiStoryWriterAgent alias."""
        agent = GeminiStoryWriterAgent()
        assert agent.content_type == "story"
        assert "story" in agent.agent_id


class TestGeminiWriterFallback:
    """Test fallback to static templates when ADK unavailable."""

    @pytest.mark.asyncio
    async def test_generate_question_fallback(self):
        """Test question generation falls back to templates."""
        agent = GeminiWriterAgent(content_type="quiz")
        question = await agent.generate_question(topic="Python", difficulty="medium")

        assert question.question  # Has question text
        assert len(question.options) == 4  # Has 4 options
        assert 0 <= question.correct_answer <= 3  # Valid correct index
        assert question.explanation  # Has explanation

    @pytest.mark.asyncio
    async def test_generate_story_node_fallback(self):
        """Test story node generation falls back to templates."""
        agent = GeminiWriterAgent(content_type="story")
        node = await agent.generate_story_node(
            node_id="start",
            topic="Dragons",
            genre="fantasy",
        )

        assert node.node_id == "start"
        assert node.content  # Has content text
        assert not node.is_ending

    @pytest.mark.asyncio
    async def test_build_quiz_fallback(self):
        """Test full quiz building with fallback."""
        agent = GeminiWriterAgent(content_type="quiz")
        result = await agent._build_quiz(
            {
                "topic": "Python",
                "num_questions": 3,
                "difficulty": "easy",
            }
        )

        # Validate structure
        assert "title" in result
        assert "questions" in result
        assert len(result["questions"]) == 3

    @pytest.mark.asyncio
    async def test_build_story_fallback(self):
        """Test full story building with fallback."""
        agent = GeminiWriterAgent(content_type="story")
        result = await agent._build_story(
            {
                "topic": "Adventure",
                "genre": "fantasy",
                "num_nodes": 5,
            }
        )

        # Validate structure
        assert "title" in result
        assert "nodes" in result
        assert "start" in result["nodes"]


class TestADKAgentWrapper:
    """Test ADKAgentWrapper class."""

    def test_wrapper_init(self):
        """Test wrapper initialization."""
        wrapper = ADKAgentWrapper(
            name="test_agent",
            model_name="gemini-2.5-flash-lite",
            instruction="Test instruction",
        )
        assert wrapper.name == "test_agent"
        assert wrapper.model_name == "gemini-2.5-flash-lite"
        assert not wrapper._initialized

    def test_parse_json_response_clean(self):
        """Test parsing clean JSON response."""
        wrapper = ADKAgentWrapper(name="test")
        result = wrapper._parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_response_markdown(self):
        """Test parsing JSON with markdown code blocks."""
        wrapper = ADKAgentWrapper(name="test")
        result = wrapper._parse_json_response('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parse_json_response_invalid(self):
        """Test parsing invalid JSON returns error structure."""
        wrapper = ADKAgentWrapper(name="test")
        result = wrapper._parse_json_response("not json")
        assert "error" in result


class TestGeminiTextProvider:
    """Test GeminiTextProvider class."""

    def test_provider_init(self):
        """Test provider initialization."""
        provider = GeminiTextProvider()
        assert provider.model_name == "gemini-2.5-flash-lite"

    @pytest.mark.asyncio
    async def test_provider_fallback(self):
        """Test provider falls back to templates without API key."""
        provider = GeminiTextProvider()
        text = await provider.generate_text("quiz_question", {"topic": "Python"})
        assert text  # Returns something
        assert "Python" in text  # Topic is in text


@pytest.mark.skipif(
    not os.environ.get("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set - skipping live ADK tests",
)
class TestGeminiWriterLive:
    """Live tests requiring GOOGLE_API_KEY.

    These tests make actual API calls to Gemini.
    Run with: GOOGLE_API_KEY=your_key pytest tests/integration/test_gemini_writer.py -v

    Note: Tests may fail with 429 rate limiting on free tier.
    This is expected and confirms the integration is working.
    """

    @pytest.mark.asyncio
    async def test_live_quiz_generation(self):
        """Test live quiz generation with ADK."""
        agent = GeminiWriterAgent(content_type="quiz")
        assert agent.adk_enabled, "ADK should be enabled with API key"

        try:
            result = await agent._build_content_with_adk(
                {
                    "task_id": "generate_quiz",
                    "topic": "Python basics",
                    "num_questions": 2,
                    "difficulty": "easy",
                }
            )

            assert "title" in result
            assert "questions" in result
            assert len(result["questions"]) >= 1
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                pytest.skip("Rate limited by Gemini API (free tier limit)")
            raise

    @pytest.mark.asyncio
    async def test_live_story_generation(self):
        """Test live story generation with ADK."""
        agent = GeminiWriterAgent(content_type="story")

        try:
            result = await agent._build_content_with_adk(
                {
                    "task_id": "generate_story",
                    "topic": "A magical forest",
                    "num_nodes": 3,
                    "genre": "fantasy",
                }
            )

            assert "title" in result
            assert "nodes" in result
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                pytest.skip("Rate limited by Gemini API (free tier limit)")
            raise

    @pytest.mark.asyncio
    async def test_live_text_generation(self):
        """Test live text generation."""
        provider = GeminiTextProvider()

        try:
            text = await provider.generate_text(
                "quiz_question", {"topic": "Machine Learning", "difficulty": "medium"}
            )

            assert text
            assert len(text) > 10  # Got substantial content
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                pytest.skip("Rate limited by Gemini API (free tier limit)")
            raise
