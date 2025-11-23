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
**For agents that generate structured content blocks.**

```python
class ContentProtocol(Protocol):
    async def generate_block(self, block_type: ContentBlockType, context: Dict[str, Any], 
                            previous_blocks: Optional[List[ContentBlock]] = None) -> ContentBlock: ...
    async def generate_blocks_sequential(self, block_types: List[ContentBlockType], 
                                        context: Dict[str, Any]) -> AsyncIterator[ContentBlock]: ...
    async def generate_blocks_looped(self, block_type: ContentBlockType, context: Dict[str, Any],
                                    max_iterations: int = 10, condition: Optional[Any] = None) -> AsyncIterator[ContentBlock]: ...
    async def generate_blocks_conditional(self, context: Dict[str, Any], 
                                         condition_fn: Any) -> AsyncIterator[ContentBlock]: ...
    async def validate_block(self, block: ContentBlock) -> bool: ...
```

For generating content as structured blocks (scenes, cards, chapters) with support for:
- Sequential generation (one after another)
- Looped generation (iterative refinement)
- Conditional generation (branching narratives)

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

## Key Principles

1. **Protocols are interfaces** - They define contracts, not implementations
2. **No inheritance required** - Structural subtyping (duck typing with type checking)
3. **Multiple protocols** - Agents can implement any combination
4. **Type safety** - Static type checkers can verify protocol compliance
5. **Flexibility** - Easy to add new protocols without changing existing code
