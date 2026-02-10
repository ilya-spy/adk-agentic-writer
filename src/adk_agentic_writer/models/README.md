# Models

Type-safe data models for agents, tasks, and content.

## Overview

- **Agent Models**: Configuration, tasks, state, roles
- **Content Models**: Quiz, Story, Game, Simulation structures
- **Editorial Models**: Review, feedback, quality metrics

## Agent Models (`agent_models.py`)

### Core Types

| Model | Purpose |
|-------|---------|
| `AgentConfig` | Agent configuration (role, instructions, params) |
| `AgentTask` | Task with prompt, content_types, parameters |
| `AgentState` | Runtime state (status, variables) |
| `AgentModel` | Agent model config (name, parameters) |

### AgentTask

Central model for task-based architecture:

```python
class AgentTask(BaseModel):
    task_id: str                    # "generate_quiz"
    agent_role: AgentRole           # WRITER, DESIGNER
    prompt: str                     # "Generate quiz about {topic}"
    parameters: Dict[str, Any]      # {"topic": "", "num_questions": 5}
    content_types: List[str]        # ["quiz", "trivia", "test"]
    output_key: Optional[str]       # "content"
```

### AgentRole Enum

```python
class AgentRole(str, Enum):
    COORDINATOR = "coordinator"
    WRITER = "writer"
    DESIGNER = "designer"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    REFINER = "refiner"
    ANALYZER = "analyzer"
    STRATEGIST = "strategist"
    STREAMER = "streamer"
```

## Content Models (`content_models.py`)

### Content Structures

| Model | Fields |
|-------|--------|
| `Quiz` | title, description, **difficulty**, questions, passing_score, time_limit, metadata |
| `QuizQuestion` | question, options, correct_answer, explanation, **tier**, **score** |
| `BranchedNarrative` | title, synopsis, start_node, nodes |
| `StoryNode` | node_id, content, branches, is_ending |
| `QuestGame` | title, description, start_node, nodes |
| `QuestNode` | node_id, title, choices, rewards, requirements |
| `WebSimulation` | title, variables, controls, rules |

### Quiz Scoring

- **`Quiz.difficulty`**: Overall quiz difficulty — `easy`, `medium`, or `hard`
- **`QuizQuestion.tier`**: Scoring tier — `low` (1pt), `mid` (2pt), or `high` (3pt)
- **`QuizQuestion.score`**: Point value matching the tier (1, 2, or 3)
- Every quiz must contain all three tiers; post-processing enforces this

### Block Types

```python
class ContentBlockType(str, Enum):
    SCENE = "scene"
    CARD = "card"
    CHAPTER = "chapter"
    SECTION = "section"
    SLIDE = "slide"
    QUESTION = "question"
    NODE = "node"
    CUSTOM = "custom"

class ContentPattern(str, Enum):
    SEQUENTIAL = "sequential"
    LOOPED = "looped"
    BRANCHED = "branched"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"
```

## Usage

```python
from adk_agentic_writer.models import (
    AgentTask, AgentRole, AgentConfig,
    Quiz, BranchedNarrative,
    ContentBlockType, ContentPattern
)

# Create task with content_types
task = AgentTask(
    task_id="generate_quiz",
    agent_role=AgentRole.WRITER,
    prompt="Generate quiz about {topic}",
    content_types=["quiz", "trivia", "test"],
    parameters={"topic": "", "num_questions": 5}
)

# Content structure
quiz = Quiz(
    title="Python Quiz",
    description="Test your Python knowledge",
    difficulty="medium",
    questions=[...],
    passing_score=8
)
```

## Key Principles

- **Type-Safe**: Pydantic validation
- **Task-Centric**: AgentTask with content_types for discovery
- **Composable**: Models reference each other
- **Extensible**: Easy to add content types
