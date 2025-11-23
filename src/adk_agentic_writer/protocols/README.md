# Protocols

Protocol interfaces for the ADK Agentic Writer system.

## Overview

This folder contains **pure interface definitions** using Python's `Protocol` from typing.
Protocols define **what** agents can do, not **how** they do it.

## Communication Model

**All agents communicate via `process_task` using `AgentTask` objects.**

Higher-level protocols (`ContentProtocol`, `EditorialProtocol`) are expressed as tasks with specific parameters. This allows:
- Agents to decide which teams and workflows to use
- Orchestration through task-based coordination
- Output reuse across stages via `output_key` and `input_keys`

## Available Protocols

### AgentProtocol (Required)
**All agents must implement this protocol.**

```python
class AgentProtocol(Protocol):
    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]: ...
    async def update_status(self, status: AgentStatus) -> None: ...
    def get_state(self) -> AgentState: ...
```

**Functions:**
- `process_task`: Universal interface for all agent communication, accepts task description and parameters
- `update_status`: Update agent status (IDLE, WORKING, COMPLETED, ERROR)
- `get_state`: Retrieve current agent state including variables and metadata

### EditorialProtocol (Optional)
**For agents that review, validate, and refine content.**

```python
class EditorialProtocol(Protocol):
    async def review_content(self, content: Dict[str, Any], review_criteria: Dict[str, Any]) -> Dict[str, Any]: ...
    async def validate_content(self, content: Dict[str, Any]) -> bool: ...
    async def refine_content(self, content: Dict[str, Any], feedback: str | Dict[str, Any]) -> Dict[str, Any]: ...
```

**Functions:**
- `review_content`: Analyze content and generate detailed feedback/suggestions
- `validate_content`: Check if content meets quality and correctness requirements
- `refine_content`: Improve content based on review feedback

**Expressed as AgentTask:**
```python
AgentTask(
    task_id="review_content",  # Matches function name
    agent_role=AgentRole.REVIEWER,
    prompt="Review the {content_type} content from {story_draft} and provide feedback",
    parameters={"content_type": "story", "review_criteria": {...}},
    output_key="review_feedback"
)
# Variables like {story_draft} are resolved from AgentState.variables
```

### ContentProtocol (Optional)
**For agents that generate content blocks with specific user interaction patterns.**

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
```

**Functions:**
- `generate_block`: Create single content block with context awareness
- `generate_sequential_blocks`: Linear content progression (chapters, scenes)
- `generate_looped_blocks`: Repeatable content with exit conditions (practice, flashcards)
- `generate_branched_blocks`: Choice-based navigation (interactive stories)
- `generate_conditional_blocks`: State-based visibility (unlockable content)

**Expressed as AgentTask:**
```python
AgentTask(
    task_id="generate_sequential_blocks",  # Matches function name
    agent_role=AgentRole.STORY_WRITER,
    prompt="Generate {num_blocks} sequential {block_type} blocks about {topic} in {genre} style",
    parameters={"num_blocks": 5, "block_type": "SCENE", "topic": "adventure", "genre": "fantasy"},
    suggested_workflow="sequential_content",
    suggested_team="content_team",
    output_key="story_blocks"
)
```

**Key Concept**: Methods specify content block patterns (user interaction model), not generation process (internal workflow).

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
    async def review_content(self, content: Dict[str, Any], review_criteria: Dict[str, Any]) -> Dict[str, Any]:
        # Generate review and feedback
        pass
    
    async def validate_content(self, content: Dict[str, Any]) -> bool:
        # Validate content
        pass
    
    async def refine_content(self, content: Dict[str, Any], feedback: str | Dict[str, Any]) -> Dict[str, Any]:
        # Refine based on feedback
        pass
```

### Type Hints

Use protocols for type checking:

