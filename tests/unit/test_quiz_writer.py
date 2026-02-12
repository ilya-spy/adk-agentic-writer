"""Tests for quiz writer agent and ContentProtocol."""

import pytest

from adk_agentic_writer.agents import StaticQuizWriterAgent
from adk_agentic_writer.models.agent_models import AgentStatus
from adk_agentic_writer.models.content_models import ContentBlockType, ContentPattern


@pytest.mark.asyncio
async def test_quiz_writer_initialization() -> None:
    """Test quiz writer agent initialization."""
    agent = StaticQuizWriterAgent()

    assert agent.agent_id == "quiz_writer"
    assert agent.state.status == AgentStatus.IDLE


@pytest.mark.asyncio
async def test_generate_text() -> None:
    """Test generate_text method (ContentProtocol)."""
    agent = StaticQuizWriterAgent()

    text = await agent.generate_text("quiz_question", {"topic": "Python"})

    assert isinstance(text, str)
    assert len(text) > 0


@pytest.mark.asyncio
async def test_generate_block() -> None:
    """Test generate_block method (ContentProtocol)."""
    agent = StaticQuizWriterAgent()

    block = await agent.generate_block(
        ContentBlockType.QUESTION,
        {"topic": "Python", "difficulty": "medium"},
    )

    assert block.block_id is not None
    assert block.block_type == ContentBlockType.QUESTION
    assert "question" in block.content


@pytest.mark.asyncio
async def test_generate_patterned_blocks_sequential() -> None:
    """Test generate_patterned_blocks with sequential pattern."""
    agent = StaticQuizWriterAgent()

    blocks = await agent.generate_patterned_blocks(
        ContentBlockType.QUESTION,
        ContentPattern.SEQUENTIAL,
        {"topic": "Math", "count": 3},
    )

    assert len(blocks) == 3
    # Sequential: each block links to next (except last)
    assert blocks[0].navigation == {"next": "question_1"}
    assert blocks[1].navigation == {"next": "question_2"}
    assert blocks[2].navigation is None or blocks[2].navigation == {}


@pytest.mark.asyncio
async def test_generate_patterned_blocks_looped() -> None:
    """Test generate_patterned_blocks with looped pattern."""
    agent = StaticQuizWriterAgent()

    blocks = await agent.generate_patterned_blocks(
        ContentBlockType.QUESTION,
        ContentPattern.LOOPED,
        {"topic": "Science", "count": 3},
    )

    assert len(blocks) == 3
    # Looped: last block links back to first
    assert blocks[2].navigation == {"next": "question_0"}
    assert blocks[0].exit_condition is not None


@pytest.mark.asyncio
async def test_generate_patterned_blocks_branched() -> None:
    """Test generate_patterned_blocks with branched pattern."""
    agent = StaticQuizWriterAgent()

    blocks = await agent.generate_patterned_blocks(
        ContentBlockType.QUESTION,
        ContentPattern.BRANCHED,
        {"topic": "History", "count": 3},
    )

    assert len(blocks) == 3
    # Branched: each block has choices to other blocks
    assert blocks[0].choices is not None
    assert len(blocks[0].choices) == 2  # Can go to 2 other blocks


@pytest.mark.asyncio
async def test_generate_question_directly() -> None:
    """Test generate_question universal block generator."""
    agent = StaticQuizWriterAgent()

    question = await agent.generate_question(
        topic="Python",
        difficulty="hard",
    )

    assert question.question is not None
    assert len(question.options) == 4
    assert 0 <= question.correct_answer <= 3
    assert question.tier == "hard"


# Task-based API tests
@pytest.mark.asyncio
async def test_agent_publishes_supported_tasks() -> None:
    """Test that agent publishes its supported tasks."""
    agent = StaticQuizWriterAgent()

    tasks = agent.get_supported_tasks()

    assert len(tasks) >= 2
    task_ids = [t.task_id for t in tasks]
    assert "generate_quiz" in task_ids
    assert "generate_story" in task_ids


@pytest.mark.asyncio
async def test_agent_supports_task() -> None:
    """Test supports_task helper method."""
    agent = StaticQuizWriterAgent()

    assert agent.supports_task("generate_quiz") is True
    assert agent.supports_task("generate_story") is True
    assert agent.supports_task("generate_simulation") is False


@pytest.mark.asyncio
async def test_get_task_by_id() -> None:
    """Test getting task template by ID."""
    agent = StaticQuizWriterAgent()

    task = agent.get_task_by_id("generate_quiz")

    assert task is not None
    assert task.task_id == "generate_quiz"
    assert "topic" in task.prompt


@pytest.mark.asyncio
async def test_coordinator_get_supported_tasks() -> None:
    """Test coordinator returns supported tasks from templates."""
    from adk_agentic_writer.agents.static import CoordinatorAgent

    coordinator = CoordinatorAgent()
    tasks = coordinator.get_supported_tasks()

    assert len(tasks) > 0
    task_ids = [t.task_id for t in tasks]
    assert "generate_quiz" in task_ids
    assert "generate_game" in task_ids


@pytest.mark.asyncio
async def test_coordinator_process_task() -> None:
    """Test processing task via coordinator."""
    from adk_agentic_writer.agents.static import CoordinatorAgent
    from adk_agentic_writer.models.agent_models import AgentTask

    coordinator = CoordinatorAgent()

    # Get task template from coordinator
    template = coordinator.get_task_by_id("generate_quiz")
    assert template is not None

    task = AgentTask(
        task_id=template.task_id,
        agent_role=template.agent_role,
        prompt=template.prompt,
        parameters={**template.parameters, "topic": "Python", "num_questions": 3},
        output_key=template.output_key,
    )

    result = await coordinator.process_task(task, task.parameters)

    assert result["status"] == "completed"
    assert "content" in result
    assert "questions" in result["content"]
