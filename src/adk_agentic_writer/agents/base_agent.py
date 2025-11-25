"""Base agent class - single source of truth for all agents.

Both static/ and gemini/ agents inherit from this base class.
"""

import logging
from typing import Any, Dict, Optional

from ..models.agent_models import AgentRole, AgentState, AgentStatus

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all agents (static and gemini).

    Provides core functionality:
    - State management
    - Status updates
    - Message handling

    Implements AgentProtocol interface.

    Subclasses should implement:
    - process_task() - Required by AgentProtocol
    - EditorialProtocol methods (if applicable)
    - ContentProtocol methods (if applicable)
    """

    def __init__(
        self, agent_id: str, role: AgentRole, config: Optional[Dict[str, Any]] = None
    ):
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

    async def update_status(self, status: AgentStatus) -> None:
        """Update the agent's status.

        Implements AgentProtocol.

        Args:
            status: New status for the agent
        """
        self.state.status = status
        logger.debug(f"Agent {self.agent_id} status updated to {status}")

    def get_state(self) -> AgentState:
        """Get the current state of the agent.

        Implements AgentProtocol.

        Returns:
            Current agent state
        """
        return self.state

    async def receive_message(
        self, message: str, sender: str, data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
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


__all__ = ["BaseAgent"]
