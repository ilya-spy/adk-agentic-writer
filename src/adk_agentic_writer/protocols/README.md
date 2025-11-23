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

Core agent operations that every agent must support. The `process_task` method is the universal interface for all agent communication.

### EditorialProtocol (Optional)
**For agents that review, validate, and refine content.**

```python
class EditorialProtocol(Protocol):
    async def review_content(self, content: Dict[str, Any], review_criteria: Dict[str, Any]) -> Dict[str, Any]: ...
    async def validate_content(self, content: Dict[str, Any]) -> bool: ...
    async def refine_content(self, content: Dict[str, Any], feedback: str | Dict[str, Any]) -> Dict[str, Any]: ...
```

**Expressed as AgentTask:**
```python
AgentTask(
    task_id="review_1",
    agent_role=AgentRole.REVIEWER,
    description="Review story content",
    parameters={"content": {...}, "review_criteria": {...}},
    output_key="review_feedback",  # Store for later use
    input_keys=["story_draft"]  # Use previous output
)
```

For content review, validation, and refinement operations:
- **review_content**: Generate detailed review/feedback (used as input to refine)
- **validate_content**: Check if content meets basic validity requirements
- **refine_content**: Improve content based on review feedback

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
    async def validate_block(self, block: ContentBlock) -> bool: ...
```

**Expressed as AgentTask:**
```python
AgentTask(
    task_id="content_1",
    agent_role=AgentRole.STORY_WRITER,
    description="Generate sequential story blocks",
    parameters={
        "num_blocks": 5,
        "block_type": "SCENE",
        "context": {"topic": "adventure", "genre": "fantasy"}
    },
    suggested_workflow="sequential_content",  # Hint for workflow selection
    suggested_team="content_team",  # Hint for team selection
    output_key="story_blocks"
)
```

For creating content blocks (scenes, cards, chapters) that define **user interaction patterns**:
- **Sequential**: Linear reading/navigation (A → B → C)
- **Looped**: Repeatable content with exit conditions (practice loops, flashcards)
- **Branched**: Choice-based navigation (choose-your-own-adventure)
- **Conditional**: State-based content visibility (unlockable sections)

**Key Concept**: These methods specify the **content block pattern** (how users interact with the content structure), NOT the generation process (how the agent internally creates the content). The agent can use any internal workflow to generate the blocks, but the output must match the specified interaction pattern.

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

## Content Block Patterns Explained

The `ContentProtocol` defines methods for generating content blocks with specific **user interaction patterns**. These patterns describe the structure and navigation model of the content from the user's perspective, not how the agent generates it internally.

### Sequential Pattern (Linear Reading)
```python
blocks = await agent.generate_sequential_blocks(
    num_blocks=5,
    block_type=ContentBlockType.CHAPTER,
    context={"topic": "Python basics"}
)
```

**Output**: Chapter 1 → Chapter 2 → Chapter 3 → Chapter 4 → Chapter 5

**User Interaction Pattern**: Linear progression, users read/navigate in order  
**Use Cases**: Books, courses, tutorials, presentations

**What this means**: The agent generates blocks where each builds on the previous one, creating a linear narrative or learning path. Users experience the content sequentially.

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

**Output**: Card 1 ⟲ Card 2 ⟲ Card 3 ⟲ (repeat until score ≥80 or 3 attempts)

**User Interaction Pattern**: Users can repeat the content set multiple times until exit condition is met  
**Use Cases**: 
- Practice exercises (repeat until mastery)
- Mini-games (play again button)
- Flashcards (review loop)
- Skill drills

**What this means**: The agent generates blocks with navigation metadata that allows users to go back, repeat sections, and continue looping until they meet the exit condition (e.g., pass the quiz, reach mastery level).

**Block Features**:
- Navigation: Back button support
- Exit condition: When users can leave the loop
- Progress tracking: Metadata for iteration count

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

**Output**: Branch point with multiple paths based on user choice

**User Interaction Pattern**: Users make choices that determine which content blocks they see next  
**Use Cases**:
- Interactive stories
- Decision trees
- Scenario-based learning
- Multiple endings

**What this means**: The agent generates blocks with choice metadata that creates branching paths. Users navigate through different content based on their decisions, creating a non-linear experience.

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

**Output**: Blocks with condition metadata determining when they're shown

**User Interaction Pattern**: Content visibility depends on runtime conditions (user state, progress, etc.)  
**Use Cases**:
- Adaptive learning paths
- Unlockable content
- Prerequisite-based sections
- Personalized experiences

**What this means**: The agent generates blocks with condition metadata. The content exists but is only displayed to users when their state/progress meets the specified conditions (e.g., completed prerequisites, reached certain level).

## Orchestration with Teams and Workflows

### Agent Orchestration Model

Agents can coordinate teams and workflows to execute complex tasks:

```python
from adk_agentic_writer.models import (
    AgentModel, AgentTask, TeamMetadata, WorkflowMetadata,
    OrchestrationStrategy, WorkflowPattern, WorkflowScope
)

