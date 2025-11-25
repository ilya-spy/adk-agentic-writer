# Models

Type-safe data models for agents, workflows, content, and editorial operations.

## Overview

**Models** define the data structures used throughout the system:

- **Agent Models**: Agent configuration, tasks, state, and orchestration
- **Content Models**: Interactive content types (quiz, story, game, simulation)
- **Editorial Models**: Review, refinement, feedback, and quality metrics

**Formula**: `Models = Structure + Validation + Type Safety`

---

## Agent Models (`agent_models.py`)

Core orchestration and agent configuration.

### Configuration & Orchestration

| Model | Purpose | Used In |
|-------|---------|---------|
| `AgentConfig` | Agent system instructions + parameters | `teams/` → `agents/` |
| `AgentTask` | Task definition with prompt + dependencies | `tasks/` → `workflows/` |
| `TeamMetadata` | Agent pool configuration | `teams/` → `workflows/` |
| `WorkflowMetadata` | Workflow pattern + scope definition | `workflows/` |

### Enums

| Enum | Values | Usage |
|------|--------|-------|
| `AgentRole` | WRITER, REVIEWER, REFINER, EDITOR, etc. | Task assignment |
| `WorkflowPattern` | SEQUENTIAL, PARALLEL, LOOP, CONDITIONAL | Execution strategy |
| `WorkflowScope` | AGENT, CONTENT, EDITORIAL | Domain separation |

### Runtime State

| Model | Purpose |
|-------|---------|
| `AgentState` | Current status, tasks, variables |
| `AgentStatus` | IDLE, WORKING, WAITING, COMPLETED, ERROR |
| `AgentMessage` | Inter-agent communication |

---

## Content Models (`content_models.py`)

Structured interactive content types.

| Model | Purpose | Used In |
|-------|---------|---------|
| `Quiz` | Educational quizzes with questions | Content generation |
| `QuestGame` | Quest-based games with nodes | Content generation |
| `BranchedNarrative` | Interactive stories with choices | Content generation |
| `WebSimulation` | Simulations with variables + controls | Content generation |

**ContentType Enum**: `QUIZ`, `QUEST_GAME`, `BRANCHED_NARRATIVE`, `WEB_SIMULATION`

---

## Editorial Models (`editorial_models.py`)

Review, refinement, and quality tracking.

| Model | Purpose | Used In |
|-------|---------|---------|
| `Feedback` | Specific improvement suggestions | Editorial workflows |
| `ContentRevision` | Version tracking with changes | Editorial workflows |
| `QualityMetrics` | Quality scores (0-100) | Evaluation tasks |
| `ValidationResult` | Validation errors + warnings | Validation tasks |
| `EditorialRequest` | Editorial action request | API endpoints |
| `EditorialResponse` | Refined content + feedback | API responses |
| `RefinementContext` | Tone, audience, constraints | Refinement tasks |

**EditorialAction Enum**: `VALIDATE`, `REFINE`, `REVIEW`, `APPROVE`, `REJECT`

**FeedbackType Enum**: `GRAMMAR`, `CLARITY`, `ACCURACY`, `STRUCTURE`, `TONE`, `ENGAGEMENT`

---

## Usage

```python
from adk_agentic_writer.models import (
    AgentConfig, AgentTask, TeamMetadata,
    Quiz, BranchedNarrative,
    Feedback, QualityMetrics
)

# Define agent configuration
config = AgentConfig(
    role="story_writer",
    system_instruction="Write engaging stories...",
    temperature=0.85,
    max_tokens=2048
)

# Create task
task = AgentTask(
    task_id="write_story",
    agent_role=AgentRole.WRITER,
    prompt="Write a story about {topic}",
    output_key="content_block"
)

# Execute task
result = await agent.process_task(task=task)

# TODO: show AgentTasks that can generate structured responses as below

# Generated content
story = BranchedNarrative(
    title="Adventure",
    start_node="intro",
    nodes={"intro": StoryNode(...)}
)

# Provided feedback
feedback = Feedback(
    feedback_type=FeedbackType.CLARITY,
    content="Simplify the opening paragraph",
    severity="medium"
)
```

---

## Key Principles

✅ **Type-Safe** - Pydantic validation for all models  
✅ **Composable** - Models reference each other naturally  
✅ **Domain-Driven** - Clear separation (agent/content/editorial)  
✅ **Extensible** - Easy to add new content types or roles

