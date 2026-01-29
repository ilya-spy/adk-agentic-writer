"""Protocols for content generation patterns."""

from typing import Any, Dict, List, Optional, Protocol

from ..models.content_models import ContentBlock, ContentBlockType


class ContentProtocol(Protocol):
    """Protocol for generating structured content blocks."""

    async def generate_block(
        self,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        previous_blocks: Optional[List[ContentBlock]] = None,
    ) -> ContentBlock:
        """Generate a single content block."""
        ...

    async def generate_sequential_blocks(
        self,
        num_blocks: int,
        block_type: ContentBlockType,
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate sequential blocks (linear navigation)."""
        ...

    async def generate_looped_blocks(
        self,
        num_blocks: int,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        exit_condition: Dict[str, Any],
        allow_back: bool = True,
    ) -> List[ContentBlock]:
        """Generate looped blocks (repeat until exit condition)."""
        ...

    async def generate_branched_blocks(
        self,
        branch_points: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate branched blocks (choice-based navigation)."""
        ...

    async def generate_conditional_blocks(
        self,
        blocks_config: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate conditional blocks (state-based display)."""
        ...


class AdaptiveContentProtocol(Protocol):
    """Protocol for adaptive content generation."""

    async def analyze_user_behavior(
        self, user_interactions: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Analyze user behavior."""
        ...

    async def adapt_content_strategy(
        self, behavior_analysis: Dict[str, Any], topic: str, **kwargs
    ) -> Dict[str, Any]:
        """Adapt strategy based on analysis."""
        ...

    async def generate_adaptive_blocks(
        self, block_type: str, topic: str, num_blocks: int = 3, **kwargs
    ) -> Dict[str, Any]:
        """Generate blocks using adaptive strategy."""
        ...

    async def generate_variant_blocks(
        self, content_type: str, topic: str, num_variants: int = 3, **kwargs
    ) -> Dict[str, Any]:
        """Generate content variants and merge."""
        ...

    def get_strategy(self) -> Dict[str, Any]:
        """Get current strategy state."""
        ...

    def update_strategy(self, updates: Dict[str, Any]) -> None:
        """Update strategy state."""
        ...


__all__ = ["ContentProtocol", "AdaptiveContentProtocol"]
