"""Integration tests for Gemini Writer Agent.

Tests require GOOGLE_API_KEY for live LLM tests.
Non-live tests verify configuration and initialization.
"""

import os
import pytest
from unittest.mock import patch

from adk_agentic_writer.agents.gemini.wrapper import ADKAgentWrapper
from adk_agentic_writer.agents.gemini.writer import (
    GeminiWriterAgent,
    GeminiQuizWriterAgent,
    GeminiStoryWriterAgent,
)
from adk_agentic_writer.teams.content_team import (
    QUIZ_WRITER,
    STORY_WRITER,
    get_config_for_role,
    ContentRole,
)
from adk_agentic_writer.tasks.content_tasks import GENERATE_QUIZ, GENERATE_STORY
from adk_agentic_writer.utils.content_registry import CONTENT_REGISTRY


class TestAgentConfigPrompts:
    """Test AgentConfig data and prompt templates."""

    def test_quiz_config_has_prompts(self):
        """Test QUIZ_WRITER config has required prompt templates."""
        assert "quiz_question_complete" in QUIZ_WRITER.prompt_templates
        assert "quiz_question" in QUIZ_WRITER.prompt_templates

    def test_story_config_has_prompts(self):
        """Test STORY_WRITER config has required prompt templates."""
        assert "story_node_complete" in STORY_WRITER.prompt_templates
        assert "story_structure" in STORY_WRITER.prompt_templates
        assert "story_ending" in STORY_WRITER.prompt_templates

    def test_quiz_generation_prompt_has_num_options(self):
        """Test that quiz generation prompt includes {num_options} placeholder."""
        assert "{num_options}" in QUIZ_WRITER.generation_prompt

    def test_quiz_generation_prompt_has_scoring(self):
        """Test quiz generation prompt mentions scoring and time_limit."""
        prompt = QUIZ_WRITER.generation_prompt
        assert "score" in prompt.lower()
        assert "passing_score" in prompt.lower()
        assert "time_limit" in prompt.lower()

    def test_quiz_generation_prompt_has_tiers(self):
        """Test quiz generation prompt specifies scoring tiers via 'tier' field."""
        prompt = QUIZ_WRITER.generation_prompt
        assert "low" in prompt
        assert "mid" in prompt
        assert "high" in prompt
        assert "passing_score" in prompt

    def test_quiz_question_complete_has_score(self):
        """Test quiz_question_complete template includes score field."""
        template = QUIZ_WRITER.prompt_templates["quiz_question_complete"]
        assert "score" in template.lower()

    def test_get_prompt_via_agent(self):
        """Test agent.get_prompt with variable substitution."""
        agent = GeminiWriterAgent(content_type="quiz")
        prompt = agent.get_prompt(
            "quiz_question_complete",
            {"topic": "Python", "difficulty": "medium", "num_options": 4},
        )
        assert "Python" in prompt
        assert "medium" in prompt

    def test_build_generation_prompt_via_agent(self):
        """Test agent.build_generation_prompt includes context."""
        agent = GeminiWriterAgent(content_type="quiz")
        prompt = agent.build_generation_prompt(
            context={
                "topic": "Python",
                "num_questions": 5,
                "difficulty": "medium",
                "num_options": 4,
            }
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


class TestContentRegistry:
    """Test content registry integration."""

    def test_quiz_in_registry(self):
        """Test quiz type is in registry."""
        config = CONTENT_REGISTRY.get("quiz")
        assert config is not None
        assert config.schema_description
        assert config.sample_output

    def test_quiz_default_params_include_num_options(self):
        """Test quiz default_params includes num_options."""
        config = CONTENT_REGISTRY.get("quiz")
        assert "num_options" in config.default_params
        assert config.default_params["num_options"] == 4

    def test_quiz_schema_mentions_score(self):
        """Test quiz schema description includes score and time_limit."""
        config = CONTENT_REGISTRY.get("quiz")
        assert "score" in config.schema_description.lower()
        assert "time_limit" in config.schema_description.lower()

    def test_quiz_sample_output_has_score(self):
        """Test quiz sample output includes score, time_limit, and 3 tiers."""
        config = CONTENT_REGISTRY.get("quiz")
        assert config.sample_output.get("time_limit") is not None
        questions = config.sample_output["questions"]
        assert len(questions) >= 3
        tiers = {q["tier"] for q in questions}
        assert tiers == {"low", "mid", "high"}
        for q in questions:
            assert "score" in q

    def test_story_in_registry(self):
        """Test story type is in registry."""
        config = CONTENT_REGISTRY.get("story")
        assert config is not None
        assert config.schema_description

    def test_all_writer_types_in_registry(self):
        """Test all writer content types are registered."""
        for ct in ["quiz", "story", "branched_narrative"]:
            config = CONTENT_REGISTRY.get(ct)
            assert config is not None, f"Missing registry entry for {ct}"
            assert config.category == "writer"

    def test_all_designer_types_in_registry(self):
        """Test all designer content types are registered."""
        for ct in ["game", "quest_game", "simulation", "web_simulation"]:
            config = CONTENT_REGISTRY.get(ct)
            assert config is not None, f"Missing registry entry for {ct}"
            assert config.category == "designer"


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
        assert "quiz_question_complete" in agent.config.prompt_templates

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
    """Test convenience alias classes."""

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
        agent.update_parameters({"topic": "Python", "num_options": 4})
        prompt = agent.get_prompt("quiz_question_complete", {"difficulty": "hard"})
        assert "Python" in prompt

    def test_build_generation_prompt(self):
        """Test agent.build_generation_prompt uses config."""
        agent = GeminiWriterAgent(content_type="quiz")
        prompt = agent.build_generation_prompt(
            {"topic": "Python", "num_questions": 3, "difficulty": "easy", "num_options": 4}
        )
        assert "Python" in prompt
        assert "3" in prompt

    def test_build_generation_prompt_with_schema(self):
        """Test build_generation_prompt includes schema from registry."""
        agent = GeminiWriterAgent(content_type="quiz")
        config = CONTENT_REGISTRY.get("quiz")
        prompt = agent.build_generation_prompt(
            context={
                "topic": "Test",
                "num_questions": 2,
                "difficulty": "easy",
                "num_options": 4,
            },
            schema_description=config.schema_description,
            sample_output=config.sample_output,
        )
        assert "JSON" in prompt  # Schema included


class TestADKAgentWrapper:
    """Test ADKAgentWrapper class."""

    @pytest.mark.skipif(
        not os.environ.get("GOOGLE_API_KEY"),
        reason="GOOGLE_API_KEY required for wrapper initialization",
    )
    def test_wrapper_init_with_key(self):
        """Test wrapper initialization with API key."""
        wrapper = ADKAgentWrapper(
            name="test_agent",
            instruction=QUIZ_WRITER.instruction,
            model_name="gemini-2.5-flash-lite",
        )
        assert wrapper.name == "test_agent"
        assert wrapper.model_name == "gemini-2.5-flash-lite"

    def test_wrapper_init_without_key_raises(self):
        """Test wrapper raises without API key."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}, clear=False):
            # Remove the key temporarily
            original = os.environ.pop("GOOGLE_API_KEY", None)
            try:
                with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
                    ADKAgentWrapper(
                        name="test",
                        instruction="Test instruction",
                        model_name="gemini-2.5-flash-lite",
                    )
            finally:
                if original:
                    os.environ["GOOGLE_API_KEY"] = original

    @pytest.mark.skipif(
        not os.environ.get("GOOGLE_API_KEY"),
        reason="GOOGLE_API_KEY required",
    )
    def test_parse_json_clean(self):
        """Test parsing clean JSON response."""
        wrapper = ADKAgentWrapper(
            name="test",
            instruction=QUIZ_WRITER.instruction,
            model_name="gemini-2.5-flash-lite",
        )
        result = wrapper._parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    @pytest.mark.skipif(
        not os.environ.get("GOOGLE_API_KEY"),
        reason="GOOGLE_API_KEY required",
    )
    def test_parse_json_markdown(self):
        """Test parsing JSON with markdown code blocks."""
        wrapper = ADKAgentWrapper(
            name="test",
            instruction=QUIZ_WRITER.instruction,
            model_name="gemini-2.5-flash-lite",
        )
        result = wrapper._parse_json('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    @pytest.mark.skipif(
        not os.environ.get("GOOGLE_API_KEY"),
        reason="GOOGLE_API_KEY required",
    )
    def test_parse_json_invalid_raises(self):
        """Test parsing invalid JSON raises ValueError."""
        wrapper = ADKAgentWrapper(
            name="test",
            instruction=QUIZ_WRITER.instruction,
            model_name="gemini-2.5-flash-lite",
        )
        with pytest.raises(ValueError, match="Invalid JSON"):
            wrapper._parse_json("not json")


class TestContentValidation:
    """Test ADKAgentWrapper.validate_content_fields for all content types."""

    def test_quiz_validation_complete(self):
        """Test quiz validation with complete data."""
        result = {
            "title": "My Quiz",
            "description": "A test quiz",
            "questions": [
                {
                    "question": "What is 1+1?",
                    "options": ["1", "2", "3", "4"],
                    "correct_answer": 1,
                    "explanation": "Basic math",
                    "tier": "low",
                    "score": 1,
                }
            ],
            "passing_score": 1,
            "time_limit": 5,
        }
        warnings = ADKAgentWrapper.validate_content_fields(result, "quiz")
        assert len(warnings) == 0

    def test_quiz_validation_missing_fields(self):
        """Test quiz validation warns on missing fields."""
        result = {"questions": [{"question": "Q?"}]}
        warnings = ADKAgentWrapper.validate_content_fields(result, "quiz")
        assert any("title" in w for w in warnings)
        assert any("passing_score" in w for w in warnings)
        assert any("time_limit" in w for w in warnings)

    def test_quiz_validation_question_missing_options(self):
        """Test quiz validation warns on question missing options."""
        result = {
            "title": "Test",
            "questions": [{"question": "Q?", "correct_answer": 0}],
            "passing_score": 1,
            "time_limit": 5,
        }
        warnings = ADKAgentWrapper.validate_content_fields(result, "quiz")
        assert any("options" in w for w in warnings)

    def test_quiz_validation_question_missing_explanation(self):
        """Test quiz validation warns on question missing explanation."""
        result = {
            "title": "Test",
            "questions": [
                {
                    "question": "Q?",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 0,
                }
            ],
            "passing_score": 1,
            "time_limit": 5,
        }
        warnings = ADKAgentWrapper.validate_content_fields(result, "quiz")
        assert any("explanation" in w for w in warnings)

    def test_story_validation_complete(self):
        """Test story validation with complete data."""
        result = {
            "title": "My Story",
            "synopsis": "A test story",
            "nodes": {
                "start": {
                    "node_id": "start",
                    "content": "Beginning...",
                    "branches": [{"text": "Go", "next_node_id": "ending_0"}],
                    "is_ending": False,
                },
                "ending_0": {
                    "node_id": "ending_0",
                    "content": "The end.",
                    "branches": [],
                    "is_ending": True,
                },
            },
        }
        warnings = ADKAgentWrapper.validate_content_fields(result, "story")
        assert len(warnings) == 0

    def test_story_validation_missing_start(self):
        """Test story validation warns on missing start node."""
        result = {
            "title": "Test",
            "synopsis": "Test",
            "nodes": {
                "ending_0": {"content": "End", "is_ending": True}
            },
        }
        warnings = ADKAgentWrapper.validate_content_fields(result, "story")
        assert any("start" in w for w in warnings)

    def test_story_validation_missing_ending(self):
        """Test story validation warns on missing ending nodes."""
        result = {
            "title": "Test",
            "synopsis": "Test",
            "nodes": {
                "start": {
                    "content": "Begin",
                    "branches": [{"text": "Go", "next_node_id": "node_0"}],
                    "is_ending": False,
                },
                "node_0": {
                    "content": "Middle",
                    "branches": [],
                    "is_ending": False,
                },
            },
        }
        warnings = ADKAgentWrapper.validate_content_fields(result, "story")
        assert any("ending" in w.lower() for w in warnings)

    def test_story_validation_node_missing_content(self):
        """Test story validation warns on node missing content."""
        result = {
            "title": "Test",
            "synopsis": "Test",
            "nodes": {
                "start": {"branches": [], "is_ending": True},
            },
        }
        warnings = ADKAgentWrapper.validate_content_fields(result, "story")
        assert any("content" in w for w in warnings)

    def test_game_validation_complete(self):
        """Test game validation with complete data."""
        result = {
            "title": "My Game",
            "nodes": {
                "start": {
                    "title": "Begin",
                    "description": "Start the quest",
                    "choices": [],
                }
            },
        }
        warnings = ADKAgentWrapper.validate_content_fields(result, "game")
        assert len(warnings) == 0

    def test_game_validation_missing_fields(self):
        """Test game validation warns on missing fields."""
        result = {"nodes": {"start": {}}}
        warnings = ADKAgentWrapper.validate_content_fields(result, "game")
        assert any("title" in w for w in warnings)

    def test_simulation_validation_complete(self):
        """Test simulation validation with complete data."""
        result = {
            "title": "My Sim",
            "variables": [{"name": "x", "initial_value": 0}],
            "controls": [{"control_id": "c1", "label": "Speed", "type": "slider"}],
            "rules": ["x increases by 1 each tick"],
        }
        warnings = ADKAgentWrapper.validate_content_fields(result, "simulation")
        assert len(warnings) == 0

    def test_simulation_validation_missing_fields(self):
        """Test simulation validation warns on missing fields."""
        result = {"title": "My Sim"}
        warnings = ADKAgentWrapper.validate_content_fields(result, "simulation")
        assert any("variables" in w for w in warnings)
        assert any("controls" in w for w in warnings)
        assert any("rules" in w for w in warnings)


@pytest.mark.skipif(
    not os.environ.get("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set - skipping live ADK tests",
)
class TestGeminiWriterLive:
    """Live tests requiring GOOGLE_API_KEY.

    Run with: GOOGLE_API_KEY=your_key pytest tests/integration/test_gemini_writer.py -v -k Live
    """

    @pytest.mark.asyncio
    async def test_live_generate_question(self):
        """Test live question generation."""
        agent = GeminiWriterAgent(content_type="quiz")

        try:
            question = await agent.generate_question(topic="Python", difficulty="easy")

            assert question.question
            assert len(question.options) >= 2
            assert 0 <= question.correct_answer < len(question.options)
            assert question.explanation
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                pytest.skip("Rate limited by Gemini API")
            if "connection" in str(e).lower():
                pytest.skip("Network connection issue")
            raise

    @pytest.mark.asyncio
    async def test_live_generate_quiz(self):
        """Test live quiz generation."""
        agent = GeminiWriterAgent(content_type="quiz")

        try:
            quiz = await agent.generate_quiz(
                topic="Python basics", num_questions=2, difficulty="easy"
            )

            assert quiz.title
            assert len(quiz.questions) >= 1
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                pytest.skip("Rate limited by Gemini API")
            if "connection" in str(e).lower():
                pytest.skip("Network connection issue")
            raise

    @pytest.mark.asyncio
    async def test_live_generate_quiz_with_scoring(self):
        """Test live quiz generation returns scoring fields."""
        agent = GeminiWriterAgent(content_type="quiz")

        try:
            quiz = await agent.generate_quiz(
                topic="Basic math", num_questions=3, difficulty="easy", num_options=4
            )

            assert quiz.title
            assert len(quiz.questions) >= 1
            # passing_score should be set (either from LLM or default)
            assert quiz.passing_score is not None
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                pytest.skip("Rate limited by Gemini API")
            if "connection" in str(e).lower():
                pytest.skip("Network connection issue")
            raise

    @pytest.mark.asyncio
    async def test_live_generate_story(self):
        """Test live story generation."""
        agent = GeminiWriterAgent(content_type="story")

        try:
            story = await agent.generate_story(
                topic="A magical forest", genre="fantasy", num_nodes=3
            )

            assert story.title
            assert "start" in story.nodes
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                pytest.skip("Rate limited by Gemini API")
            if "connection" in str(e).lower():
                pytest.skip("Network connection issue")
            raise

    @pytest.mark.asyncio
    async def test_live_generate_story_node(self):
        """Test live story node generation."""
        agent = GeminiWriterAgent(content_type="story")

        try:
            node = await agent.generate_story_node(
                node_id="start",
                topic="Dragons",
                genre="fantasy",
                available_nodes=["node_0", "node_1"],
            )

            assert node.node_id == "start"
            assert node.content
            assert len(node.branches) > 0
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                pytest.skip("Rate limited by Gemini API")
            if "connection" in str(e).lower():
                pytest.skip("Network connection issue")
            raise
