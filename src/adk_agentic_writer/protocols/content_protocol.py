"""Protocol defining the interface for content block generation.

This protocol represents blocks of generated content corresponding to patterns.
For example, a story_writer can implement ContentProtocol to yield sequential,
looped, or conditional sets of scenes/cards.
"""

from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Protocol, runtime_checkable


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


class ContentBlock:
    """Represents a single block of generated content.

    A content block is a discrete unit of content that can be:
    - Generated sequentially (one after another)
    - Generated in a loop (iterative refinement)
    - Generated conditionally (based on previous blocks)
    """

    def __init__(
        self,
        block_id: str,
        block_type: ContentBlockType,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a content block.

        Args:
            block_id: Unique identifier for this block
            block_type: Type of content block
            content: The actual content data
            metadata: Optional metadata about the block
        """
        self.block_id = block_id
        self.block_type = block_type
        self.content = content
        self.metadata = metadata or {}


@runtime_checkable
class ContentProtocol(Protocol):
    """Protocol defining the interface for content block generation.

    Agents implementing this protocol can generate structured content as
    a series of blocks, supporting various generation patterns:
    - Sequential: Generate blocks one after another
    - Looped: Generate and refine blocks iteratively
    - Conditional: Generate blocks based on conditions or previous blocks
    """

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

    async def generate_blocks_sequential(
        self,
        block_types: List[ContentBlockType],
        context: Dict[str, Any],
    ) -> AsyncIterator[ContentBlock]:
        """Generate content blocks sequentially.

        Each block is generated one after another, with each block
        potentially using previous blocks as context.

        Args:
            block_types: List of block types to generate in order
            context: Context information for generation

        Yields:
            Content blocks in sequence
        """
        ...

    async def generate_blocks_looped(
        self,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        max_iterations: int = 10,
        condition: Optional[Any] = None,
    ) -> AsyncIterator[ContentBlock]:
        """Generate content blocks in a loop with refinement.

        Useful for iterative content generation where each iteration
        refines or builds upon previous attempts.

        Args:
            block_type: Type of block to generate
            context: Context information for generation
            max_iterations: Maximum number of iterations
            condition: Optional condition to stop iteration

        Yields:
            Refined content blocks
        """
        ...

    async def generate_blocks_conditional(
        self,
        context: Dict[str, Any],
        condition_fn: Any,
    ) -> AsyncIterator[ContentBlock]:
        """Generate content blocks conditionally.

        Blocks are generated based on conditions evaluated at runtime,
        allowing for branching and dynamic content generation.

        Args:
            context: Context information for generation
            condition_fn: Function to determine next block type/generation

        Yields:
            Conditionally generated content blocks
        """
        ...

    async def validate_block(self, block: ContentBlock) -> bool:
        """Validate a content block.

        Args:
            block: Content block to validate

        Returns:
            True if block is valid, False otherwise
        """
        ...
