"""Base agent class for all agents in the system."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..models.agent_models import AgentRole, AgentState, AgentStatus

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents in the multi-agentic system."""

    def __init__(self, agent_id: str, role: AgentRole, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.

        Args:
            agent_id: Unique identifier for this agent
            role: Role this agent plays
            config: Optional configuration dictionary
        """
        self.agent_id = agent_id
        self.role = role
        self.config = config or {}
        self.state = AgentState(
            agent_id=agent_id,
            role=role,
            status=AgentStatus.IDLE,
        )
        logger.info(f"Initialized agent {agent_id} with role {role}")

    @abstractmethod
    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task assigned to this agent.

        Args:
            task_description: Description of the task to perform
            parameters: Parameters for the task

        Returns:
            Dict containing the task results
        """
        pass

    async def update_status(self, status: AgentStatus) -> None:
        """Update the agent's status."""
        self.state.status = status
        logger.debug(f"Agent {self.agent_id} status updated to {status}")

    def get_state(self) -> AgentState:
        """Get the current state of the agent."""
        return self.state

    async def receive_message(self, message: str, sender: str, data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Receive a message from another agent.

        Args:
            message: Message content
            sender: ID of the sending agent
            data: Optional additional data

        Returns:
            Optional response message
        """
        logger.info(f"Agent {self.agent_id} received message from {sender}: {message}")
        return None
