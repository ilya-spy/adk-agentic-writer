# Architecture

> Task-based multi-agent content generation system with Google ADK integration

## Overview

ADK Agentic Writer generates interactive content using coordinated agents. Content types (quiz, story, game, simulation) are aliases that map to tasks published by agents. Two agent teams are available: a fast static/template team and an AI-powered Gemini team.

```
Frontend (showcase.html) → FastAPI (:8000) → CoordinatorAgent → WriterAgent / DesignerAgent
                                                                       ↓ (Gemini team)
                                                                 ADKAgentWrapper → Gemini LLM
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
│   └── gemini/
│       ├── coordinator.py    # Routes to Gemini agents
│       ├── wrapper.py        # ADKAgentWrapper: LLM interaction, JSON parsing, refusal detection
│       ├── writer.py         # GeminiWriterAgent: quiz/story with post-processing
│       └── designer.py       # GeminiDesignerAgent: game/simulation
├── backend/
│   └── api.py                # FastAPI endpoints
├── models/
│   ├── agent_models.py       # AgentTask, AgentConfig, AgentRole
│   └── content_models.py     # Quiz, QuizQuestion, StoryNode, QuestGame, WebSimulation
├── protocols/
│   ├── agent_protocol.py     # process_task interface
│   └── content_protocol.py   # ContentProtocol (generate_block, etc.)
├── tasks/
│   └── content_tasks.py      # GENERATE_QUIZ, GENERATE_STORY, etc.
├── teams/
│   ├── content_team.py       # Agent configs + prompt templates
│   └── editorial_team.py     # Review/refine configs
├── utils/
│   ├── content_registry.py   # Content type configs, schemas, sample outputs
│   ├── schema_helpers.py     # JSON schema extraction utilities
│   └── text_provider.py      # Text generation providers (static, Gemini)
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
| Quiz | `{title, description, difficulty, questions, passing_score, time_limit}` |
| QuizQuestion | `{question, options, correct_answer, explanation, tier, score}` |
| BranchedNarrative | `{title, synopsis, start_node, nodes: {id: {content, branches}}}` |
| StoryNode | `{node_id, content, branches: [{text, target_node_id}], is_ending}` |
| QuestGame | `{title, description, nodes: {id: {title, choices, rewards}}}` |
| WebSimulation | `{title, variables, controls, rules}` |

### Quiz Scoring Model

- **Quiz.difficulty**: Overall quiz difficulty (easy, medium, hard)
- **QuizQuestion.tier**: Per-question scoring tier (low=1pt, mid=2pt, high=3pt)
- Every quiz is enforced to contain all three tiers (low, mid, high)
- Passing score is validated to be within 50-85% of total points

## Protocols

**ContentProtocol** (implemented by ContentWriterAgent):
- `generate_text(prompt_key, context)` → text
- `generate_block(block_type, context)` → ContentBlock
- `generate_patterned_blocks(block_type, pattern, context)` → List[ContentBlock]

**AgentProtocol** (implemented by all agents):
- `process_task(task, parameters)` → Dict
- `update_status(status)` → None
- `get_state()` → AgentState

## Gemini Team Pipeline

```
1. Prompt assembled from content_team.py templates + content_registry.py schema/sample
2. ADKAgentWrapper sends prompt to Gemini LLM via InMemoryRunner
3. Response checked for refusal patterns (→ ValueError if detected)
4. JSON extracted and parsed (resilient: strips markdown fences, fixes trailing commas)
5. Post-processing in writer.py:
   - Quiz: normalize tier/difficulty fields, enforce 3-tier distribution, validate passing_score
   - Story: fuzzy key matching for branch text/target fields, normalize node structure
6. Pydantic model validation (Quiz, BranchedNarrative, etc.)
7. Response returned to API
```

## Extension

**Add new content type:**
1. Add task in `tasks/content_tasks.py` with `content_types` aliases
2. Add config in `utils/content_registry.py` (schema, sample output, prompts)
3. Import and publish in agent's `get_supported_tasks()`
4. Add builder method in agent (e.g., `_build_newtype()`)
5. Add model in `models/content_models.py`
6. Add UI rendering in `showcase.html`

**Add new agent:**
1. Inherit from `ContentWriterAgent`
2. Implement `generate_block()` and `_build_content()`
3. For Gemini: use `ADKAgentWrapper` for LLM interaction
4. Register in coordinator
