"""Agent-related models.

Includes base Agent models matching Google GenAI API Agent class structure.
Reference: day-1b-agent-architectures notebook
"""

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


class AgentConfig(BaseModel):
    """Configuration for an agent specialist."""

    role: AgentRole = Field(..., description="Agent role")
    system_instruction: str = Field(..., description="System instruction for the agent")
    temperature: float = Field(0.7, description="Generation temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    required_parameters: List[str] = Field(
        default_factory=list, description="Required parameters for this agent"
    )
    optional_parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Optional parameters with defaults"
    )
    capabilities: List[str] = Field(
        default_factory=list, description="Agent capabilities"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


# Team specialist definitions - our agent models
AGENT_TEAM_CONFIGS: Dict[AgentRole, AgentConfig] = {
    AgentRole.QUIZ_WRITER: AgentConfig(
        role=AgentRole.QUIZ_WRITER,
        system_instruction="""You are an expert educational content creator specializing in interactive quizzes.
Your role is to create engaging, accurate, and pedagogically sound quiz questions.

Guidelines:
- Create clear, unambiguous questions
- Provide 4 answer options with only one correct answer
- Include detailed explanations for correct answers
- Adjust difficulty appropriately
- Make questions relevant and practical
- Avoid trick questions or ambiguous wording""",
        temperature=0.7,
        required_parameters=["topic"],
        optional_parameters={
            "num_questions": 5,
            "difficulty": "medium",
            "passing_score": 70,
        },
        capabilities=["quiz_generation", "educational_content", "question_design"],
    ),
    AgentRole.STORY_WRITER: AgentConfig(
        role=AgentRole.STORY_WRITER,
        system_instruction="""You are a creative storytelling expert specializing in branched narratives.
Your role is to craft engaging, immersive stories with meaningful choices.

Guidelines:
- Create compelling narratives with clear story arcs
- Design meaningful choices that impact the story
- Develop interesting characters and settings
- Ensure narrative coherence across branches
- Balance story depth with interactivity
- Create satisfying endings for different paths""",
        temperature=0.8,
        required_parameters=["topic", "genre"],
        optional_parameters={"num_branches": 3, "story_length": "medium"},
        capabilities=["narrative_design", "branching_stories", "character_development"],
    ),
    AgentRole.GAME_DESIGNER: AgentConfig(
        role=AgentRole.GAME_DESIGNER,
        system_instruction="""You are a game design expert specializing in quest-based interactive experiences.
Your role is to create engaging quest games with clear objectives and rewarding progression.

Guidelines:
- Design clear objectives and victory conditions
- Create meaningful choices and consequences
- Balance challenge and reward
- Ensure logical quest progression
- Design interesting items and rewards
- Make the game engaging and fun""",
        temperature=0.75,
        required_parameters=["topic", "theme"],
        optional_parameters={"difficulty": "medium", "num_quests": 5},
        capabilities=["game_design", "quest_creation", "progression_systems"],
    ),
    AgentRole.SIMULATION_DESIGNER: AgentConfig(
        role=AgentRole.SIMULATION_DESIGNER,
        system_instruction="""You are a simulation design expert specializing in interactive web simulations.
Your role is to create educational and engaging simulations with realistic models.

Guidelines:
- Design accurate simulation models
- Create intuitive user controls
- Ensure realistic variable interactions
- Make simulations educational and engaging
- Provide clear visualization options
- Balance complexity with usability""",
        temperature=0.6,
        required_parameters=["topic", "simulation_type"],
        optional_parameters={"complexity": "medium", "num_variables": 5},
        capabilities=["simulation_design", "modeling", "interactive_visualization"],
    ),
    AgentRole.REVIEWER: AgentConfig(
        role=AgentRole.REVIEWER,
        system_instruction="""You are a quality assurance expert specializing in content review and improvement.
Your role is to review content for quality, accuracy, and engagement.

Guidelines:
- Check for accuracy and correctness
- Ensure content is engaging and well-structured
- Verify pedagogical soundness
- Identify areas for improvement
- Maintain consistency and coherence
- Provide constructive feedback""",
        temperature=0.5,
        required_parameters=["content", "content_type"],
        optional_parameters={"review_depth": "thorough"},
        capabilities=["content_review", "quality_assurance", "improvement_suggestions"],
    ),
    AgentRole.COORDINATOR: AgentConfig(
        role=AgentRole.COORDINATOR,
        system_instruction="""You are a workflow orchestration expert managing multiple AI agents.
Your role is to coordinate agents efficiently to produce high-quality interactive content.

Guidelines:
- Choose appropriate workflow patterns (sequential, parallel, loop)
- Optimize agent collaboration
- Ensure quality through review cycles
- Handle errors gracefully
- Maximize efficiency and output quality""",
        temperature=0.4,
        required_parameters=["task_description", "content_type"],
        optional_parameters={"workflow_pattern": "sequential"},
        capabilities=["workflow_orchestration", "agent_coordination", "task_planning"],
    ),
}


# ============================================================================
# Base Agent Models (matching Google GenAI API)
# ============================================================================


class WorkflowMetadata(BaseModel):
    """Metadata describing a workflow that an agent can use."""

    name: str = Field(..., description="Workflow name")
    pattern: WorkflowPattern = Field(..., description="Workflow orchestration pattern")
    scope: WorkflowScope = Field(..., description="Workflow application scope")
    description: str = Field(..., description="Description of what this workflow does")
    agent_refs: List[str] = Field(
        default_factory=list, description="References to other agents used in workflow"
    )
    max_iterations: Optional[int] = Field(
        None, description="Max iterations for loop workflows"
    )
    merge_strategy: Optional[str] = Field(
        None, description="Merge strategy for parallel workflows"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Workflow-specific parameters"
    )


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
    workflows: List[WorkflowMetadata] = Field(
        default_factory=list, description="Available workflows for this agent"
    )


class SequentialAgentModel(BaseModel):
    """
    Sequential Agent model matching Google ADK SequentialAgent.

    Corresponds to google.adk.agents.SequentialAgent:
    ```python
    SequentialAgent(name="Pipeline", sub_agents=[agent1, agent2, agent3])
    ```
    """

    name: str = Field(..., description="Sequential agent pipeline name")
    sub_agents: List[str] = Field(
        ..., description="List of sub-agent names to execute in order"
    )


class ParallelAgentModel(BaseModel):
    """
    Parallel Agent model matching Google ADK ParallelAgent.

    Corresponds to google.adk.agents.ParallelAgent:
    ```python
    ParallelAgent(name="ParallelTeam", sub_agents=[agent1, agent2, agent3])
    ```
    """

    name: str = Field(..., description="Parallel agent team name")
    sub_agents: List[str] = Field(
        ..., description="List of sub-agent names to execute concurrently"
    )
    merge_strategy: str = Field(
        "combine", description="How to merge results: combine, first, vote"
    )


class LoopAgentModel(BaseModel):
    """
    Loop Agent model matching Google ADK LoopAgent.

    Corresponds to google.adk.agents.LoopAgent:
    ```python
    LoopAgent(name="RefinementLoop", sub_agents=[critic, refiner], max_iterations=3)
    ```
    """

    name: str = Field(..., description="Loop agent name")
    sub_agents: List[str] = Field(
        ..., description="List of sub-agent names to execute in loop"
    )
    max_iterations: int = Field(10, description="Maximum number of loop iterations")


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
    """Task assigned to an agent."""

    task_id: str = Field(..., description="Unique task identifier")
    agent_role: AgentRole = Field(..., description="Agent role for this task")
    description: str = Field(..., description="Task description")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Task parameters"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="IDs of prerequisite tasks"
    )
    status: AgentStatus = Field(AgentStatus.IDLE, description="Current task status")


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
