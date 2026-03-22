"""Tests for the ADK Agentic Writer system.

All tests run offline (no GOOGLE_API_KEY, no LLM calls).
Covers: response parsing, format registry, flavors, unified tasks,
prompt building, schema validation, workflow construction, runtime store.
"""

import json
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
        fmt = get_format("quiz")
        assert fmt is not None
        assert fmt.name == "quiz"

    def test_lookup_by_flavor(self):
        fmt = get_format("trivia")
        assert fmt is not None
        assert fmt.name == "quiz"
        assert fmt.flavor == "trivia"

    def test_all_flavors_registered(self):
        assert get_format("narrative") is not None
        assert get_format("quest_game") is not None
        assert get_format("web_simulation") is not None

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
# 3. Flavors
# ---------------------------------------------------------------------------


class TestFlavors:
    def test_quiz_flavors(self):
        assert "trivia" in QUIZ_FORMAT.flavors
        assert "test" in QUIZ_FORMAT.flavors
        assert "quiz" not in QUIZ_FORMAT.flavors

    def test_flavor_creates_clone(self):
        trivia = get_format("trivia")
        quiz = get_format("quiz")
        assert trivia.flavor == "trivia"
        assert quiz.flavor == "quiz"
        assert trivia.name == quiz.name == "quiz"

    def test_each_flavor_has_own_spec(self):
        trivia = get_format("trivia")
        quiz = get_format("quiz")
        assert trivia is not quiz

    def test_flavor_in_default_params(self):
        trivia = get_format("trivia")
        assert trivia.default_params.get("flavor") == "trivia"

    def test_story_flavors(self):
        assert "narrative" in STORY_FORMAT.flavors
        assert "adventure" in STORY_FORMAT.flavors

    def test_topic_in_parameter_specs(self):
        for fmt in list_formats():
            param_names = [p.name for p in fmt.parameter_specs]
            assert "topic" in param_names, f"{fmt.name} missing 'topic' param"

    def test_flavor_in_parameter_specs(self):
        for fmt in list_formats():
            param_names = [p.name for p in fmt.parameter_specs]
            assert "flavor" in param_names, f"{fmt.name} missing 'flavor' param"


# ---------------------------------------------------------------------------
# 4. Unified tasks
# ---------------------------------------------------------------------------
from adk_agentic_writer.tasks import IDEATE, WRITE, REVIEW, REFINE, PUBLISH, ALL_TASKS


class TestUnifiedTasks:
    def test_all_tasks_present(self):
        ids = {t.task_id for t in ALL_TASKS}
        assert ids == {"ideate", "write", "review", "verify", "refine", "publish"}

    def test_output_keys(self):
        assert IDEATE.output_key == "ideation_result"
        assert WRITE.output_key == "draft_content"
        assert REVIEW.output_key == "review_result"
        assert REFINE.output_key == "draft_content"
        assert PUBLISH.output_key == "published_content"

    def test_task_has_parameters(self):
        for t in ALL_TASKS:
            assert t.parameters is not None, f"Task {t.task_id} missing parameters"


# ---------------------------------------------------------------------------
# 5. Prompt building from format specs
# ---------------------------------------------------------------------------


class TestPromptBuilding:
    def test_quiz_prompt_with_flavor(self):
        prompt = QUIZ_FORMAT.writer_prompt.format(
            topic="Python",
            flavor="trivia",
            num_questions=5,
            difficulty="medium",
            num_options=4,
        )
        assert "Python" in prompt
        assert "trivia" in prompt
        assert "5" in prompt

    def test_quiz_prompt_has_schema(self):
        assert "correct_answer" in QUIZ_FORMAT.schema_description
        assert "tier" in QUIZ_FORMAT.schema_description

    def test_story_prompt_with_flavor(self):
        prompt = STORY_FORMAT.writer_prompt.format(
            topic="Dragons",
            flavor="adventure",
            num_nodes=7,
            genre="fantasy",
        )
        assert "Dragons" in prompt
        assert "adventure" in prompt
        assert "fantasy" in prompt

    def test_game_prompt_with_flavor(self):
        prompt = GAME_FORMAT.writer_prompt.format(
            topic="Space",
            flavor="quest",
            num_nodes=5,
            complexity="medium",
        )
        assert "Space" in prompt
        assert "quest" in prompt
        assert "medium" in prompt

    def test_simulation_prompt_with_flavor(self):
        prompt = SIMULATION_FORMAT.writer_prompt.format(
            topic="Gravity",
            flavor="simulator",
            complexity="advanced",
        )
        assert "Gravity" in prompt
        assert "simulator" in prompt
        assert "advanced" in prompt


