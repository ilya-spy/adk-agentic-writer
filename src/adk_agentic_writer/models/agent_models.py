"""Agent-related models.

Includes base Agent models matching Google GenAI API Agent class structure.
Reference: day-1b-agent-architectures notebook
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class WorkflowPattern(str, Enum):
    """Workflow orchestration patterns."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    LOOP = "loop"
    CONDITIONAL = "conditional"


class WorkflowScope(str, Enum):
    """Scope of workflow application."""

    AGENT = "agent"  # Agent-level workflow (coordinates between agent tasks)
    CONTENT = "content"  # Content-level workflow (coordinates content generation)
    EDITORIAL = "editorial"  # Editorial-level workflow (coordinates review/editing)


class AgentRole(str, Enum):
    """
    Base agent roles - abstract categories.

    Teams extend this with specific roles in their own files.
    Example: ContentRole(str, Enum) adds STORY_WRITER, QUIZ_WRITER, etc.
    """

    # Base abstract roles (not used directly, extended by teams)
    WRITER = "writer"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    REFINER = "refiner"
    ANALYZER = "analyzer"
    STRATEGIST = "strategist"
    STREAMER = "streamer"

    # Legacy roles (for backward compatibility with existing agents)
    COORDINATOR = "coordinator"
    QUIZ_WRITER = "quiz_writer"
    STORY_WRITER = "story_writer"
    GAME_DESIGNER = "game_designer"
    SIMULATION_DESIGNER = "simulation_designer"


class WorkflowMetadata(BaseModel):
    """Metadata describing a workflow that an agent can use."""

    name: str = Field(..., description="Workflow name")
    pattern: WorkflowPattern = Field(..., description="Workflow orchestration pattern")
    scope: WorkflowScope = Field(..., description="Workflow application scope")
    description: str = Field(..., description="Description of what this workflow does")
    max_iterations: Optional[int] = Field(
        None, description="Max iterations for loop workflows"
    )
    merge_strategy: Optional[str] = Field(
        None, description="Merge strategy for parallel workflows"
    )


class WorkflowDecision(BaseModel):
    """Decision about which workflow to use for a task."""

    scope: Optional[WorkflowScope] = Field(None, description="Selected workflow scope")
    pattern: Optional[WorkflowPattern] = Field(
        None, description="Selected workflow pattern"
    )
    roles: Optional[List[AgentRole]] = Field(None, description="Selected roles")
    reason: str = Field(..., description="Reason for this decision")
    confidence: float = Field(..., description="Confidence score (0-1)")


class TeamMetadata(BaseModel):
    """
    Metadata describing a team of agents.

    Teams can specify required roles and agent pool sizes.
    """

    name: str = Field(..., description="Team name identifier")
    scope: WorkflowScope = Field(..., description="Team application scope")
    description: str = Field(..., description="Team purpose and responsibilities")
    roles: List[str] = Field(
        default_factory=list,
        description="List of role types needed for this team (e.g., ['story_writer', 'story_writer', 'story_writer'])",
    )
    agent_ids: List[str] = Field(
        default_factory=list,
        description="List of agent instance IDs assigned to this team",
    )


class AgentConfig(BaseModel):
    """Configuration for an agent specialist."""

    role: Union[AgentRole, str, Enum] = Field(
        ..., description="Agent role (base or team-specific)"
    )
    system_instruction: str = Field(..., description="System instruction for the agent")
    temperature: float = Field(0.7, description="Generation temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    output_key: Optional[str] = Field(
        None, description="Key to store output in session state"
    )
    workflows: List[WorkflowMetadata] = Field(
        default_factory=list, description="Available workflows for this agent"
    )
    teams: List[TeamMetadata] = Field(
        default_factory=list, description="Teams of agents this agent can coordinate"
    )


# ============================================================================
# Base Agent Models (matching Google GenAI API)
# ============================================================================
class AgentModel(BaseModel):
    """
    Base Agent model matching Google GenAI API Agent structure.

    Corresponds to google.adk.agents.Agent:
    ```python
    Agent(
        name="AgentName",
        model=Gemini(model="gemini-2.5-flash-lite"),
        instruction="System instruction for the agent",
        tools=[...],
        output_key="result_key"
    )
    ```
    """

    name: str = Field(..., description="Agent name identifier")
    model_name: str = Field("gemini-2.5-flash-lite", description="Model to use")
    instruction: str = Field(
        ..., description="System instruction defining agent behavior"
    )
    tools: List[str] = Field(default_factory=list, description="List of tool names")
    output_key: Optional[str] = Field(
        None, description="Key to store output in session state"
    )
    temperature: float = Field(0.7, description="Generation temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")


class AgentToolModel(BaseModel):
    """
    Agent Tool model for wrapping agents as tools.

    Corresponds to google.adk.tools.AgentTool:
    ```python
    AgentTool(sub_agent)
    ```
    """

    agent_name: str = Field(..., description="Name of the agent to wrap as a tool")


class FunctionToolModel(BaseModel):
    """
    Function Tool model for wrapping Python functions as tools.

    Corresponds to google.adk.tools.FunctionTool:
    ```python
    FunctionTool(exit_loop)
    ```
    """

    function_name: str = Field(..., description="Name of the function")
    description: str = Field(..., description="Function description for the agent")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Function parameters schema"
    )


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
    """
    Task assigned to an agent.

    All agents communicate via process_task using AgentTask.
    Higher-level protocols (ContentProtocol, EditorialProtocol) are expressed as tasks
    so agents can decide which teams and workflows to use.

    The prompt can use variable substitution: "Write a story about {topic}"
    Variables are resolved from AgentState.variables at runtime.
    """

    task_id: str = Field(..., description="Unique task identifier")
    status: AgentStatus = Field(AgentStatus.IDLE, description="Current task status")
    agent_role: AgentRole = Field(..., description="Agent role for this task")
    prompt: str = Field(
        ...,
        description="Task prompt with variable substitution support (e.g., 'Write about {topic}')",
    )
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Task parameters and input data"
    )
    dependencies: Optional[List[str]] = Field(
        default_factory=list, description="IDs of prerequisite tasks"
    )

    # Workflow and team hints for orchestration
    suggested_workflow: Optional[WorkflowDecision] = Field(
        None, description="Suggested workflow name to use"
    )
    suggested_team: Optional[TeamMetadata] = Field(
        None, description="Suggested team name to use"
    )

    # Output management for stage reuse
    output_key: Optional[str] = Field(
        None, description="Key to store output in AgentState.variables"
    )


class AgentState(BaseModel):
    """Current state of an agent."""

    agent_id: str = Field(..., description="Agent identifier")
    role: AgentRole = Field(..., description="Agent role")
    status: AgentStatus = Field(AgentStatus.IDLE, description="Current status")
    current_task: Optional[str] = Field(None, description="Current task ID")
    completed_tasks: List[str] = Field(
        default_factory=list, description="Completed task IDs"
    )
    variables: Dict[str, Any] = Field(
        default_factory=dict, description="Runtime variable storage between stages"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
