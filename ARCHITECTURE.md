# Architecture

> Task-based multi-agent content generation system

## Overview

ADK Agentic Writer generates interactive content using coordinated agents. Content types (quiz, story, game, simulation) are aliases that map to tasks published by agents.

```
Frontend (showcase.html) → FastAPI (:8000) → CoordinatorAgent → WriterAgent/DesignerAgent
```

## Directory Structure

```
src/adk_agentic_writer/
├── agents/
│   ├── base_agent.py         # BaseAgent: core agent class
│   ├── stateful_agent.py     # StatefulAgent: state + task execution
│   ├── content_agent.py      # ContentWriterAgent: ContentProtocol
│   ├── static/
│   │   ├── coordinator.py    # Routes content_type → task → agent
│   │   ├── writer.py         # WriterAgent (quiz, story)
│   │   └── designer.py       # DesignerAgent (game, simulation)
│   └── gemini/               # Gemini team (stubs)
├── backend/
│   └── api.py                # FastAPI endpoints
├── models/
│   ├── agent_models.py       # AgentTask, AgentConfig, AgentRole
│   └── content_models.py     # Quiz, Story, Game, Simulation models
├── protocols/
│   ├── agent_protocol.py     # process_task interface
│   └── content_protocol.py   # ContentProtocol (generate_block, etc.)
├── tasks/
│   └── content_tasks.py      # GENERATE_QUIZ, GENERATE_STORY, etc.
└── workflows/                # Orchestration patterns
```

## Core Concepts

### AgentTask

Tasks are the unit of work. Each task has:
- `task_id`: Unique identifier (e.g., "generate_quiz")
- `agent_role`: Role that handles this task (WRITER, DESIGNER)
- `prompt`: Template with `{variable}` substitution
- `content_types`: Aliases that map to this task
- `parameters`: Default parameter values

```python
GENERATE_QUIZ = AgentTask(
    task_id="generate_quiz",
    agent_role=AgentRole.WRITER,
    prompt="Generate a quiz about {topic}",
    content_types=["quiz", "trivia", "test"],
    parameters={"topic": "", "num_questions": 5}
)
```

### Task Discovery

Agents publish tasks via `get_supported_tasks()`. The coordinator aggregates these and builds mappings:

```python
coordinator = CoordinatorAgent()

# Task discovery
tasks = coordinator.get_supported_tasks()
# [GENERATE_QUIZ, GENERATE_STORY, GENERATE_GAME, GENERATE_SIMULATION]

# Content type → Task mapping
coordinator.get_task_for_content_type("trivia")  # Returns GENERATE_QUIZ
coordinator.get_task_for_content_type("rpg")     # Returns GENERATE_GAME

# All content types grouped by task
coordinator.get_all_content_types()
# {"generate_quiz": ["quiz", "trivia", "test"], ...}
```

### Agent Hierarchy

```
BaseAgent (id, role, config)
    ↓
StatefulAgent (state, variables, process_task)
    ↓
ContentWriterAgent (ContentProtocol: generate_text, generate_block)
    ↓
WriterAgent / DesignerAgent (content builders)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page |
| `/showcase` | GET | Content showcase UI |
| `/tasks` | GET | Tasks with content_types |
| `/content-types` | GET | All aliases (flat + grouped) |
| `/generate` | POST | Generate content |
| `/generate/with-review` | POST | Generate with review |
| `/generate/adaptive` | POST | Adaptive workflow |
| `/health` | GET | Health check |

## Data Flow

```
1. Request: POST /generate {content_type: "trivia", topic: "History"}
2. API: coordinator.generate_content("trivia", "History")
3. Coordinator: get_task_for_content_type("trivia") → GENERATE_QUIZ
4. Coordinator: route to WriterAgent
5. WriterAgent: process_task(task, context)
6. WriterAgent: _build_quiz(params) based on task_id
7. Response: {title, questions, ...}
```

## Content Models

| Model | Structure |
|-------|-----------|
| Quiz | `{title, questions: [{question, options, correct_answer}]}` |
| BranchedNarrative | `{title, synopsis, start_node, nodes: {id: {content, branches}}}` |
| QuestGame | `{title, description, nodes: {id: {title, choices, rewards}}}` |
| WebSimulation | `{title, variables, controls, rules}` |

## Protocols

**ContentProtocol** (implemented by ContentWriterAgent):
- `generate_text(prompt_key, context)` → text
- `generate_block(block_type, context)` → ContentBlock
- `generate_patterned_blocks(block_type, pattern, context)` → List[ContentBlock]

**AgentProtocol** (implemented by all agents):
- `process_task(task, parameters)` → Dict
- `update_status(status)` → None
- `get_state()` → AgentState

## Extension

**Add new content type:**
1. Add task in `tasks/content_tasks.py` with `content_types` aliases
2. Import and publish in agent's `get_supported_tasks()`
3. Add builder method in agent (e.g., `_build_newtype()`)
4. Add model in `models/content_models.py`
5. Add UI rendering in `showcase.html`

**Add new agent:**
1. Inherit from `ContentWriterAgent`
2. Implement `generate_block()` and `_build_content()`
3. Register in coordinator