# ---------------------------------------------------------------------------
# 6. Schema validation (from reviewer module)
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
            "total_score": 1,
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
            "total_score": 1,
            "passing_score": 70,
        }
        result = schema_validate(quiz, "quiz")
        assert result["valid"] is False
        assert any("out of bounds" in e for e in result["errors"])

    def test_quiz_flavor_alias_validation(self):
        """schema_validate should work with flavor names like 'trivia'."""
        quiz = {
            "title": "Trivia",
            "description": "A trivia quiz",
            "difficulty": "easy",
            "questions": [
                {
                    "question": "Q?",
                    "options": ["A", "B"],
                    "correct_answer": 0,
                    "tier": "low",
                    "score": 1,
                }
            ],
            "total_score": 1,
            "passing_score": 50,
        }
        result = schema_validate(quiz, "trivia")
        assert result["valid"] is True

    def test_quiz_missing_total_score(self):
        quiz = {
            "title": "No Total",
            "description": "x",
            "difficulty": "easy",
            "questions": [
                {
                    "question": "Q?",
                    "options": ["A", "B"],
                    "correct_answer": 0,
                    "tier": "low",
                    "score": 1,
                }
            ],
            "passing_score": 1,
        }
        result = schema_validate(quiz, "quiz")
        assert result["valid"] is False
        assert any("total_score" in e.lower() for e in result["errors"])

    def test_quiz_total_score_mismatch(self):
        quiz = {
            "title": "Bad Total",
            "description": "x",
            "difficulty": "easy",
            "questions": [
                {
                    "question": "Q?",
                    "options": ["A", "B"],
                    "correct_answer": 0,
                    "tier": "mid",
                    "score": 2,
                }
            ],
            "total_score": 99,
            "passing_score": 1,
        }
        result = schema_validate(quiz, "quiz")
        assert result["valid"] is False
        assert any("total_score" in e.lower() for e in result["errors"])

    def test_story_missing_start(self):
        story = {
            "title": "No Start",
            "synopsis": "A story",
            "genre": "fantasy",
            "start_node": "start",
            "nodes": {
                "node_1": {"node_id": "node_1", "content": "...", "branches": []}
            },
            "characters": [],
        }
        result = schema_validate(story, "story")
        assert result["valid"] is False
        assert any("start" in e.lower() for e in result["errors"])

    def test_unknown_type_still_works(self):
        result = schema_validate({"some": "data"}, "unknown")
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# 7. Runtime store
# ---------------------------------------------------------------------------
from adk_agentic_writer.backend.runtime import RuntimeStore, NamedStore


class TestNamedStore:
    def test_set_and_get(self):
        ns = NamedStore()
        ns.set("a", 1)
        assert ns.get("a") == 1

    def test_get_missing(self):
        ns = NamedStore()
        assert ns.get("x") is None
        assert ns.get("x", 42) == 42

    def test_keys_and_all(self):
        ns = NamedStore()
        ns.set("a", 1)
        ns.set("b", 2)
        assert set(ns.keys()) == {"a", "b"}
        assert ns.all() == {"a": 1, "b": 2}

    def test_clear(self):
        ns = NamedStore()
        ns.set("a", 1)
        ns.clear()
        assert ns.keys() == []


class TestRuntimeStore:
    def test_outputs_set_get(self):
        store = RuntimeStore()
        store.outputs.set("draft_content", {"title": "Quiz"})
        assert store.outputs.get("draft_content") == {"title": "Quiz"}

    def test_outputs_keys_all_clear(self):
        store = RuntimeStore()
        store.outputs.set("a", 1)
        store.outputs.set("b", 2)
        assert set(store.outputs.keys()) == {"a", "b"}
        assert store.outputs.all() == {"a": 1, "b": 2}
        store.outputs.clear()
        assert store.outputs.keys() == []

    def test_outputs_missing_returns_default(self):
        store = RuntimeStore()
        assert store.outputs.get("missing") is None
        assert store.outputs.get("missing", "default") == "default"

    def test_services_property(self):
        store = RuntimeStore()
        store.services.set("coordinator", "svc_obj")
        assert store.services.get("coordinator") == "svc_obj"
        assert store.services.keys() == ["coordinator"]

    def test_stores_are_isolated(self):
        store = RuntimeStore()
        store.outputs.set("key", "output_val")
        store.services.set("key", "service_val")
        store.store("custom").set("key", "custom_val")
        assert store.outputs.get("key") == "output_val"
        assert store.services.get("key") == "service_val"
        assert store.store("custom").get("key") == "custom_val"

    def test_custom_named_store(self):
        store = RuntimeStore()
        custom = store.store("custom")
        custom.set("foo", "bar")
        assert store.store("custom").get("foo") == "bar"


