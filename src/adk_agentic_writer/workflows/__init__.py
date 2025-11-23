"""Abstract workflow patterns for agent, editorial, and content orchestration.

Workflow implementations are in:
- agents/base/workflows.py (base implementations using Python)
- agents/gemini/workflows.py (Gemini implementations using ADK)
"""

# Base workflow patterns
from .base_workflow import (
    ConditionalWorkflow,
    LoopWorkflow,
    ParallelWorkflow,
    SequentialWorkflow,
    WorkflowPattern,
)

# Agent workflows (for agent orchestration)
from .agent_workflows import (
    ConditionalAgentWorkflow,
    LoopAgentWorkflow,
    ParallelAgentWorkflow,
    SequentialAgentWorkflow,
)

# Editorial workflows (for content editing/refinement - corresponds to EditorialProtocol)
from .editorial_workflows import (
    AdaptiveEditorialWorkflow,
    IterativeEditorialWorkflow,
    ParallelEditorialWorkflow,
    SequentialEditorialWorkflow,
)

# Content workflows (for UX interaction patterns - corresponds to ContentProtocol)
from .content_workflows import (
    AdaptiveContentWorkflow,
    ConditionalContentWorkflow,
    InteractiveContentWorkflow,
    LoopedContentWorkflow,
    SequentialContentWorkflow,
    StreamingContentWorkflow,
)

__all__ = [
    # Base workflow patterns
    "WorkflowPattern",
    "SequentialWorkflow",
    "ParallelWorkflow",
    "LoopWorkflow",
    "ConditionalWorkflow",
    # Agent workflows
    "SequentialAgentWorkflow",
    "ParallelAgentWorkflow",
    "LoopAgentWorkflow",
    "ConditionalAgentWorkflow",
    # Editorial workflows (EditorialProtocol)
    "SequentialEditorialWorkflow",
    "ParallelEditorialWorkflow",
    "IterativeEditorialWorkflow",
    "AdaptiveEditorialWorkflow",
    # Content workflows (ContentProtocol)
    "SequentialContentWorkflow",
    "LoopedContentWorkflow",
    "ConditionalContentWorkflow",
    "InteractiveContentWorkflow",
    "AdaptiveContentWorkflow",
    "StreamingContentWorkflow",
]

