"""Minimal tests proving the new 3-agent system wiring works.

All tests run offline (no GOOGLE_API_KEY, no LLM calls).
They verify: adk_utils, task resolution, prompt building, schema validation.
"""

import json
import os
import pytest

# ---------------------------------------------------------------------------
# 1. adk_utils — pure logic, no dependencies
# ---------------------------------------------------------------------------
from adk_agentic_writer.agents.adk_utils import (
    strip_code_fences,
    parse_json,
    detect_refusal,
    extract_text,
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
# 2. Coordinator — task resolution (no LLM, no API key)
# ---------------------------------------------------------------------------
from adk_agentic_writer.tasks.content_tasks import (
    GENERATE_QUIZ,
    GENERATE_STORY,
    GENERATE_GAME,
    GENERATE_SIMULATION,
)
from adk_agentic_writer.agents.coordinator import Coordinator, _PRIMARY_TASKS


class TestTaskResolution:
    """Test task resolution without instantiating Coordinator (avoids API key)."""

    def setup_method(self):
        self.task_by_id = {t.task_id: t for t in _PRIMARY_TASKS}
        self.type_to_task = {}
        for t in _PRIMARY_TASKS:
            for ct in t.content_types:
                self.type_to_task[ct] = t

    def test_resolve_by_task_id(self):
        assert self.task_by_id["generate_quiz"] is GENERATE_QUIZ
        assert self.task_by_id["generate_story"] is GENERATE_STORY
        assert self.task_by_id["generate_game"] is GENERATE_GAME
        assert self.task_by_id["generate_simulation"] is GENERATE_SIMULATION

    def test_resolve_by_content_type(self):
        assert self.type_to_task["quiz"] is GENERATE_QUIZ
        assert self.type_to_task["trivia"] is GENERATE_QUIZ
        assert self.type_to_task["story"] is GENERATE_STORY
        assert self.type_to_task["quest_game"] is GENERATE_GAME
        assert self.type_to_task["web_simulation"] is GENERATE_SIMULATION

    def test_all_primary_tasks_present(self):
        assert len(_PRIMARY_TASKS) == 4
        ids = {t.task_id for t in _PRIMARY_TASKS}
        assert ids == {
            "generate_quiz",
            "generate_story",
            "generate_game",
            "generate_simulation",
        }

    def test_effective_content_type_from_params(self):
        ct = Coordinator._effective_content_type(
            GENERATE_QUIZ, {"content_type": "trivia"}
        )
        assert ct == "trivia"

    def test_effective_content_type_from_task(self):
        ct = Coordinator._effective_content_type(GENERATE_QUIZ, {})
        assert ct == "quiz"

    def test_effective_content_type_default(self):
        from adk_agentic_writer.models.agent_models import AgentTask, AgentRole
        empty_task = AgentTask(
            task_id="empty", agent_role=AgentRole.WRITER, prompt="x",
            content_types=[],
        )
        ct = Coordinator._effective_content_type(empty_task, {})
        assert ct == "quiz"


# ---------------------------------------------------------------------------
# 3. Prompt building — WriterAgent._build_prompt (no LLM, patched init)
# ---------------------------------------------------------------------------
from adk_agentic_writer.agents.writer import WriterAgent


class TestPromptBuilding:
    """Test prompt construction without an API key by calling _build_prompt
    on a partially-initialised WriterAgent (skip __init__ entirely)."""

    def setup_method(self):
        self.writer = object.__new__(WriterAgent)
        self.writer._model_name = "test-model"
        self.writer._agents = {}
        self.writer._runners = {}

    def test_quiz_prompt_contains_topic(self):
        prompt = self.writer._build_prompt("quiz", {
            "topic": "Python",
            "num_questions": 5,
            "difficulty": "medium",
            "num_options": 4,
        })
        assert "Python" in prompt
        assert "5" in prompt  # num_questions

    def test_quiz_prompt_has_schema(self):
        prompt = self.writer._build_prompt("quiz", {
            "topic": "Math",
            "num_questions": 3,
            "difficulty": "easy",
            "num_options": 4,
        })
        assert "correct_answer" in prompt  # from schema description
        assert "tier" in prompt

    def test_story_prompt(self):
        prompt = self.writer._build_prompt("story", {
            "topic": "Dragons",
            "num_nodes": 7,
            "genre": "fantasy",
        })
        assert "Dragons" in prompt
        assert "fantasy" in prompt

    def test_unknown_type_uses_fallback(self):
        prompt = self.writer._build_prompt("unknown_type", {"topic": "X"})
        assert "X" in prompt  # at minimum, topic is used


# ---------------------------------------------------------------------------
# 4. ValidatorAgent._schema_validate — static method, no LLM
# ---------------------------------------------------------------------------
from adk_agentic_writer.agents.validator import ValidatorAgent


class TestSchemaValidation:
    def test_empty_content(self):
        result = ValidatorAgent._schema_validate({}, "quiz")
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
        result = ValidatorAgent._schema_validate(quiz, "quiz")
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
        result = ValidatorAgent._schema_validate(quiz, "quiz")
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
        result = ValidatorAgent._schema_validate(story, "story")
        assert result["valid"] is False
        assert any("start" in e.lower() for e in result["errors"])

    def test_unknown_type_still_works(self):
        result = ValidatorAgent._schema_validate({"some": "data"}, "unknown")
        assert result["valid"] is True
