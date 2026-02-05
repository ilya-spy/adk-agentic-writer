"""Tests for base agent functionality."""

import pytest

from adk_agentic_writer.agents.base_agent import BaseAgent
from adk_agentic_writer.agents.stateful_agent import StatefulAgent
from adk_agentic_writer.models.agent_models import (
    AgentConfig,
    AgentModel,
    AgentRole,
    AgentStatus,
)


class DummyAgent(StatefulAgent):
    """Test implementation using StatefulAgent."""

    pass


@pytest.mark.asyncio
async def test_base_agent_initialization() -> None:
    """Test base agent initialization."""
    config = AgentConfig(role=AgentRole.COORDINATOR, instruction="Test instruction")
    model = AgentModel(name="test_agent")

    agent = DummyAgent("test_agent", config=config, model=model)

    assert agent.agent_id == "test_agent"
    assert agent.id == "test_agent"
    assert agent.config.role == AgentRole.COORDINATOR
    assert agent.state.status == AgentStatus.IDLE


@pytest.mark.asyncio
async def test_base_agent_status_update() -> None:
    """Test updating agent status."""
    config = AgentConfig(role=AgentRole.COORDINATOR, instruction="Test instruction")
    model = AgentModel(name="test_agent")

    agent = DummyAgent("test_agent", config=config, model=model)

    await agent.update_status(AgentStatus.WORKING)
    assert agent.state.status == AgentStatus.WORKING

    await agent.update_status(AgentStatus.COMPLETED)
    assert agent.state.status == AgentStatus.COMPLETED


@pytest.mark.asyncio
async def test_base_agent_get_state() -> None:
    """Test getting agent state."""
    config = AgentConfig(role=AgentRole.WRITER, instruction="Test instruction")
    model = AgentModel(name="test_agent")

    agent = DummyAgent("test_agent", config=config, model=model)

    assert agent.state.agent_id == "test_agent"
    assert agent.state.status == AgentStatus.IDLE


@pytest.mark.asyncio
async def test_agent_parameters() -> None:
    """Test agent parameters."""
    config = AgentConfig(role=AgentRole.WRITER, instruction="Test")
    model = AgentModel(name="test_agent", parameters={"topic": "Python"})

    agent = DummyAgent("test_agent", config=config, model=model)

    assert agent.get_parameter("topic") == "Python"
    assert agent.get_parameter("missing", "default") == "default"

    agent.update_parameters({"difficulty": "hard"})
    assert agent.get_parameter("difficulty") == "hard"