```python
def process_agent(agent: AgentProtocol) -> None:
    """Function that accepts any agent implementing AgentProtocol."""
    result = await agent.process_task("task", {})

async def edit_content(agent: EditorialProtocol, content: Dict[str, Any]) -> None:
    """Function that accepts any agent implementing EditorialProtocol."""
    # First review the content
    review = await agent.review_content(content, {"focus": "quality"})
    
    # Then refine based on review feedback
    if review.get("issues_found"):
        content = await agent.refine_content(content, review["feedback"])
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

## Orchestration with Teams and Workflows

Agents coordinate teams and workflows to execute complex tasks. See `utils/README.md` for details on `OrchestrationStrategy` and `TaskCollection`.

### Example: Agent with Teams and Workflows

```python
from adk_agentic_writer.models import AgentModel, TeamMetadata, WorkflowMetadata

# Agent with team and workflow
agent = AgentModel(
    name="coordinator",
    model_name="gemini-2.5-flash-lite",
    instruction="Coordinate content creation",
    teams=[TeamMetadata(name="content_team", scope=WorkflowScope.CONTENT, 
                        agent_ids=["writer", "editor"])],
    workflows=[WorkflowMetadata(name="review_loop", pattern=WorkflowPattern.LOOP,
                                scope=WorkflowScope.EDITORIAL, description="Review loop")]
)
```

### Example: Task Pipeline with Variable Reuse

```python
# Task outputs stored in AgentState.variables, referenced in subsequent prompts
task1 = AgentTask(
    task_id="generate_content",
    prompt="Write a story about {topic}",
    output_key="story_draft"  # Stored in variables["story_draft"]
)

task2 = AgentTask(
    task_id="review_content", 
    prompt="Review this story: {story_draft}",  # References variables["story_draft"]
    output_key="review_feedback"
)

task3 = AgentTask(
    task_id="refine_content",
    prompt="Refine {story_draft} based on: {review_feedback}",  # Uses both variables
    output_key="final_story"
)
```

### Example: Protocol Interface via Task Delegation

```python
from adk_agentic_writer.tasks import GENERATE_SEQUENTIAL_BLOCKS, REVIEW_CONTENT, REFINE_CONTENT
from adk_agentic_writer.teams import STORY_WRITER, EDITORIAL_REVIEWER, EDITORIAL_REFINER
from adk_agentic_writer.utils.variable_substitution import substitute_variables

# Implement protocol by delegating to team members
class ContentCoordinator:
    async def create_and_review_content(self, topic, genre, num_blocks):
        # Step 1: Generate content with specialized writer
        self.state.variables.update({
            "topic": topic,
            "genre": genre,
            "num_blocks": num_blocks,
            "block_type": "SCENE"
        })
        
        prompt = substitute_variables(GENERATE_SEQUENTIAL_BLOCKS.prompt, self.state.variables)
        content = await self.execute_with_agent(STORY_WRITER, prompt)
        self.state.variables["content_draft"] = content
        
        # Step 2: Review content with editorial reviewer
        prompt = substitute_variables(REVIEW_CONTENT.prompt, self.state.variables)
        feedback = await self.execute_with_agent(EDITORIAL_REVIEWER, prompt)
        self.state.variables["feedback"] = feedback
        
        # Step 3: Refine content with editorial refiner
        prompt = substitute_variables(REFINE_CONTENT.prompt, self.state.variables)
        refined = await self.execute_with_agent(EDITORIAL_REFINER, prompt)
        self.state.variables["refined_content"] = refined
        
        return refined
```

## Key Principles

1. **Protocols are interfaces** - They define contracts, not implementations
2. **No inheritance required** - Structural subtyping (duck typing with type checking)
3. **Multiple protocols** - Agents can implement any combination
4. **Type safety** - Static type checkers can verify protocol compliance
5. **Flexibility** - Easy to add new protocols without changing existing code
6. **Content block patterns ≠ Generation workflows** - ContentProtocol methods specify the **output structure and user interaction model**, not the internal generation process. An agent can use any workflow (sequential, parallel, iterative) internally to generate blocks with the specified pattern.
7. **Task-based communication** - All agents communicate via `process_task` using `AgentTask` objects, enabling orchestration and output reuse
