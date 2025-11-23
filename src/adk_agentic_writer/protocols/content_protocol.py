"""Protocol defining the interface for content block patterns.

This protocol defines content structure patterns based on how users interact with content,
not how we generate it. Content can have different user interaction patterns:
- Sequential: Linear reading/progression (chapter 1 → 2 → 3)
- Looped: Repeatable sections with exit conditions (practice loops, mini-games)
- Branched: Choice-based navigation (choose-your-own-adventure)
- Conditional: Content shown based on user state/progress
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


class ContentPattern(str, Enum):
    """User interaction patterns for content structure.

    These patterns define how users navigate and consume content,
    not how the content is generated.
    """

    SEQUENTIAL = "sequential"  # Linear progression: A → B → C
    LOOPED = "looped"  # Repeatable with exit: A ⟲ (until condition) → B
    BRANCHED = "branched"  # Choice-based: A → [B|C|D]
    CONDITIONAL = "conditional"  # State-based: Show A if condition met
    PARALLEL = "parallel"  # Independent sections accessible in any order


class ContentBlock:
    """Represents a single block of content with navigation/interaction metadata.

    Content blocks define both the content and how users interact with it.
    Blocks can have:
    - Navigation controls (next, previous, choice buttons)
    - Exit conditions (for looped content)
    - Conditional display rules
    - Branching choices
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


@runtime_checkable
class ContentProtocol(Protocol):
    """Protocol defining the interface for content block patterns.

    Agents implementing this protocol can generate structured content with
    different user interaction patterns:
    - Sequential: Linear reading pattern (chapters, slides)
    - Looped: Repeatable content with exit conditions (practice, mini-games)
    - Branched: Choice-based navigation (interactive stories)
    - Conditional: State-based content display

    Methods create content structures, not generation workflows.
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

    async def generate_sequential_blocks(
        self,
        num_blocks: int,
        block_type: ContentBlockType,
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate sequential blocks for linear reading pattern.

        Creates a sequence of blocks where user progresses linearly:
        Block 1 → Block 2 → Block 3 → ... → Block N

        Each block has navigation to next/previous blocks.

        Args:
            num_blocks: Number of sequential blocks to generate
            block_type: Type of blocks (scene, chapter, slide, etc.)
            context: Context for content generation

        Returns:
            List of sequential content blocks with navigation
        """
        ...

    async def generate_looped_blocks(
        self,
        num_blocks: int,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        exit_condition: Dict[str, Any],
        allow_back: bool = True,
    ) -> List[ContentBlock]:
        """Generate looped blocks that user can repeat until exit condition met.

        Creates a set of blocks in a loop pattern:
        Block 1 ⟲ Block 2 ⟲ Block 3 ⟲ ... → (exit when condition met)

        Useful for:
        - Practice exercises (repeat until mastery)
        - Mini-games (play again until score threshold)
        - Learning modules (review until understood)

        Args:
            num_blocks: Number of blocks in the loop
            block_type: Type of blocks
            context: Context for content generation
            exit_condition: Condition to exit loop (e.g., {"score": ">=80", "attempts": ">=3"})
            allow_back: Whether to include back navigation within loop

        Returns:
            List of looped content blocks with navigation and exit conditions
        """
        ...

    async def generate_branched_blocks(
        self,
        branch_points: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate branched blocks for choice-based navigation.

        Creates blocks with choice branches:
        Block A → [Choice 1 → Block B]
                  [Choice 2 → Block C]
                  [Choice 3 → Block D]

        Each branch point defines choices and resulting blocks.

        Args:
            branch_points: List of branch definitions, each containing:
                - block_type: Type of block at this branch point
                - choices: List of choice options
                - branches: Map of choice to next blocks
            context: Context for content generation

        Returns:
            List of branched content blocks with choice navigation
        """
        ...

    async def generate_conditional_blocks(
        self,
        blocks_config: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate conditional blocks shown based on user state/progress.

        Creates blocks that appear conditionally:
        - Show Block A if user completed prerequisite
        - Show Block B if user score > threshold
        - Show Block C if user chose specific path

        Args:
            blocks_config: List of block configurations with conditions:
                - block_type: Type of block
                - condition: Display condition
                - content_spec: Content specification
            context: Context for content generation

        Returns:
            List of conditional content blocks with display rules
        """
        ...
