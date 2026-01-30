"""Protocols for content generation patterns."""

from typing import Any, Dict, List, Optional, Protocol

from ..models.content_models import ContentBlock, ContentBlockType, ContentPattern


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

    async def generate_patterned_blocks(
        self,
        block_type: ContentBlockType,
        pattern: ContentPattern,
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate content blocks based on a pattern."""
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
