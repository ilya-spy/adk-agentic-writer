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
    max_iterations: Optional[int] = Field(
        None, description="Max iterations for loop workflows"
    )
    merge_strategy: Optional[str] = Field(
        None, description="Merge strategy for parallel workflows"
    )


class TeamMetadata(BaseModel):
    """Metadata describing a team of agents."""

    name: str = Field(..., description="Team name")
    scope: WorkflowScope = Field(..., description="Team application scope")
    agent_ids: List[str] = Field(..., description="List of agent IDs in this team")


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
    teams: List[TeamMetadata] = Field(
        default_factory=list, description="Teams of agents this agent can coordinate"
    )


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
    """

    task_id: str = Field(..., description="Unique task identifier")
    agent_role: AgentRole = Field(..., description="Agent role for this task")
    description: str = Field(..., description="Task description")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Task parameters and input data"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="IDs of prerequisite tasks"
    )
    status: AgentStatus = Field(AgentStatus.IDLE, description="Current task status")

    # Workflow and team hints for orchestration
    suggested_workflow: Optional[str] = Field(
        None, description="Suggested workflow name to use"
    )
    suggested_team: Optional[str] = Field(
        None, description="Suggested team name to use"
    )

    # Output management for stage reuse
    output_key: Optional[str] = Field(
        None, description="Key to store output for later stages"
    )
    input_keys: List[str] = Field(
        default_factory=list, description="Keys of previous outputs to use as input"
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


class WorkflowDecision(BaseModel):
    """Decision about which workflow to use for a task."""

    workflow_name: str = Field(..., description="Selected workflow name")
    team_name: Optional[str] = Field(None, description="Selected team name")
    reason: str = Field(..., description="Reason for this decision")
    confidence: float = Field(..., description="Confidence score (0-1)")


class OrchestrationStrategy(BaseModel):
    """
    Strategy for agent orchestration decisions.

    Helps agents decide which teams and workflows to use based on task characteristics.
    """

    name: str = Field(..., description="Strategy name")

    # Decision criteria
    task_complexity_threshold: float = Field(
        0.5, description="Threshold for considering task complex (0-1)"
    )
    parallel_threshold: int = Field(
        3, description="Min independent subtasks to use parallel workflow"
    )
    iteration_threshold: int = Field(
        2, description="Min expected iterations to use loop workflow"
    )

    # Team selection rules
    scope_to_team: Dict[str, str] = Field(
        default_factory=dict, description="Map workflow scope to team name"
    )
    role_to_team: Dict[str, str] = Field(
        default_factory=dict, description="Map agent role to team name"
    )

    def select_workflow(
        self,
        task: AgentTask,
        available_workflows: List[WorkflowMetadata],
        task_context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowDecision:
        """
        Select appropriate workflow based on task characteristics.

        Args:
            task: The task to execute
            available_workflows: List of available workflows
            task_context: Additional context for decision making

        Returns:
            WorkflowDecision with selected workflow and reasoning
        """
        context = task_context or {}

        # Check for explicit suggestions
        if task.suggested_workflow:
            matching = [
                w for w in available_workflows if w.name == task.suggested_workflow
            ]
            if matching:
                return WorkflowDecision(
                    workflow_name=task.suggested_workflow,
                    team_name=task.suggested_team,
                    reason=f"Task explicitly suggests workflow: {task.suggested_workflow}",
                    confidence=1.0,
                )

        # Analyze task characteristics
        num_subtasks = context.get("num_subtasks", 1)
        expected_iterations = context.get("expected_iterations", 1)
        requires_review = context.get("requires_review", False)

        # Decision logic
        if num_subtasks >= self.parallel_threshold:
            parallel_wf = [
                w for w in available_workflows if w.pattern == WorkflowPattern.PARALLEL
            ]
            if parallel_wf:
                return WorkflowDecision(
                    workflow_name=parallel_wf[0].name,
                    team_name=self._select_team(task, parallel_wf[0].scope),
                    reason=f"Task has {num_subtasks} independent subtasks",
                    confidence=0.8,
                )

        if expected_iterations >= self.iteration_threshold or requires_review:
            loop_wf = [
                w for w in available_workflows if w.pattern == WorkflowPattern.LOOP
            ]
            if loop_wf:
                return WorkflowDecision(
                    workflow_name=loop_wf[0].name,
                    team_name=self._select_team(task, loop_wf[0].scope),
                    reason=f"Task requires {expected_iterations} iterations or review",
                    confidence=0.7,
                )

        # Default to sequential
        seq_wf = [
            w for w in available_workflows if w.pattern == WorkflowPattern.SEQUENTIAL
        ]
        if seq_wf:
            return WorkflowDecision(
                workflow_name=seq_wf[0].name,
                team_name=self._select_team(task, seq_wf[0].scope),
                reason="Default sequential workflow for standard task",
                confidence=0.6,
            )

        # Fallback
        return WorkflowDecision(
            workflow_name=(
                available_workflows[0].name if available_workflows else "default"
            ),
            team_name=None,
            reason="No matching workflow found, using first available",
            confidence=0.3,
        )

    def _select_team(self, task: AgentTask, scope: WorkflowScope) -> Optional[str]:
        """Select team based on task and scope."""
        # Check explicit suggestion
        if task.suggested_team:
            return task.suggested_team

        # Check scope mapping
        if scope.value in self.scope_to_team:
            return self.scope_to_team[scope.value]

        # Check role mapping
        if task.agent_role.value in self.role_to_team:
            return self.role_to_team[task.agent_role.value]

        return None

    def evaluate_condition(self, condition_type: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate a condition for workflow control flow.

        Args:
            condition_type: Type of condition to evaluate
            context: Current execution context

        Returns:
            True if condition is met, False otherwise
        """
        if condition_type == "quality_threshold":
            quality = context.get("quality_score", 0)
            threshold = context.get("threshold", 0.8)
            return quality >= threshold

        elif condition_type == "max_iterations":
            iteration = context.get("iteration", 0)
            max_iter = context.get("max_iterations", 10)
            return iteration < max_iter

        elif condition_type == "task_complete":
            return context.get("status") == "completed"

        elif condition_type == "approval_received":
            return context.get("approved", False)

        return False
