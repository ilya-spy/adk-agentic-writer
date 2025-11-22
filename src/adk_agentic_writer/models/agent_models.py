"""Agent-related models."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Roles that agents can play in the system."""

    COORDINATOR = "coordinator"
    QUIZ_WRITER = "quiz_writer"
    STORY_WRITER = "story_writer"
    GAME_DESIGNER = "game_designer"
    SIMULATION_DESIGNER = "simulation_designer"
    EDITOR = "editor"
    REVIEWER = "reviewer"


class AgentStatus(str, Enum):
    """Current status of an agent."""

    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


class AgentMessage(BaseModel):
    """Message sent between agents."""

    sender: str = Field(..., description="Sending agent ID")
    receiver: str = Field(..., description="Receiving agent ID")
    content: str = Field(..., description="Message content")
    message_type: str = Field("task", description="Type: task, response, feedback")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional data")


class AgentTask(BaseModel):
    """Task assigned to an agent."""

    task_id: str = Field(..., description="Unique task identifier")
    agent_role: AgentRole = Field(..., description="Agent role for this task")
    description: str = Field(..., description="Task description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    dependencies: List[str] = Field(default_factory=list, description="IDs of prerequisite tasks")
    status: AgentStatus = Field(AgentStatus.IDLE, description="Current task status")


class AgentState(BaseModel):
    """Current state of an agent."""

    agent_id: str = Field(..., description="Agent identifier")
    role: AgentRole = Field(..., description="Agent role")
    status: AgentStatus = Field(AgentStatus.IDLE, description="Current status")
    current_task: Optional[str] = Field(None, description="Current task ID")
    completed_tasks: List[str] = Field(default_factory=list, description="Completed task IDs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
