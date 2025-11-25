# Protocols

Protocol interfaces defining agent capabilities.

## Overview

**Protocols** define **what** agents can do, not **how** they do it.

**Communication**: All agents communicate via `process_task` using `AgentTask` objects.

---

## Available Protocols

### AgentProtocol (Required)

```python
class AgentProtocol(Protocol):
    async def process_task(self, task: AgentTask, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]: ...
    async def update_status(self, status: AgentStatus) -> None: ...
    def get_state(self) -> AgentState: ...
```

- `process_task`: Universal task interface (accepts AgentTask object)
- `update_status`: Update status (IDLE, WORKING, COMPLETED, ERROR)
- `get_state`: Retrieve agent state with variables

### EditorialProtocol (Optional)

```python
class EditorialProtocol(Protocol):
    async def review_content(self, content: Dict[str, Any], review_criteria: Dict[str, Any]) -> Dict[str, Any]: ...
    async def validate_content(self, content: Dict[str, Any]) -> bool: ...
    async def refine_content(self, content: Dict[str, Any], feedback: str | Dict[str, Any]) -> Dict[str, Any]: ...
```

- `review_content`: Generate feedback
- `validate_content`: Check quality requirements
- `refine_content`: Improve based on feedback

### ContentProtocol (Optional)

```python
class ContentProtocol(Protocol):
    async def generate_block(...) -> ContentBlock: ...
    async def generate_sequential_blocks(...) -> List[ContentBlock]: ...
    async def generate_looped_blocks(...) -> List[ContentBlock]: ...
    async def generate_branched_blocks(...) -> List[ContentBlock]: ...
    async def generate_conditional_blocks(...) -> List[ContentBlock]: ...
```

- `generate_block`: Single content block
- `generate_sequential_blocks`: Linear progression (chapters)
- `generate_looped_blocks`: Repeatable with exit (practice)
- `generate_branched_blocks`: Choice-based (stories)
- `generate_conditional_blocks`: State-based visibility

**Note**: Methods specify content patterns (user interaction), not generation workflows (internal process).

---

## Usage

### Implement in Agents

```python
from adk_agentic_writer.agents import BaseAgent
from adk_agentic_writer.models import AgentConfig, AgentTask

class MyAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(
            agent_id=f"{config.role}_agent",
            role=config.role,
            config=config.model_dump()
        )
    
    async def process_task(self, task: AgentTask, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Access task fields directly
        prompt = task.prompt
        params = task.parameters or {}
        if parameters:
            params.update(parameters)
        
        result = await self.generate_block(prompt, context={params})
        return {"output": result}
```

### Protocol Composition

Agents can implement multiple protocols:

- **Basic**: `AgentProtocol` only
- **Editorial**: `AgentProtocol` + `EditorialProtocol`
- **Content**: `AgentProtocol` + `ContentProtocol` + `EditorialProtocol`

---

## Orchestration

**Architecture**: `Workflow → Tasks → Teams → Agents`

### Editorial Workflow

```python
from adk_agentic_writer.workflows import SequentialEditorialWorkflow
from adk_agentic_writer.teams import EDITORIAL_REVIEWER, EDITORIAL_REFINER
from adk_agentic_writer.agents import BaseAgent

reviewer = BaseAgent(config=EDITORIAL_REVIEWER)
refiner = BaseAgent(config=EDITORIAL_REFINER)

workflow = SequentialEditorialWorkflow(
    name="review_and_refine",
    stages=[reviewer, refiner]
)

result = await workflow.execute({
    "draft_content": "Original content...",
    "review_criteria": {"focus": ["clarity", "accuracy"]}
})
```

### Content Generation

```python
from adk_agentic_writer.workflows import AdaptiveContentWorkflow
from adk_agentic_writer.teams import STORY_WRITER
from adk_agentic_writer.agents import BaseAgent

writer = BaseAgent(config=STORY_WRITER)

workflow = AdaptiveContentWorkflow(
    name="adaptive_story",
    generator=writer,
    adaptator=writer,
    max_iterations=10
)

result = await workflow.execute({
    "topic": "space exploration",
    "genre": "sci-fi",
    "user_interactions": {"engagement_level": "high"}
})
```

### Task-Based Communication

```python
from adk_agentic_writer.tasks import content_tasks, editorial_tasks
from adk_agentic_writer.teams import STORY_WRITER, EDITORIAL_REVIEWER
from adk_agentic_writer.agents import BaseAgent

writer = BaseAgent(config=STORY_WRITER)
reviewer = BaseAgent(config=EDITORIAL_REVIEWER)

# Generate content
task1 = content_tasks.GENERATE_SEQUENTIAL_BLOCKS
result1 = await writer.process_task(task=task1)

# Review content
task2 = editorial_tasks.REVIEW_DRAFT
result2 = await reviewer.process_task(task=task2)
```

---

## Key Principles

✅ **Interface-based** - Define contracts, not implementations  
✅ **Structural typing** - No inheritance required  
✅ **Composable** - Implement multiple protocols  
✅ **Type-safe** - Static verification support  
✅ **Task-driven** - All communication via `process_task`
