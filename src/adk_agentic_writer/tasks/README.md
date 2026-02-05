# Tasks

Task templates with content type aliases for discovery.

## Overview

**AgentTask** defines a unit of work with:
- `task_id`: Unique identifier
- `agent_role`: Role that handles this task (WRITER, DESIGNER)
- `prompt`: Template with `{variable}` substitution
- `content_types`: Aliases for API/UI discovery
- `parameters`: Default values
- `output_key`: State variable for result

## Primary Tasks

Tasks published by agents via `get_supported_tasks()`:

| Task | Agent | Content Types (Aliases) |
|------|-------|------------------------|
| `GENERATE_QUIZ` | WRITER | quiz, trivia, test |
| `GENERATE_STORY` | WRITER | story, narrative, branched_narrative, adventure |
| `GENERATE_GAME` | DESIGNER | game, quest_game, quest, rpg |
| `GENERATE_SIMULATION` | DESIGNER | simulation, web_simulation, interactive, simulator |

### Task Discovery

```python
from adk_agentic_writer.agents import CoordinatorAgent

coordinator = CoordinatorAgent()

# Get all tasks with content_types
for task in coordinator.get_supported_tasks():
    print(f"{task.task_id}: {task.content_types}")

# Get task for a content type alias
task = coordinator.get_task_for_content_type("trivia")  # GENERATE_QUIZ
task = coordinator.get_task_for_content_type("rpg")     # GENERATE_GAME
```

## Block-Level Tasks

Internal tasks for granular control:

- `GENERATE_BLOCK` - Single content unit
- `GENERATE_SEQUENTIAL_BLOCKS` - Linear sequence
- `GENERATE_LOOPED_BLOCKS` - Repeatable with exit
- `GENERATE_BRANCHED_BLOCKS` - Choice-based
- `GENERATE_CONDITIONAL_BLOCKS` - State-based

## Editorial Tasks

Refinement and quality:

- `REVIEW_CONTENT` - Generate feedback
- `VALIDATE_CONTENT` - Check requirements
- `REFINE_CONTENT` - Improve based on feedback

## Usage

```python
from adk_agentic_writer.tasks import GENERATE_QUIZ, GENERATE_STORY

# Task properties
GENERATE_QUIZ.task_id        # "generate_quiz"
GENERATE_QUIZ.agent_role     # AgentRole.WRITER
GENERATE_QUIZ.content_types  # ["quiz", "trivia", "test"]
GENERATE_QUIZ.parameters     # {"topic": "", "num_questions": 5}

# Import specific task
from adk_agentic_writer.tasks.content_tasks import GENERATE_GAME
```

## Key Principles

- **Discoverable**: Tasks publish content_types for API/UI
- **Aliased**: Multiple content types map to one task
- **Templated**: Prompts use `{variable}` substitution
- **Type-safe**: Pydantic validation
