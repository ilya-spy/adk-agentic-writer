# Protocols

Protocol interfaces defining agent capabilities.

## Overview

Protocols define **what** agents can do, not **how**. All agents communicate via `process_task()` using `AgentTask` objects.

## AgentProtocol (Required)

```python
class AgentProtocol(Protocol):
    async def process_task(self, task: AgentTask, parameters: Dict = None) -> Dict: ...
    async def update_status(self, status: AgentStatus) -> None: ...
    def get_state(self) -> AgentState: ...
```

## ContentProtocol (Optional)

For content-generating agents:

```python
class ContentProtocol(Protocol):
    async def generate_text(prompt_key: str, context: Dict) -> str: ...
    async def generate_block(block_type, context, previous_blocks) -> ContentBlock: ...
    async def generate_patterned_blocks(block_type, pattern, context) -> List[ContentBlock]: ...
```

- `generate_text`: Text via TextProvider
- `generate_block`: Single content block
- `generate_patterned_blocks`: Blocks with navigation (sequential, looped, branched)

**Note**: Data models (`ContentBlock`, `ContentBlockType`, `ContentPattern`) are in `models/content_models.py`.

## AdaptiveContentProtocol (Optional)

For adaptive content based on user behavior:

```python
class AdaptiveContentProtocol(Protocol):
    async def analyze_user_behavior(...) -> Dict: ...
    async def adapt_content_strategy(...) -> Dict: ...
    async def generate_adaptive_blocks(...) -> Dict: ...
    async def generate_variant_blocks(...) -> Dict: ...
```

## EditorialProtocol (Optional)

```python
class EditorialProtocol(Protocol):
    async def review_content(content, criteria) -> Dict: ...
    async def validate_content(content) -> bool: ...
    async def refine_content(content, feedback) -> Dict: ...
```

## Usage

```python
from adk_agentic_writer.agents import ContentWriterAgent
from adk_agentic_writer.models import AgentTask, AgentConfig

class MyAgent(ContentWriterAgent):
    async def generate_block(self, block_type, context, previous_blocks=None):
        # Custom block generation
        return ContentBlock(...)
    
    async def _build_content(self, context):
        # Custom content building
        return {"title": "...", "content": "..."}
```

## Protocol Composition

Agents can implement multiple protocols:
- **Basic**: `AgentProtocol` only
- **Content**: `AgentProtocol` + `ContentProtocol`
- **Editorial**: `AgentProtocol` + `EditorialProtocol`
- **Full**: All protocols

## Key Principles

- **Interface-based**: Define contracts, not implementations
- **Structural typing**: No inheritance required
- **Composable**: Implement multiple protocols
- **Task-driven**: Communication via `process_task()`
