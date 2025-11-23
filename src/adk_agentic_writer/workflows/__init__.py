"""Workflow system with metadata-driven orchestration.

All workflows inherit from the base Workflow class and use WorkflowMetadata
to specify their pattern (sequential, parallel, loop, conditional) and scope.
"""

# Base workflow class
from .base_workflow import Workflow

# Predefined workflow instances
from .agent_workflows import (
    ConditionalAgentWorkflow,
    LoopAgentWorkflow,
    ParallelAgentWorkflow,
    SequentialAgentWorkflow,
)
from .content_workflows import (
    AdaptiveContentWorkflow,
    ConditionalContentWorkflow,
    InteractiveContentWorkflow,
    LoopedContentWorkflow,
    SequentialContentWorkflow,
    StreamingContentWorkflow,
)
from .editorial_workflows import (
    AdaptiveEditorialWorkflow,
    IterativeEditorialWorkflow,
    ParallelEditorialWorkflow,
    SequentialEditorialWorkflow,
)

__all__ = [
    # Base class
    "Workflow",
    # Agent workflows
    "SequentialAgentWorkflow",
    "ParallelAgentWorkflow",
    "LoopAgentWorkflow",
    "ConditionalAgentWorkflow",
    # Content workflows
    "SequentialContentWorkflow",
    "LoopedContentWorkflow",
    "ConditionalContentWorkflow",
    "InteractiveContentWorkflow",
    "AdaptiveContentWorkflow",
    "StreamingContentWorkflow",
    # Editorial workflows
    "SequentialEditorialWorkflow",
    "ParallelEditorialWorkflow",
    "IterativeEditorialWorkflow",
    "AdaptiveEditorialWorkflow",
]
