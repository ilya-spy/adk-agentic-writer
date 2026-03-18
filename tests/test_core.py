"""Tests for the ADK Agentic Writer system.

All tests run offline (no GOOGLE_API_KEY, no LLM calls).
Covers: response parsing, format registry, prompt building,
schema validation, and workflow construction.
"""

import json
import os
import pytest

# ---------------------------------------------------------------------------
# 1. Response utilities (pure logic)
# ---------------------------------------------------------------------------
from adk_agentic_writer.utils.response import (
    strip_code_fences,
    parse_json,
    detect_refusal,
    extract_text,
    _repair_truncated_json,
)


class TestStripCodeFences:
    def test_json_fence(self):
        assert strip_code_fences('```json\n{"a":1}\n```') == '{"a":1}'

    def test_plain_fence(self):
        assert strip_code_fences('```\n{"a":1}\n```') == '{"a":1}'

    def test_no_fence(self):
        assert strip_code_fences('{"a":1}') == '{"a":1}'


class TestParseJson:
    def test_clean_json(self):
        assert parse_json('{"x": 42}') == {"x": 42}

    def test_fenced_json(self):
        assert parse_json('```json\n{"x": 42}\n```') == {"x": 42}

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_json("not json at all {{{")

    def test_refusal_raises(self):
        with pytest.raises(ValueError, match="LLM refused"):
            parse_json("I cannot generate that content for safety reasons.")

    def test_escape_repair(self):
        raw = """{"msg": "it\\'s fine"}"""
        result = parse_json(raw)
        assert result["msg"] == "it's fine"


class TestRepairTruncatedJson:
    def test_truncated_object(self):
        raw = '{"title": "Quiz", "questions": [{"q": "What?"'
        repaired = _repair_truncated_json(raw)
        assert repaired is not None
        result = json.loads(repaired)
        assert result["title"] == "Quiz"

    def test_truncated_array_element(self):
        raw = '{"items": [1, 2, 3'
        repaired = _repair_truncated_json(raw)
        assert repaired is not None
        result = json.loads(repaired)
        assert result["items"] == [1, 2, 3]

    def test_truncated_mid_string(self):
        raw = '{"name": "hello wor'
        repaired = _repair_truncated_json(raw)
        assert repaired is not None
        result = json.loads(repaired)
        assert "hello" in result["name"]

    def test_complete_json_returns_none(self):
        assert _repair_truncated_json('{"a": 1}') is None

    def test_truncated_nested(self):
        raw = '{"outer": {"inner": [1, 2'
        repaired = _repair_truncated_json(raw)
        assert repaired is not None
        result = json.loads(repaired)
        assert result["outer"]["inner"] == [1, 2]

    def test_parse_json_uses_repair(self):
        raw = '{"title": "Test", "items": [{"x": 1}, {"x": 2'
        result = parse_json(raw, agent_name="test")
        assert result["title"] == "Test"
        assert len(result["items"]) >= 1


class TestDetectRefusal:
    def test_json_not_refused(self):
        assert detect_refusal('{"valid": true}') is None

    def test_refusal_detected(self):
        assert detect_refusal("I'm sorry, I cannot generate that.") is not None

    def test_normal_text_not_refused(self):
        assert detect_refusal("Here is the quiz about Python.") is None


class TestExtractText:
    def test_string_passthrough(self):
        assert extract_text("hello") == "hello"

    def test_object_with_text(self):
        class FakeResp:
            text = "result"
        assert extract_text(FakeResp()) == "result"


# ---------------------------------------------------------------------------
# 2. Format registry
# ---------------------------------------------------------------------------
from adk_agentic_writer.formats import (
    FORMAT_REGISTRY,
    get_format,
    list_formats,
    QUIZ_FORMAT,
    STORY_FORMAT,
    GAME_FORMAT,
    SIMULATION_FORMAT,
)


class TestFormatRegistry:
    def test_four_base_formats(self):
        fmts = list_formats()
        names = {f.name for f in fmts}
        assert names == {"quiz", "story", "game", "simulation"}

    def test_lookup_by_name(self):
        assert get_format("quiz") is QUIZ_FORMAT
        assert get_format("story") is STORY_FORMAT
        assert get_format("game") is GAME_FORMAT
        assert get_format("simulation") is SIMULATION_FORMAT

    def test_lookup_by_alias(self):
        assert get_format("trivia") is QUIZ_FORMAT
        assert get_format("narrative") is STORY_FORMAT
        assert get_format("quest_game") is GAME_FORMAT
        assert get_format("web_simulation") is SIMULATION_FORMAT

    def test_unknown_returns_none(self):
        assert get_format("nonexistent") is None

    def test_format_has_prompts(self):
        for fmt in list_formats():
            assert fmt.writer_instruction, f"{fmt.name} missing writer_instruction"
            assert fmt.writer_prompt, f"{fmt.name} missing writer_prompt"
            assert fmt.reviewer_prompt, f"{fmt.name} missing reviewer_prompt"
            assert fmt.refiner_prompt, f"{fmt.name} missing refiner_prompt"

    def test_format_has_parameter_specs(self):
        for fmt in list_formats():
            assert len(fmt.parameter_specs) > 0, f"{fmt.name} missing parameter_specs"

    def test_quiz_params(self):
        assert QUIZ_FORMAT.default_params["num_questions"] == 5
        names = [p.name for p in QUIZ_FORMAT.parameter_specs]
        assert "num_questions" in names
        assert "difficulty" in names


# ---------------------------------------------------------------------------
# 3. Task resolution
# ---------------------------------------------------------------------------
from adk_agentic_writer.tasks.content_tasks import (
    GENERATE_QUIZ,
    GENERATE_STORY,
    GENERATE_GAME,
    GENERATE_SIMULATION,
)
from adk_agentic_writer.agents.coordinator import Coordinator


