"""Content workflow patterns and predefined instances.

These workflows implement patterns for generating structured content blocks
that represent user experience and interaction patterns (scenes, cards, chapters, etc.).
They correspond to the ContentProtocol.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from ..models.agent_models import AgentConfig, WorkflowPattern, WorkflowScope
from .base_workflow import Workflow
from ..tasks import content_tasks

logger = logging.getLogger(__name__)


class AdaptiveContentWorkflow(Workflow):
    """
    Adaptive content workflow - adapts generation mechanics based on previously generated content.

    Pattern: Analyze Behavior → Adapt Strategy → Generate Block → Repeat
    Content adapts to user preferences, skill level, or engagement patterns.

    Example: Adaptive learning paths, personalized story branches, difficulty scaling.
    """

    def __init__(
        self,
        name: str,
        generator: AgentConfig,
        adaptator: AgentConfig,
        max_iterations: int = 10,
    ):
        """
        Initialize adaptive content workflow.

        Args:
            name: Workflow name
            generator: Agent that generates content blocks
            adaptator: Agent that analyzes behavior and adapts strategy
            max_iterations: Maximum number of adaptation iterations
        """
        super().__init__(
            name=name,
            pattern=WorkflowPattern.LOOP,
            scope=WorkflowScope.CONTENT,
            description="Adapt content generation based on user behavior",
            agents=[generator, adaptator],
            max_iterations=max_iterations,
            tasks=[
                content_tasks.ANALYZE_USER_BEHAVIOR,
                content_tasks.ADAPT_CONTENT_STRATEGY,
                content_tasks.GENERATE_ADAPTIVE_BLOCK,
            ],
        )


class StreamingContentWorkflow(Workflow):
    """
    Streaming content workflow - generates content blocks in real-time stream.

    Pattern: Generate Block 1 → Stream → Generate Block 2 → Stream → ...
    Blocks are generated and delivered progressively for immediate user experience.

    Example: Real-time story generation, progressive quiz delivery, streaming tutorials.
    """

    def __init__(
        self,
        name: str,
        generator: AgentConfig,
        streamer: AgentConfig,
        buffer_size: int = 3,
    ):
        """
        Initialize streaming content workflow.

        Args:
            name: Workflow name
            generator: Content generator implementing ContentProtocol
            streamer: Agent that handles streaming blocks to user
            buffer_size: Number of blocks to buffer ahead
        """
        super().__init__(
            name=name,
            pattern=WorkflowPattern.LOOP,
            scope=WorkflowScope.CONTENT,
            description="Generate and stream content blocks progressively",
            agents=[generator, streamer],
            tasks=[
                content_tasks.GENERATE_STREAMING_BLOCK,
                content_tasks.STREAM_CONTENT_BLOCK,
            ],
        )
        self.buffer_size = buffer_size
        logger.info(
            f"Streaming content workflow '{name}' configured with buffer size {buffer_size}"
        )
