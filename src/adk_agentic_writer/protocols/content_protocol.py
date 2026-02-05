"""Protocol defining the interface for content generation.

Content data models (ContentBlock, ContentBlockType, ContentPattern) are in models/content_models.py.
This module defines only the protocol interfaces that agents implement.
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ..models.content_models import ContentBlock, ContentBlockType, ContentPattern


@runtime_checkable
class ContentProtocol(Protocol):
    """Protocol for content-generating agents.

    Agents implementing this protocol can:
    - Generate text via text provider
    - Generate structured content blocks
    - Generate patterned blocks with navigation (sequential, looped, branched)
    """

    async def generate_text(
        self,
        prompt_key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate text using the text provider.

        Args:
            prompt_key: Key for prompt template
            context: Context variables for substitution

        Returns:
            Generated text string
        """
        ...

    async def generate_block(
        self,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        previous_blocks: Optional[List[ContentBlock]] = None,
    ) -> ContentBlock:
        """Generate a single content block.

        Args:
            block_type: Type of block to generate
            context: Context information for generation
            previous_blocks: Previously generated blocks for context

        Returns:
            Generated content block
        """
        ...

    async def generate_patterned_blocks(
        self,
        block_type: ContentBlockType,
        pattern: ContentPattern,
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate blocks with navigation based on pattern.

        Patterns:
        - SEQUENTIAL: Linear A → B → C with next/prev navigation
        - LOOPED: Repeatable A ⟲ B ⟲ C with exit conditions
        - BRANCHED: Choice-based A → [B|C|D] with choices
        - CONDITIONAL: State-based visibility
        - PARALLEL: Independent sections

        Args:
            block_type: Type of blocks to generate
            pattern: Navigation pattern to apply
            context: Context with 'count' and pattern-specific params

        Returns:
            List of blocks with navigation metadata
        """
        ...


@runtime_checkable
class AdaptiveContentProtocol(Protocol):
    """Protocol for adaptive content generation.

    Supports behavior analysis, strategy adaptation, and variant generation.
    """

    async def analyze_user_behavior(
        self, user_interactions: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Analyze user behavior and generate analysis.

        Args:
            user_interactions: User interactions data
            **kwargs: Additional parameters

        Returns:
            Analysis of user behavior
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
        """Get current strategy state."""
        ...

    def update_strategy(self, updates: Dict[str, Any]) -> None:
        """Update strategy state."""
        ...