# ---------------------------------------------------------------------------
# 8. Workflow construction (verifies factories return correct types)
# ---------------------------------------------------------------------------


class TestWorkflowConstruction:
    def test_refinement_creates_loop(self):
        from adk_agentic_writer.workflows import create_refinement_pipeline
        from adk_agentic_writer.agents.reviewer import create_reviewer_pipeline
        from adk_agentic_writer.agents.refiner import create_refiner_pipeline
        from adk_agentic_writer.workflows.tools import exit_loop

        reviewer = create_reviewer_pipeline()
        refiner = create_refiner_pipeline(exit_loop)
        pipeline = create_refinement_pipeline(reviewer, refiner)
        assert "RefinementLoop" in pipeline.name
        assert len(pipeline.sub_agents) == 2

    def test_publish_creates_full_pipeline(self):
        from adk_agentic_writer.workflows import create_publish_pipeline
        from adk_agentic_writer.agents.ideator import create_ideator_pipeline
        from adk_agentic_writer.agents.writer import create_writer_pipeline
        from adk_agentic_writer.agents.reviewer import create_reviewer_pipeline
        from adk_agentic_writer.agents.refiner import create_refiner_pipeline
        from adk_agentic_writer.agents.verifier import create_verifier_pipeline
        from adk_agentic_writer.workflows.tools import exit_loop

        ideator = create_ideator_pipeline()
        writer = create_writer_pipeline(GAME_FORMAT)
        reviewer = create_reviewer_pipeline()
        refiner = create_refiner_pipeline(exit_loop)
        verifier = create_verifier_pipeline()
        pipeline = create_publish_pipeline(ideator, writer, reviewer, refiner, verifier)
        assert "PublishPipeline" in pipeline.name
        assert len(pipeline.sub_agents) == 4


# ---------------------------------------------------------------------------
# 9. Agent service registration
# ---------------------------------------------------------------------------


class TestAgentServiceRegistration:
    def test_base_agent_service_tasks(self):
        from adk_agentic_writer.agents.base import BaseAgentService

        svc = BaseAgentService()
        assert svc.get_supported_tasks() == []
        assert svc.handles("write") is False

    def test_writer_service_handles_write(self):
        from adk_agentic_writer.agents.writer import WriterAgentService

        writer = WriterAgentService.__new__(WriterAgentService)
        writer._pipeline_agents = []
        writer._service_agents = []
        writer._runners = {}
        writer._tasks = []
        writer._task_by_id = {}
        from adk_agentic_writer.tasks import WRITE

        writer._register_tasks([WRITE])
        assert writer.handles("write")
        assert not writer.handles("review")

    def test_reviewer_service_handles_review(self):
        from adk_agentic_writer.agents.reviewer import ReviewerAgentService

        reviewer = ReviewerAgentService.__new__(ReviewerAgentService)
        reviewer._pipeline_agents = []
        reviewer._service_agents = []
        reviewer._runners = {}
        reviewer._tasks = []
        reviewer._task_by_id = {}
        from adk_agentic_writer.tasks import REVIEW

        reviewer._register_tasks([REVIEW])
        assert reviewer.handles("review")


# ---------------------------------------------------------------------------
# 10. find_by_task helper
# ---------------------------------------------------------------------------


class TestFindByTask:
    def test_finds_correct_agent(self):
        from adk_agentic_writer.agents.base import BaseAgentService, find_by_task
        from adk_agentic_writer.tasks import WRITE, REVIEW

        writer = BaseAgentService.__new__(BaseAgentService)
        writer._tasks = []
        writer._task_by_id = {}
        writer._register_tasks([WRITE])

        reviewer = BaseAgentService.__new__(BaseAgentService)
        reviewer._tasks = []
        reviewer._task_by_id = {}
        reviewer._register_tasks([REVIEW])

        assert find_by_task([writer, reviewer], "write") is writer
        assert find_by_task([writer, reviewer], "review") is reviewer

    def test_raises_on_missing_task(self):
        from adk_agentic_writer.agents.base import BaseAgentService, find_by_task

        agent = BaseAgentService()
        with pytest.raises(ValueError, match="No agent"):
            find_by_task([agent], "nonexistent")


# ---------------------------------------------------------------------------
# 11. Domain parameter propagation
# ---------------------------------------------------------------------------


