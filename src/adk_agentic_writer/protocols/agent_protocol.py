"""Protocol defining the interface for agent operations."""

from typing import Any, Dict, Optional, Protocol, runtime_checkable

from ..models.agent_models import AgentState, AgentStatus


@runtime_checkable
class AgentProtocol(Protocol):
    """Protocol defining the interface for agent operations.

    This protocol defines the core interface that all agents must implement,
    regardless of their specific capabilities or underlying implementation.
    """

    async def process_task(
        self, task_description: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a task assigned to this agent.

        Args:
            task_description: Description of the task to perform
            parameters: Parameters for the task

        Returns:
            Dict containing the task results
        """
        ...

    async def update_status(self, status: AgentStatus) -> None:
        """Update the agent's status.

        Args:
            status: New status for the agent
        """
        ...

    def get_state(self) -> AgentState:
        """Get the current state of the agent.

        Returns:
            Current agent state
        """
        ...

    async def receive_message(
        self, message: str, sender: str, data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Receive a message from another agent or system.

        Args:
            message: Message content
            sender: ID of the sending agent or system
            data: Optional additional data

        Returns:
            Optional response message
        """
        ...
