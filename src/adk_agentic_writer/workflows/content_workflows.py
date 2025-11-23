"""Content workflow patterns and predefined instances.

These workflows implement patterns for generating structured content blocks
that represent user experience and interaction patterns (scenes, cards, chapters, etc.).
They correspond to the ContentProtocol.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from ..models.agent_models import WorkflowPattern, WorkflowScope
from .base_workflow import Workflow

logger = logging.getLogger(__name__)


class SequentialContentWorkflow(Workflow):
    """
    Sequential content workflow - generates content blocks in sequence.

    Pattern: Block 1 → Block 2 → Block 3 → ...
    Each block builds upon previous blocks for coherent narrative/experience.

    Corresponds to ContentProtocol.generate_blocks_sequential().

    Example: Story scenes generated one after another, quiz questions in sequence.
    """

    def __init__(self, name: str, block_types: List[str], generator: Any):
        """
        Initialize sequential content workflow.

        Args:
            name: Workflow name
            block_types: List of content block types to generate in order
            generator: Content generator implementing ContentProtocol
        """
        super().__init__(
            name=name,
            pattern=WorkflowPattern.SEQUENTIAL,
            scope=WorkflowScope.CONTENT,
            description="Generate content blocks in linear sequence for reading",
            agents=[generator],
        )
        self.block_types = block_types
        self.generator = generator
        logger.info(
            f"Sequential content workflow '{name}' configured with {len(block_types)} blocks"
        )


class LoopedContentWorkflow(Workflow):
    """
    Looped content workflow - generates and refines content blocks iteratively.

    Pattern: Generate Block → Validate → Refine → Validate → ... → Done
    Each iteration improves the content block until quality criteria are met.

    Corresponds to ContentProtocol.generate_blocks_looped().

    Example: Refining a story scene through multiple iterations, improving quiz questions.
    """

    def __init__(
        self,
        name: str,
        block_type: str,
        generator: Any,
        validator: Callable[[Any], bool],
        max_iterations: int = 10,
    ):
        """
        Initialize looped content workflow.

        Args:
            name: Workflow name
            block_type: Type of content block to generate
            generator: Content generator implementing ContentProtocol
            validator: Function to validate block quality
            max_iterations: Maximum refinement iterations
        """
        condition_fn = (
            lambda data, iteration: not validator(data) and iteration < max_iterations
        )

        super().__init__(
            name=name,
            pattern=WorkflowPattern.LOOP,
            scope=WorkflowScope.CONTENT,
            description="Generate content blocks that user can repeat until exit",
            agents=[generator],
            condition=condition_fn,
            max_iterations=max_iterations,
        )
        self.block_type = block_type
        self.validator = validator
        logger.info(
            f"Looped content workflow '{name}' configured for {block_type} with max {max_iterations} iterations"
        )


class ConditionalContentWorkflow(Workflow):
    """
    Conditional content workflow - generates content blocks based on conditions.

    Pattern: Condition → [Block Type A | Block Type B | Block Type C]
    Blocks are generated based on runtime conditions, enabling branching narratives.

    Corresponds to ContentProtocol.generate_blocks_conditional().

    Example: Branching story paths, adaptive quiz questions, conditional game states.
    """

    def __init__(
        self,
        name: str,
        condition_fn: Callable[[Dict[str, Any]], str],
        generators: Dict[str, Any],
    ):
        """
        Initialize conditional content workflow.

        Args:
            name: Workflow name
            condition_fn: Function that determines which block type to generate
            generators: Dict mapping block types to generators
        """
        super().__init__(
            name=name,
            pattern=WorkflowPattern.CONDITIONAL,
            scope=WorkflowScope.CONTENT,
            description="Generate content blocks based on user state/conditions",
            agents=generators,
            condition=condition_fn,
        )
        logger.info(
            f"Conditional content workflow '{name}' configured with {len(generators)} branches"
        )


class InteractiveContentWorkflow(Workflow):
    """
    Interactive content workflow - generates content with user interaction points.

    Pattern: Block → User Choice → Block → User Choice → ...
    Content adapts based on user interactions and choices.

    Example: Interactive stories, choose-your-own-adventure, branching tutorials.
    """

    def __init__(
        self,
        name: str,
        generator: Any,
        interaction_handler: Callable[[Dict[str, Any]], Dict[str, Any]],
        max_interactions: int = 20,
    ):
        """
        Initialize interactive content workflow.

        Args:
            name: Workflow name
            generator: Content generator implementing ContentProtocol
            interaction_handler: Function that processes user interactions
            max_interactions: Maximum number of interaction points
        """
        super().__init__(
            name=name,
            pattern=WorkflowPattern.SEQUENTIAL,
            scope=WorkflowScope.CONTENT,
            description="Generate content with user interaction points",
            agents=[generator],
            max_iterations=max_interactions,
        )
        self.generator = generator
        self.interaction_handler = interaction_handler
        self.max_interactions = max_interactions
        logger.info(
            f"Interactive content workflow '{name}' configured with max {max_interactions} interactions"
        )


class AdaptiveContentWorkflow(Workflow):
    """
    Adaptive content workflow - adapts content generation based on user behavior.

    Pattern: Analyze Behavior → Adapt Strategy → Generate Block → Repeat
    Content adapts to user preferences, skill level, or engagement patterns.

    Example: Adaptive learning paths, personalized story branches, difficulty scaling.
    """

    def __init__(
        self,
        name: str,
        behavior_analyzer: Callable[[Dict[str, Any]], str],
        generators: Dict[str, Any],
        default_generator: Any,
    ):
        """
        Initialize adaptive content workflow.

        Args:
            name: Workflow name
            behavior_analyzer: Function that analyzes user behavior
            generators: Dict mapping behavior patterns to generators
            default_generator: Default generator for unknown patterns
        """
        super().__init__(
            name=name,
            pattern=WorkflowPattern.SEQUENTIAL,
            scope=WorkflowScope.CONTENT,
            description="Adapt content generation based on user behavior",
            agents=[default_generator],
        )
        self.behavior_analyzer = behavior_analyzer
        self.generators = generators
        self.default_generator = default_generator
        logger.info(
            f"Adaptive content workflow '{name}' configured with {len(generators)} adaptation strategies"
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
        generator: Any,
        stream_handler: Callable[[Any], None],
        buffer_size: int = 3,
    ):
        """
        Initialize streaming content workflow.

        Args:
            name: Workflow name
            generator: Content generator implementing ContentProtocol
            stream_handler: Function that handles streaming blocks to user
            buffer_size: Number of blocks to buffer ahead
        """
        super().__init__(
            name=name,
            pattern=WorkflowPattern.SEQUENTIAL,
            scope=WorkflowScope.CONTENT,
            description="Generate and stream content blocks progressively",
            agents=[generator],
        )
        self.generator = generator
        self.stream_handler = stream_handler
        self.buffer_size = buffer_size
        logger.info(
            f"Streaming content workflow '{name}' configured with buffer size {buffer_size}"
        )