class TestDomainPropagation:
    """Verify that prepare_task includes domain in the prompt for all agents."""

    def test_ideator_prepare_task_includes_domain(self):
        from adk_agentic_writer.agents.ideator import IdeatorAgentService
        from adk_agentic_writer.tasks import IDEATE

        svc = IdeatorAgentService.__new__(IdeatorAgentService)
        svc._tasks = []
        svc._task_by_id = {}
        svc._pipeline_agents = []
        svc._service_agents = []
        svc._runners = {}
        svc._register_tasks([IDEATE])
        prompt = svc.prepare_task("ideate", {"prompt": "test", "domain": "fictional"})
        assert "DOMAIN: fictional" in prompt

    def test_ideator_defaults_to_realworld(self):
        from adk_agentic_writer.agents.ideator import IdeatorAgentService
        from adk_agentic_writer.tasks import IDEATE

        svc = IdeatorAgentService.__new__(IdeatorAgentService)
        svc._tasks = []
        svc._task_by_id = {}
        svc._pipeline_agents = []
        svc._service_agents = []
        svc._runners = {}
        svc._register_tasks([IDEATE])
        prompt = svc.prepare_task("ideate", {"prompt": "test"})
        assert "DOMAIN: realworld" in prompt

    def test_writer_prepare_task_includes_domain(self):
        from adk_agentic_writer.agents.writer import WriterAgentService
        from adk_agentic_writer.tasks import WRITE
        from adk_agentic_writer.formats import get_format

        svc = WriterAgentService.__new__(WriterAgentService)
        svc._tasks = []
        svc._task_by_id = {}
        svc._pipeline_agents = []
        svc._service_agents = []
        svc._runners = {}
        svc._pipeline_writers = {}
        svc._writers = {}
        svc._register_tasks([WRITE])
        prompt = svc.prepare_task("write", {"format": "quiz", "topic": "test", "domain": "fictional"})
        assert "DOMAIN: fictional" in prompt

    def test_reviewer_prepare_task_includes_domain(self):
        from adk_agentic_writer.agents.reviewer import ReviewerAgentService
        from adk_agentic_writer.tasks import REVIEW

        svc = ReviewerAgentService.__new__(ReviewerAgentService)
        svc._tasks = []
        svc._task_by_id = {}
        svc._pipeline_agents = []
        svc._service_agents = []
        svc._runners = {}
        svc._register_tasks([REVIEW])
        prompt = svc.prepare_task("review", {
            "draft_content": {"title": "Test"},
            "format": "quiz",
            "domain": "fictional",
        })
        assert "DOMAIN: fictional" in prompt

    def test_verifier_prepare_task_includes_domain(self):
        from adk_agentic_writer.agents.verifier import VerifierAgentService
        from adk_agentic_writer.tasks import VERIFY

        svc = VerifierAgentService.__new__(VerifierAgentService)
        svc._tasks = []
        svc._task_by_id = {}
        svc._pipeline_agents = []
        svc._service_agents = []
        svc._runners = {}
        svc._register_tasks([VERIFY])
        prompt = svc.prepare_task("verify", {
            "draft_content": {"title": "Test"},
            "format": "quiz",
            "domain": "realworld",
        })
        assert "DOMAIN: realworld" in prompt

    def test_refiner_prepare_task_includes_domain(self):
        from adk_agentic_writer.agents.refiner import RefinerAgentService
        from adk_agentic_writer.tasks import REFINE
        from adk_agentic_writer.workflows.tools import exit_loop
        from adk_agentic_writer.agents.reviewer import create_reviewer_pipeline

        reviewer = create_reviewer_pipeline()
        svc = RefinerAgentService.__new__(RefinerAgentService)
        svc._tasks = []
        svc._task_by_id = {}
        svc._pipeline_agents = []
        svc._service_agents = []
        svc._runners = {}
        svc._register_tasks([REFINE])
        prompt = svc.prepare_task("refine", {
            "draft_content": {"title": "Test"},
            "review_result": {"score": 70},
            "verification_result": {},
            "format": "quiz",
            "domain": "fictional",
        })
        assert "DOMAIN: fictional" in prompt

    def test_writer_instruction_contains_domain_block(self):
        from adk_agentic_writer.agents.writer import _build_instruction
        from adk_agentic_writer.formats import get_format

        fmt = get_format("quiz")
        instruction = _build_instruction(fmt)
        assert "DOMAIN AWARENESS" in instruction
        assert "Google Search" in instruction

    def test_verifier_instruction_contains_domain_match(self):
        from adk_agentic_writer.agents.verifier import _INSTRUCTION_BASE

        assert "DOMAIN MATCH CHECK" in _INSTRUCTION_BASE
        assert "realworld" in _INSTRUCTION_BASE
        assert "fictional" in _INSTRUCTION_BASE
