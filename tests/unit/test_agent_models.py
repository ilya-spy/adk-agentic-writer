"""Tests for agent models."""

from adk_agentic_writer.models.agent_models import (
    AgentConfig,
    AgentMessage,
    AgentModel,
    AgentRole,
    AgentState,
    AgentStatus,
    AgentTask,
)


def test_agent_state_creation() -> None:
    """Test creating an agent state."""
    state = AgentState(
        agent_id="test_agent",
        status=AgentStatus.IDLE,
    )

    assert state.agent_id == "test_agent"
    assert state.status == AgentStatus.IDLE
    assert state.current_task is None
    assert len(state.completed_tasks) == 0
    assert state.variables == {}


def test_agent_task_creation() -> None:
    """Test creating an agent task."""
    task = AgentTask(
        task_id="task_1",
        agent_role=AgentRole.QUIZ_WRITER,
        prompt="Create a quiz about Python",
        parameters={"num_questions": 5},
    )

    assert task.task_id == "task_1"
    assert task.agent_role == AgentRole.QUIZ_WRITER
    assert task.prompt == "Create a quiz about Python"
    assert task.parameters["num_questions"] == 5
    assert task.status == AgentStatus.IDLE


def test_agent_message_creation() -> None:
    """Test creating an agent message."""
    message = AgentMessage(
        sender="agent_1",
        receiver="agent_2",
        content="Complete the task",
        message_type="task",
        data={"priority": "high"},
    )

    assert message.sender == "agent_1"
    assert message.receiver == "agent_2"
    assert message.content == "Complete the task"
    assert message.message_type == "task"
    assert message.data["priority"] == "high"


def test_agent_config_creation() -> None:
    """Test creating an agent config."""
    config = AgentConfig(
        role=AgentRole.QUIZ_WRITER,
        instruction="You are a quiz writer.",
        temperature=0.7,
    )

    assert config.role == AgentRole.QUIZ_WRITER
    assert config.instruction == "You are a quiz writer."
    assert config.temperature == 0.7


def test_agent_model_creation() -> None:
    """Test creating an agent model."""
    model = AgentModel(
        name="test_agent",
        model_name="gemini-2.5-flash-lite",
        parameters={"topic": "Python"},
    )

    assert model.name == "test_agent"
    assert model.model_name == "gemini-2.5-flash-lite"
    assert model.parameters["topic"] == "Python"
    assert model.workflows == []
    assert model.teams == []