# Define team
team = TeamMetadata(
    name="content_team",
    scope=WorkflowScope.CONTENT,
    agent_ids=["writer", "editor", "reviewer"]
)

# Define workflows
workflow = WorkflowMetadata(
    name="review_loop",
    pattern=WorkflowPattern.LOOP,
    scope=WorkflowScope.EDITORIAL,
    description="Iterative review and refinement",
    max_iterations=3
)

# Create agent with teams and workflows
agent = AgentModel(
    name="coordinator",
    model_name="gemini-2.5-flash-lite",
    instruction="Coordinate content creation",
    teams=[team],
    workflows=[workflow]
)

# Create task with output management
task = AgentTask(
    task_id="create_story",
    agent_role=AgentRole.COORDINATOR,
    description="Create and review story",
    parameters={"topic": "adventure", "length": "medium"},
    suggested_workflow="review_loop",
    suggested_team="content_team",
    output_key="final_story",  # Store output
    input_keys=["story_outline"]  # Use previous output
)

# Use strategy to select workflow
strategy = OrchestrationStrategy(
    name="default",
    scope_to_team={"content": "content_team", "editorial": "review_team"}
)

decision = strategy.select_workflow(
    task, 
    agent.workflows,
    {"expected_iterations": 2, "requires_review": True}
)
# Returns: WorkflowDecision(workflow_name="review_loop", confidence=0.7, ...)
```

### Output Reuse Across Stages

Tasks can reference outputs from previous stages:

```python
# Stage 1: Generate draft
task1 = AgentTask(
    task_id="draft",
    description="Write story draft",
    parameters={"topic": "adventure"},
    output_key="story_draft"  # Store for later
)

# Stage 2: Review draft (uses output from stage 1)
task2 = AgentTask(
    task_id="review",
    description="Review story",
    parameters={"review_criteria": {...}},
    input_keys=["story_draft"],  # Reference previous output
    output_key="review_feedback"
)

# Stage 3: Refine based on feedback (uses outputs from stages 1 & 2)
task3 = AgentTask(
    task_id="refine",
    description="Refine story based on feedback",
    parameters={},
    input_keys=["story_draft", "review_feedback"],  # Use both
    output_key="final_story"
)
```

### Strategy Decision Methods

`OrchestrationStrategy` provides methods for workflow selection:

- **`select_workflow()`**: Choose workflow based on task characteristics
- **`evaluate_condition()`**: Evaluate conditions for workflow control flow
- **`_select_team()`**: Select appropriate team based on scope and role

## Key Principles

1. **Protocols are interfaces** - They define contracts, not implementations
2. **No inheritance required** - Structural subtyping (duck typing with type checking)
3. **Multiple protocols** - Agents can implement any combination
4. **Type safety** - Static type checkers can verify protocol compliance
5. **Flexibility** - Easy to add new protocols without changing existing code
6. **Content block patterns ≠ Generation workflows** - ContentProtocol methods specify the **output structure and user interaction model**, not the internal generation process. An agent can use any workflow (sequential, parallel, iterative) internally to generate blocks with the specified pattern.
7. **Task-based communication** - All agents communicate via `process_task` using `AgentTask` objects, enabling orchestration and output reuse
