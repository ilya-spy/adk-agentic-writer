"""Models package initialization."""

from .agent_models import (
    AGENT_TEAM_CONFIGS,
    AgentConfig,
    AgentMessage,
    AgentModel,
    AgentRole,
    AgentState,
    AgentStatus,
    AgentTask,
    AgentToolModel,
    FunctionToolModel,
    LoopAgentModel,
    ParallelAgentModel,
    SequentialAgentModel,
)
from .content_models import (
    BranchedNarrative,
    ContentRequest,
    ContentResponse,
    ContentType,
    QuestGame,
    Quiz,
    WebSimulation,
)
from .editorial_models import (
    ContentRevision,
    EditorialAction,
    EditorialRequest,
    EditorialResponse,
    EditorialWorkflow,
    Feedback,
    FeedbackType,
    QualityMetrics,
    RefinementContext,
    ValidationResult,
)

__all__ = [
    # Agent models
    "AgentMessage",
    "AgentRole",
    "AgentState",
    "AgentStatus",
    "AgentTask",
    "AgentConfig",
    "AGENT_TEAM_CONFIGS",
    # Base agent models (matching Google GenAI API)
    "AgentModel",
    "SequentialAgentModel",
    "ParallelAgentModel",
    "LoopAgentModel",
    "AgentToolModel",
    "FunctionToolModel",
    # Content models
    "BranchedNarrative",
    "ContentRequest",
    "ContentResponse",
    "ContentType",
    "QuestGame",
    "Quiz",
    "WebSimulation",
    # Editorial models
    "ContentRevision",
    "EditorialAction",
    "EditorialRequest",
    "EditorialResponse",
    "EditorialWorkflow",
    "Feedback",
    "FeedbackType",
    "QualityMetrics",
    "RefinementContext",
    "ValidationResult",
]
