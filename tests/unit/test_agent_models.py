"""Tests for agent models."""

from adk_agentic_writer.models.agent_models import (
    AgentMessage,
    AgentRole,
    AgentState,
    AgentStatus,
    AgentTask,
)


def test_agent_state_creation() -> None:
    """Test creating an agent state."""
    state = AgentState(
        agent_id="test_agent",
        role=AgentRole.COORDINATOR,
        status=AgentStatus.IDLE,
    )
    
    assert state.agent_id == "test_agent"
    assert state.role == AgentRole.COORDINATOR
    assert state.status == AgentStatus.IDLE
    assert state.current_task is None
    assert len(state.completed_tasks) == 0


def test_agent_task_creation() -> None:
    """Test creating an agent task."""
    task = AgentTask(
        task_id="task_1",
        agent_role=AgentRole.QUIZ_WRITER,
        description="Create a quiz about Python",
        parameters={"num_questions": 5},
    )
    
    assert task.task_id == "task_1"
    assert task.agent_role == AgentRole.QUIZ_WRITER
    assert task.description == "Create a quiz about Python"
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
