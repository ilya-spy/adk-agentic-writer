# Protocol Structure

## Overview

This folder contains **pure protocol interfaces** - no implementations, no base classes, just interface definitions.

## Files

```
protocols/
├── __init__.py                 # Exports all protocols
├── agent_protocol.py           # AgentProtocol (required for all agents)
├── editorial_protocol.py       # EditorialProtocol (optional)
├── content_protocol.py         # ContentProtocol (optional) + ContentBlock, ContentBlockType
├── README.md                   # Usage documentation
└── STRUCTURE.md               # This file
```

## Protocol Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    PROTOCOL INTERFACES                      │
│                  (Pure interface definitions)               │
└─────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │    Agent     │ │  Editorial   │ │   Content    │
        │   Protocol   │ │   Protocol   │ │   Protocol   │
        │  (REQUIRED)  │ │  (OPTIONAL)  │ │  (OPTIONAL)  │
        └──────────────┘ └──────────────┘ └──────────────┘
                │              │              │
                └──────────────┼──────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Agent              │
                    │  Implementations    │
                    │  (in agents/ folder)│
                    └─────────────────────┘
```

## Protocol Composition

Agents implement one or more protocols:

| Agent Type | AgentProtocol | EditorialProtocol | ContentProtocol |
|---------- -|---------------|-------------------|-----------------|
| Basic Agent       | ✓ (required) | ✗ | ✗ |
| Editorial Agent   | ✓ (required) | ✓ | ✗ |
| Content Generator | ✓ (required) | ✓ | ✓ |

## Usage Pattern

```python
# 1. Import protocols
from adk_agentic_writer.protocols import AgentProtocol, EditorialProtocol, ContentProtocol

# 2. Implement in your agent class
class MyAgent:
    """No inheritance needed - just implement the methods."""
    
    # AgentProtocol methods (required)
    async def process_task(self, ...): ...
    async def update_status(self, ...): ...
    def get_state(self, ...): ...
    
    # EditorialProtocol methods (optional)
    async def generate_content(self, ...): ...
    async def validate_content(self, ...): ...
    async def refine_content(self, ...): ...

# 3. Use with type hints
def process(agent: AgentProtocol):
    """Accepts any object implementing AgentProtocol."""
    pass

def edit(agent: EditorialProtocol):
    """Accepts any object implementing EditorialProtocol."""
    pass
```

## Key Concepts

### 1. Structural Subtyping
Protocols use structural subtyping (duck typing with type checking). An agent doesn't need to explicitly inherit from a protocol - it just needs to implement the required methods.

### 2. No Base Classes
This folder contains NO base classes or implementations. All implementations are in `agents/` folder.

### 3. Multiple Protocols
Agents can implement any combination of protocols. Each protocol represents a capability.

### 4. Type Safety
Static type checkers (mypy, pyright) can verify that agents correctly implement protocols.

## Examples

### Minimal Agent (AgentProtocol only)
```python
class MinimalAgent:
    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": "done"}
    
    async def update_status(self, status: AgentStatus) -> None:
        self.status = status
    
    def get_state(self) -> AgentState:
        return self.state

# Type checker confirms this implements AgentProtocol
agent: AgentProtocol = MinimalAgent()
```

### Editorial Agent (AgentProtocol + EditorialProtocol)
```python
class EditorialAgent:
    # AgentProtocol methods
    async def process_task(self, ...): ...
    async def update_status(self, ...): ...
    def get_state(self, ...): ...
    
    # EditorialProtocol methods
    async def generate_content(self, ...): ...
    async def validate_content(self, ...): ...
    async def refine_content(self, ...): ...

# Can be used as either protocol
agent: AgentProtocol = EditorialAgent()
editor: EditorialProtocol = EditorialAgent()
```

### Full-Featured Agent (All Protocols)
```python
class FullAgent:
    # AgentProtocol methods
    async def process_task(self, ...): ...
    async def update_status(self, ...): ...
    def get_state(self, ...): ...
    
    # EditorialProtocol methods
    async def generate_content(self, ...): ...
    async def validate_content(self, ...): ...
    async def refine_content(self, ...): ...
    
    # ContentProtocol methods
    async def generate_block(self, ...): ...
    async def generate_blocks_sequential(self, ...): ...
    async def generate_blocks_looped(self, ...): ...
    async def generate_blocks_conditional(self, ...): ...
    async def validate_block(self, ...): ...

# Can be used as any protocol
agent: AgentProtocol = FullAgent()
editor: EditorialProtocol = FullAgent()
generator: ContentProtocol = FullAgent()
```

## Benefits

1. **No inheritance required** - Structural subtyping is more flexible
2. **Clear contracts** - Protocols explicitly define what methods are needed
3. **Type safety** - Static type checkers verify compliance
4. **Composable** - Mix and match protocols as needed
5. **Testable** - Easy to create mock objects for testing
6. **Extensible** - Add new protocols without changing existing code
