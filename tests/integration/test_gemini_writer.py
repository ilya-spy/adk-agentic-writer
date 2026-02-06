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
from adk_agentic_writer.teams.content_team import (
    QUIZ_WRITER,
    STORY_WRITER,
    get_config_for_role,
    ContentRole,
)
from adk_agentic_writer.models.content_models import Quiz, BranchedNarrative
from adk_agentic_writer.tasks.content_tasks import GENERATE_QUIZ, GENERATE_STORY


class TestAgentConfigPrompts:
    """Test AgentConfig data and BaseAgent prompt methods."""

    def test_quiz_config_has_prompts(self):
        """Test QUIZ_WRITER config has prompt templates."""
        assert "quiz_question" in QUIZ_WRITER.prompt_templates
        assert "quiz_option" in QUIZ_WRITER.prompt_templates
        assert "quiz_explanation" in QUIZ_WRITER.prompt_templates

    def test_story_config_has_prompts(self):
        """Test STORY_WRITER config has prompt templates."""
        assert "story_opening" in STORY_WRITER.prompt_templates
        assert "story_path" in STORY_WRITER.prompt_templates
        assert "story_ending" in STORY_WRITER.prompt_templates

    def test_get_prompt_via_agent(self):
        """Test agent.get_prompt with variable substitution."""
        agent = GeminiWriterAgent(content_type="quiz")
        prompt = agent.get_prompt(
            "quiz_question", {"topic": "Python", "difficulty": "medium"}
        )
        assert "Python" in prompt
        assert "medium" in prompt

    def test_build_generation_prompt_via_agent(self):
        """Test agent.build_generation_prompt includes context."""
        agent = GeminiWriterAgent(content_type="quiz")
        prompt = agent.build_generation_prompt(
            context={"topic": "Python", "num_questions": 5, "difficulty": "medium"}
        )
        assert "Python" in prompt
        assert "5" in prompt

    def test_get_config_for_role(self):
        """Test get_config_for_role returns correct config."""
        assert get_config_for_role("quiz") == QUIZ_WRITER
        assert get_config_for_role("story") == STORY_WRITER
        assert get_config_for_role(ContentRole.QUIZ_WRITER) == QUIZ_WRITER

    def test_apply_modifiers_via_agent(self):
        """Test agent.apply_prompt_modifiers adds modifier text."""
        agent = GeminiWriterAgent(content_type="quiz")
        base_prompt = "Generate a quiz."
        modified = agent.apply_prompt_modifiers(base_prompt, ["difficulty_hard"])
        assert "challenging" in modified.lower()


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

    def test_init_uses_role_config(self):
        """Test agent uses config from content_team."""
        agent = GeminiWriterAgent(content_type="quiz")
        assert agent.config.role == ContentRole.QUIZ_WRITER
        assert "quiz_question" in agent.config.prompt_templates

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


class TestGeminiWriterPromptMethods:
    """Test prompt building methods on agent."""

    def test_get_prompt(self):
        """Test agent.get_prompt uses config."""
        agent = GeminiWriterAgent(content_type="quiz")
        agent.update_parameters({"topic": "Python"})
        prompt = agent.get_prompt("quiz_question", {"difficulty": "hard"})
        assert "Python" in prompt

    def test_build_generation_prompt(self):
        """Test agent.build_generation_prompt uses config."""
        agent = GeminiWriterAgent(content_type="quiz")
        prompt = agent.build_generation_prompt(
            {"topic": "Python", "num_questions": 3, "difficulty": "easy"}
        )
        assert "Python" in prompt
        assert "3" in prompt


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
        """Test wrapper initialization with config."""
        wrapper = ADKAgentWrapper(
            name="test_agent",
            config=QUIZ_WRITER,
            model_name="gemini-2.5-flash-lite",
        )
        assert wrapper.name == "test_agent"
        assert wrapper.model_name == "gemini-2.5-flash-lite"
        assert not wrapper._initialized

    def test_parse_json_response_clean(self):
        """Test parsing clean JSON response."""
        wrapper = ADKAgentWrapper(name="test", config=QUIZ_WRITER)
        result = wrapper._parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_response_markdown(self):
        """Test parsing JSON with markdown code blocks."""
        wrapper = ADKAgentWrapper(name="test", config=QUIZ_WRITER)
        result = wrapper._parse_json_response('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parse_json_response_invalid(self):
        """Test parsing invalid JSON returns error structure."""
        wrapper = ADKAgentWrapper(name="test", config=QUIZ_WRITER)
        result = wrapper._parse_json_response("not json")
        assert "error" in result


class TestGeminiTextProvider:
    """Test GeminiTextProvider class."""

    def test_provider_init(self):
        """Test provider initialization with config."""
        provider = GeminiTextProvider(config=QUIZ_WRITER)
        assert provider.config == QUIZ_WRITER
        assert provider.model_name == "gemini-2.5-flash-lite"

    @pytest.mark.asyncio
    async def test_provider_fallback(self):
        """Test provider falls back to templates without API key."""
        provider = GeminiTextProvider(config=QUIZ_WRITER)
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
        provider = GeminiTextProvider(config=QUIZ_WRITER)

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
