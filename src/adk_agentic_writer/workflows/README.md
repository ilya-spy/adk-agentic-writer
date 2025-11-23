# Workflows

Workflow patterns for orchestrating agents, editorial operations, and content generation.

## Overview

Workflows define orchestration patterns that inherit from base workflow classes.
They correspond to the three protocol types:

1. **Agent Workflows** - Orchestrate multiple agents
2. **Editorial Workflows** - Orchestrate content editing/refinement (EditorialProtocol)
3. **Content Workflows** - Orchestrate UX interaction patterns (ContentProtocol)

## Workflow Types

### Base Workflows (`base_workflow.py`)

Foundation patterns that all workflows inherit from:

- `SequentialWorkflow` - Execute in order: A → B → C
- `ParallelWorkflow` - Execute concurrently: [A, B, C] → Merge
- `LoopWorkflow` - Execute repeatedly: A → Check → A → ...
- `ConditionalWorkflow` - Branch based on conditions: Condition → [A | B | C]

### Agent Workflows (`agent_workflows.py`)

Orchestrate multiple agents working together:

- `SequentialAgentWorkflow` - Agents execute in sequence
- `ParallelAgentWorkflow` - Agents execute concurrently
- `LoopAgentWorkflow` - Agent executes in loop
- `ConditionalAgentWorkflow` - Route to different agents based on conditions

### Editorial Workflows (`editorial_workflows.py`)

Orchestrate content editing and refinement (corresponds to **EditorialProtocol**):

- `SequentialEditorialWorkflow` - Edit in stages: Draft → Refine → Review → Finalize
- `ParallelEditorialWorkflow` - Generate variants concurrently, select best
- `IterativeEditorialWorkflow` - Refine through iterations: Generate → Validate → Refine
- `AdaptiveEditorialWorkflow` - Adapt editing strategy based on content type

### Content Workflows (`content_workflows.py`)

Orchestrate UX interaction patterns (corresponds to **ContentProtocol**):

- `SequentialContentWorkflow` - Generate blocks in sequence (scenes, cards, chapters)
- `LoopedContentWorkflow` - Generate and refine blocks iteratively
- `ConditionalContentWorkflow` - Generate blocks based on conditions (branching narratives)
- `InteractiveContentWorkflow` - Generate with user interaction points
- `AdaptiveContentWorkflow` - Adapt generation based on user behavior
- `StreamingContentWorkflow` - Generate and stream blocks in real-time

## Usage

### Import Workflows

```python
from adk_agentic_writer.workflows import (
    # Agent workflows
    SequentialAgentWorkflow,
    
    # Editorial workflows
    IterativeEditorialWorkflow,
    
    # Content workflows
    SequentialContentWorkflow,
    ConditionalContentWorkflow,
)
```

### Example: Editorial Workflow

```python
# Iterative refinement workflow
workflow = IterativeEditorialWorkflow(
    name="quiz_refinement",
    generator=quiz_agent,  # Implements EditorialProtocol
    evaluator=reviewer_agent,
    max_iterations=3
)

result = await workflow.execute({"topic": "Python", "difficulty": "medium"})
```

### Example: Content Workflow

```python
# Sequential story generation
workflow = SequentialContentWorkflow(
    name="story_generation",
    block_types=["SCENE", "SCENE", "SCENE"],
    generator=story_agent  # Implements ContentProtocol
)

result = await workflow.execute({"theme": "adventure", "genre": "fantasy"})
```

### Example: Conditional Content Workflow

```python
# Branching narrative
def branching_logic(context):
    if context["user_choice"] == "left":
        return "path_a"
    return "path_b"

workflow = ConditionalContentWorkflow(
    name="branching_story",
    condition_fn=branching_logic,
    generators={
        "path_a": story_agent_a,
        "path_b": story_agent_b,
    }
)
```

## Workflow Hierarchy

```
base_workflow.py (foundation patterns)
    ↓
├── agent_workflows.py (agent orchestration)
├── editorial_workflows.py (EditorialProtocol operations)
└── content_workflows.py (ContentProtocol operations)
```

## Correspondence with Protocols

| Workflow Type | Protocol | Purpose |
|--------------|----------|---------|
| Agent Workflows | AgentProtocol | Orchestrate multiple agents |
| Editorial Workflows | EditorialProtocol | Content editing/refinement |
| Content Workflows | ContentProtocol | UX interaction patterns |

## Key Principles

1. **Inheritance** - All workflows inherit from base patterns
2. **Composition** - Workflows compose agents and operations
3. **Patterns** - Reusable orchestration patterns
4. **Flexibility** - Mix and match workflows as needed
5. **Separation** - Clear separation between workflow types