class TestTaskResolution:
    """Test task resolution without instantiating Coordinator."""

    def setup_method(self):
        tasks = [GENERATE_QUIZ, GENERATE_STORY, GENERATE_GAME, GENERATE_SIMULATION]
        self.task_by_id = {t.task_id: t for t in tasks}
        self.type_to_task = {}
        for t in tasks:
            for ct in t.content_types:
                self.type_to_task[ct] = t

    def test_resolve_by_task_id(self):
        assert self.task_by_id["generate_quiz"] is GENERATE_QUIZ
        assert self.task_by_id["generate_story"] is GENERATE_STORY

    def test_resolve_by_content_type(self):
        assert self.type_to_task["quiz"] is GENERATE_QUIZ
        assert self.type_to_task["trivia"] is GENERATE_QUIZ
        assert self.type_to_task["story"] is GENERATE_STORY

    def test_all_primary_tasks_present(self):
        ids = {t.task_id for t in [GENERATE_QUIZ, GENERATE_STORY, GENERATE_GAME, GENERATE_SIMULATION]}
        assert ids == {"generate_quiz", "generate_story", "generate_game", "generate_simulation"}

    def test_effective_content_type_from_params(self):
        ct = Coordinator._effective_content_type(GENERATE_QUIZ, {"content_type": "trivia"})
        assert ct == "trivia"

    def test_effective_content_type_from_task(self):
        ct = Coordinator._effective_content_type(GENERATE_QUIZ, {})
        assert ct == "quiz"

    def test_effective_content_type_default(self):
        from adk_agentic_writer.models.agent_models import AgentTask, AgentRole
        empty = AgentTask(task_id="empty", agent_role=AgentRole.WRITER, prompt="x", content_types=[])
        ct = Coordinator._effective_content_type(empty, {})
        assert ct == "quiz"


# ---------------------------------------------------------------------------
# 4. Prompt building from format specs
# ---------------------------------------------------------------------------

class TestPromptBuilding:
    def test_quiz_prompt_contains_topic(self):
        prompt = QUIZ_FORMAT.writer_prompt.format(
            topic="Python", num_questions=5, difficulty="medium", num_options=4,
        )
        assert "Python" in prompt
        assert "5" in prompt

    def test_quiz_prompt_has_schema(self):
        assert "correct_answer" in QUIZ_FORMAT.schema_description
        assert "tier" in QUIZ_FORMAT.schema_description

    def test_story_prompt(self):
        prompt = STORY_FORMAT.writer_prompt.format(
            topic="Dragons", num_nodes=7, genre="fantasy",
        )
        assert "Dragons" in prompt
        assert "fantasy" in prompt


# ---------------------------------------------------------------------------
# 5. Schema validation (from reviewer module)
# ---------------------------------------------------------------------------
from adk_agentic_writer.agents.reviewer import schema_validate


class TestSchemaValidation:
    def test_empty_content(self):
        result = schema_validate({}, "quiz")
        assert result["valid"] is False
        assert any("empty" in e.lower() for e in result["errors"])

    def test_valid_quiz(self):
        quiz = {
            "title": "Test Quiz",
            "description": "A test",
            "difficulty": "medium",
            "questions": [
                {
                    "question": "What is 2+2?",
                    "options": ["3", "4", "5", "6"],
                    "correct_answer": 1,
                    "explanation": "Basic math",
                    "tier": "low",
                    "score": 1,
                }
            ],
            "passing_score": 70,
        }
        result = schema_validate(quiz, "quiz")
        assert result["valid"] is True
        assert result["score"] == 100

    def test_quiz_bad_index(self):
        quiz = {
            "title": "Bad Quiz",
            "description": "Test",
            "difficulty": "easy",
            "questions": [
                {
                    "question": "Q?",
                    "options": ["A", "B"],
                    "correct_answer": 5,
                    "tier": "low",
                    "score": 1,
                }
            ],
            "passing_score": 70,
        }
        result = schema_validate(quiz, "quiz")
        assert result["valid"] is False
        assert any("out of bounds" in e for e in result["errors"])

    def test_story_missing_start(self):
        story = {
            "title": "No Start",
            "synopsis": "A story",
            "genre": "fantasy",
            "start_node": "start",
            "nodes": {"node_1": {"node_id": "node_1", "content": "...", "branches": []}},
            "characters": [],
        }
        result = schema_validate(story, "story")
        assert result["valid"] is False
        assert any("start" in e.lower() for e in result["errors"])

    def test_unknown_type_still_works(self):
        result = schema_validate({"some": "data"}, "unknown")
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# 6. Workflow construction (verifies factories return correct types)
# ---------------------------------------------------------------------------

class TestWorkflowConstruction:
    def test_write_review_creates_sequential(self):
        from adk_agentic_writer.workflows import create_write_review_pipeline
        pipeline = create_write_review_pipeline(QUIZ_FORMAT)
        assert pipeline.name == "WriteReview_quiz"
        assert len(pipeline.sub_agents) == 2

    def test_refinement_creates_sequential_with_loop(self):
        from adk_agentic_writer.workflows import create_refinement_pipeline
        pipeline = create_refinement_pipeline(STORY_FORMAT, max_iterations=2)
        assert pipeline.name == "WriteAndRefine_story"
        assert len(pipeline.sub_agents) == 2

    def test_publish_creates_full_pipeline(self):
        from adk_agentic_writer.workflows import create_publish_pipeline
        pipeline = create_publish_pipeline(GAME_FORMAT)
        assert pipeline.name == "PublishPipeline_game"
        assert len(pipeline.sub_agents) == 3
