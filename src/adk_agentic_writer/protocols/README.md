# Protocols

Protocol interfaces for the ADK Agentic Writer system.

## Overview

This folder contains **pure interface definitions** using Python's `Protocol` from typing.
Protocols define **what** agents can do, not **how** they do it.

## Available Protocols

### AgentProtocol (Required)
**All agents must implement this protocol.**

```python
class AgentProtocol(Protocol):
    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]: ...
    async def update_status(self, status: AgentStatus) -> None: ...
    def get_state(self) -> AgentState: ...
```

Core agent operations that every agent must support.

### EditorialProtocol (Optional)
**For agents that edit and refine content.**

```python
class EditorialProtocol(Protocol):
    async def generate_content(self, prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]: ...
    async def validate_content(self, content: Dict[str, Any]) -> bool: ...
    async def refine_content(self, content: Dict[str, Any], feedback: str) -> Dict[str, Any]: ...
```

For content generation, validation, and refinement operations.

### ContentProtocol (Optional)
**For agents that generate structured content with user interaction patterns.**

```python
class ContentProtocol(Protocol):
    async def generate_block(self, block_type: ContentBlockType, context: Dict[str, Any], 
                            previous_blocks: Optional[List[ContentBlock]] = None) -> ContentBlock: ...
    async def generate_sequential_blocks(self, num_blocks: int, block_type: ContentBlockType,
                                         context: Dict[str, Any]) -> List[ContentBlock]: ...
    async def generate_looped_blocks(self, num_blocks: int, block_type: ContentBlockType, 
                                    context: Dict[str, Any], exit_condition: Dict[str, Any],
                                    allow_back: bool = True) -> List[ContentBlock]: ...
    async def generate_branched_blocks(self, branch_points: List[Dict[str, Any]],
                                      context: Dict[str, Any]) -> List[ContentBlock]: ...
    async def generate_conditional_blocks(self, blocks_config: List[Dict[str, Any]],
                                         context: Dict[str, Any]) -> List[ContentBlock]: ...
    async def validate_block(self, block: ContentBlock) -> bool: ...
```

For generating content as structured blocks (scenes, cards, chapters) with different **user interaction patterns**:
- **Sequential**: Linear reading pattern (A → B → C)
- **Looped**: Repeatable sections with exit conditions (practice loops, mini-games)
- **Branched**: Choice-based navigation (interactive stories, decision trees)
- **Conditional**: State-based content display (shown when conditions met)

**Key Concept**: Methods define content structure patterns (how users interact), not generation workflows (how we create content).

## Usage

### Import Protocols

```python
from adk_agentic_writer.protocols import AgentProtocol, EditorialProtocol, ContentProtocol
```

### Implement in Agents

```python
from adk_agentic_writer.protocols import AgentProtocol, EditorialProtocol

class MyAgent:
    """Agent implementing AgentProtocol and EditorialProtocol."""
    
    # AgentProtocol methods (required)
    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation
        pass
    
    async def update_status(self, status: AgentStatus) -> None:
        # Implementation
        pass
    
    def get_state(self) -> AgentState:
        # Implementation
        pass
    
    # EditorialProtocol methods (optional)
    async def generate_content(self, prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation
        pass
    
    async def validate_content(self, content: Dict[str, Any]) -> bool:
        # Implementation
        pass
    
    async def refine_content(self, content: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        # Implementation
        pass
```

### Type Hints

Use protocols for type checking:

```python
def process_agent(agent: AgentProtocol) -> None:
    """Function that accepts any agent implementing AgentProtocol."""
    result = await agent.process_task("task", {})

def edit_content(agent: EditorialProtocol, content: Dict[str, Any]) -> None:
    """Function that accepts any agent implementing EditorialProtocol."""
    is_valid = await agent.validate_content(content)
    if not is_valid:
        content = await agent.refine_content(content, "improve quality")
```

## Protocol Composition

Agents can implement multiple protocols:

- **Basic Agent**: `AgentProtocol` only
- **Editorial Agent**: `AgentProtocol` + `EditorialProtocol`
- **Content Generator**: `AgentProtocol` + `EditorialProtocol` + `ContentProtocol`

Example:
```python
class StoryWriterAgent:
    """Implements all three protocols for maximum flexibility."""
    pass

# Type checking works for any protocol
agent: AgentProtocol = StoryWriterAgent()
editor: EditorialProtocol = StoryWriterAgent()
generator: ContentProtocol = StoryWriterAgent()
```

## Content Patterns Explained

The `ContentProtocol` defines methods for creating different **content structure patterns** based on how users interact with content.

### Sequential Pattern (Linear Reading)
```python
blocks = await agent.generate_sequential_blocks(
    num_blocks=5,
    block_type=ContentBlockType.CHAPTER,
    context={"topic": "Python basics"}
)
```

Creates: Chapter 1 → Chapter 2 → Chapter 3 → Chapter 4 → Chapter 5

**User Experience**: Linear progression, read in order  
**Use Cases**: Books, courses, tutorials, presentations

### Looped Pattern (Repeatable Content)
```python
blocks = await agent.generate_looped_blocks(
    num_blocks=3,
    block_type=ContentBlockType.CARD,
    context={"topic": "Vocabulary quiz"},
    exit_condition={"score": ">=80", "or": "attempts>=3"},
    allow_back=True
)
```

Creates: Card 1 ⟲ Card 2 ⟲ Card 3 ⟲ (repeat until score ≥80 or 3 attempts)

**User Experience**: Repeatable practice with exit condition  
**Use Cases**: 
- Practice exercises (repeat until mastery)
- Mini-games (play again button)
- Flashcards (review loop)
- Skill drills

**Key Features**:
- Back button support (review previous cards)
- Exit condition (when to leave loop)
- Progress tracking

### Branched Pattern (Choice-Based Navigation)
```python
blocks = await agent.generate_branched_blocks(
    branch_points=[
        {
            "block_type": ContentBlockType.SCENE,
            "content": "You reach a fork in the road",
            "choices": [
                {"text": "Go left", "leads_to": "forest_scene"},
                {"text": "Go right", "leads_to": "mountain_scene"},
                {"text": "Turn back", "leads_to": "village_scene"}
            ]
        }
    ],
    context={"story": "Adventure"}
)
```

Creates: Branch point with multiple paths based on user choice

**User Experience**: Choose-your-own path  
**Use Cases**:
- Interactive stories
- Decision trees
- Scenario-based learning
- Multiple endings

### Conditional Pattern (State-Based Display)
```python
blocks = await agent.generate_conditional_blocks(
    blocks_config=[
        {
            "block_type": ContentBlockType.SECTION,
            "condition": {"user_level": ">=3"},
            "content_spec": {"topic": "Advanced concepts"}
        },
        {
            "block_type": ContentBlockType.SECTION,
            "condition": {"completed": ["intro", "basics"]},
            "content_spec": {"topic": "Next steps"}
        }
    ],
    context={"course": "Python"}
)
```

Creates: Blocks shown only when conditions are met

**User Experience**: Dynamic content based on progress/state  
**Use Cases**:
- Adaptive learning paths
- Unlockable content
- Prerequisite-based sections
- Personalized experiences

## Key Principles

1. **Protocols are interfaces** - They define contracts, not implementations
2. **No inheritance required** - Structural subtyping (duck typing with type checking)
3. **Multiple protocols** - Agents can implement any combination
4. **Type safety** - Static type checkers can verify protocol compliance
5. **Flexibility** - Easy to add new protocols without changing existing code
6. **Content patterns ≠ Generation patterns** - Methods define user interaction, not how we generate
