"""Tests for base agent functionality."""

import pytest

from adk_agentic_writer.agents.base_agent import BaseAgent
from adk_agentic_writer.models.agent_models import AgentRole, AgentStatus


class DummyAgent(BaseAgent):
    """Test implementation of BaseAgent."""
    
    async def process_task(self, task_description: str, parameters: dict) -> dict:
        """Simple test implementation."""
        return {"result": "completed", "description": task_description}


@pytest.mark.asyncio
async def test_base_agent_initialization() -> None:
    """Test base agent initialization."""
    agent = DummyAgent("test_agent", AgentRole.COORDINATOR)
    
    assert agent.agent_id == "test_agent"
    assert agent.role == AgentRole.COORDINATOR
    assert agent.state.status == AgentStatus.IDLE


@pytest.mark.asyncio
async def test_base_agent_status_update() -> None:
    """Test updating agent status."""
    agent = DummyAgent("test_agent", AgentRole.COORDINATOR)
    
    await agent.update_status(AgentStatus.WORKING)
    assert agent.state.status == AgentStatus.WORKING
    
    await agent.update_status(AgentStatus.COMPLETED)
    assert agent.state.status == AgentStatus.COMPLETED


@pytest.mark.asyncio
async def test_base_agent_get_state() -> None:
    """Test getting agent state."""
    agent = DummyAgent("test_agent", AgentRole.QUIZ_WRITER)
    
    state = agent.get_state()
    assert state.agent_id == "test_agent"
    assert state.role == AgentRole.QUIZ_WRITER
