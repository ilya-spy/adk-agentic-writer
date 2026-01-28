"""Protocol defining the interface for adaptive content generation.

This module provides:
- ContentBlockType: Types of content blocks
- ContentPattern: User interaction patterns
- ContentBlock: A single content block with metadata
- AdaptiveContentProtocol: Interface for adaptive content generation
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol


class ContentBlockType(str, Enum):
    """Types of content blocks that can be generated."""

    SCENE = "scene"
    CARD = "card"
    CHAPTER = "chapter"
    SECTION = "section"
    SLIDE = "slide"
    QUESTION = "question"
    NODE = "node"
    CUSTOM = "custom"


class ContentPattern(str, Enum):
    """User interaction patterns for content structure.

    These patterns define how users navigate and consume content.
    """

    SEQUENTIAL = "sequential"  # Linear progression: A → B → C
    LOOPED = "looped"  # Repeatable with exit: A ⟲ (until condition) → B
    BRANCHED = "branched"  # Choice-based: A → [B|C|D]
    CONDITIONAL = "conditional"  # State-based: Show A if condition met
    PARALLEL = "parallel"  # Independent sections accessible in any order


class ContentBlock:
    """Represents a single block of content with navigation/interaction metadata.

    Content blocks define both the content and how users interact with it.
    """

    def __init__(
        self,
        block_id: str,
        block_type: ContentBlockType,
        content: Dict[str, Any],
        pattern: ContentPattern = ContentPattern.SEQUENTIAL,
        navigation: Optional[Dict[str, Any]] = None,
        exit_condition: Optional[Dict[str, Any]] = None,
        choices: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a content block.

        Args:
            block_id: Unique identifier for this block
            block_type: Type of content block
            content: The actual content data
            pattern: User interaction pattern for this block
            navigation: Navigation controls (next_block, prev_block, etc.)
            exit_condition: Condition to exit loop (for looped patterns)
            choices: Available choices (for branched patterns)
            metadata: Optional metadata about the block
        """
        self.block_id = block_id
        self.block_type = block_type
        self.content = content
        self.pattern = pattern
        self.navigation = navigation or {}
        self.exit_condition = exit_condition
        self.choices = choices or []
        self.metadata = metadata or {}


class AdaptiveContentProtocol(Protocol):
    """Protocol for adaptive content generation interface.

    Implemented by ProducerAgent for strategy-based content generation.
    """

    async def analyze_user_behavior(
        self, user_interactions: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Analyze user behavior and generate analysis.

        Args:
            user_interactions: User interactions data
            **kwargs: Additional parameters

        Returns:
            Dict with Analysis of user behavior
        """
        ...

    async def adapt_content_strategy(
        self, behavior_analysis: Dict[str, Any], topic: str, **kwargs
    ) -> Dict[str, Any]:
        """Adapt content generation strategy based on analysis.

        Args:
            behavior_analysis: Analysis of user behavior or content quality
            topic: Content topic
            **kwargs: Additional parameters

        Returns:
            Updated strategy dict
        """
        ...

    async def generate_adaptive_blocks(
        self, block_type: str, topic: str, num_blocks: int = 3, **kwargs
    ) -> Dict[str, Any]:
        """Generate blocks using adaptive strategy.

        Args:
            block_type: Type of content block
            topic: Content topic
            num_blocks: Number of blocks to generate
            **kwargs: Additional parameters

        Returns:
            Generated adaptive blocks
        """
        ...

    async def generate_variant_blocks(
        self, content_type: str, topic: str, num_variants: int = 3, **kwargs
    ) -> Dict[str, Any]:
        """Generate content variants in parallel and merge.

        Args:
            content_type: Type of content to generate
            topic: Content topic
            num_variants: Number of variants to generate
            **kwargs: Additional parameters

        Returns:
            Merged variant results
        """
        ...

    def get_strategy(self) -> Dict[str, Any]:
        """Get current strategy state.

        Returns:
            Current strategy dict
        """
        ...

    def update_strategy(self, updates: Dict[str, Any]) -> None:
        """Update strategy state.

        Args:
            updates: Strategy updates to apply
        """
        ...
