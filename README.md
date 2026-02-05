# ADK Agentic Writer

> Multi-agent content generation system with task-based orchestration

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

Generate interactive educational content (quizzes, stories, games, simulations) using multi-agent systems.

## Features

**Two Agent Teams**
- **Static Team**: Fast, template-based, no API calls
- **Gemini Team**: AI-powered via Google ADK (coming soon)

**4 Primary Tasks with 15 Content Type Aliases**
- `generate_quiz` → quiz, trivia, test
- `generate_story` → story, narrative, branched_narrative, adventure
- `generate_game` → game, quest_game, quest, rpg
- `generate_simulation` → simulation, web_simulation, interactive, simulator

**Task-Based Architecture**
- Agents publish supported tasks via `get_supported_tasks()`
- API discovers tasks dynamically from coordinator
- Content types are aliases for tasks

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Server

```bash
# Direct
cd src && uvicorn adk_agentic_writer.backend.api:app --reload

# Or with Makefile
make run-backend
```

Server runs at: `http://localhost:8000`

## Project Structure

```
adk-agentic-writer/
├── src/adk_agentic_writer/
│   ├── agents/                # Agent implementations
│   │   ├── base_agent.py      # BaseAgent class
│   │   ├── stateful_agent.py  # StatefulAgent with state management
│   │   ├── content_agent.py   # ContentWriterAgent (ContentProtocol)
│   │   ├── static/            # Static team (WriterAgent, DesignerAgent, Coordinator)
│   │   └── gemini/            # Gemini team (stubs)
│   ├── backend/               # FastAPI server
│   ├── models/                # Pydantic data models
│   ├── protocols/             # Interface definitions
│   ├── tasks/                 # Task templates with content_types
│   └── workflows/             # Orchestration patterns
├── frontend/public/           # Static HTML UI
├── tests/                     # Test suite
└── requirements.txt
```

## Usage

### Web UI

1. Open `http://localhost:8000`
2. Navigate to **Showcase**
3. Select content type (grouped by task)
4. Enter topic and generate

### Python API

```python
from adk_agentic_writer.agents import CoordinatorAgent

# Initialize coordinator (creates WriterAgent + DesignerAgent internally)
coordinator = CoordinatorAgent()

# Discover available tasks
tasks = coordinator.get_supported_tasks()
for task in tasks:
    print(f"{task.task_id}: {task.content_types}")

# Generate content
result = await coordinator.generate_content(
    content_type="quiz",  # Any alias works: trivia, test, etc.
    topic="Python Programming",
    num_questions=5
)
```

### REST API

```bash
# Get available tasks with content type aliases
curl http://localhost:8000/tasks

# Get content types (flat + grouped)
curl http://localhost:8000/content-types

# Generate content
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "team": "static",
    "content_type": "quiz",
    "topic": "Python",
    "parameters": {"num_questions": 5}
  }'

# Health check
curl http://localhost:8000/health
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page |
| `/showcase` | GET | Content showcase UI |
| `/tasks` | GET | Available tasks with content_types |
| `/content-types` | GET | All content type aliases |
| `/generate` | POST | Generate content |
| `/generate/with-review` | POST | Generate with review cycles |
| `/generate/adaptive` | POST | Adaptive generation workflow |
| `/health` | GET | Health check |

## Architecture

```
Request → FastAPI → CoordinatorAgent → WriterAgent/DesignerAgent → Response
                         ↓
              get_task_for_content_type()
                         ↓
                   process_task()
```

**Key Concepts:**
- **AgentTask**: Template with `task_id`, `prompt`, `parameters`, `content_types`
- **content_types**: Aliases that map to tasks (e.g., "trivia" → generate_quiz)
- **Coordinator**: Routes requests to appropriate agent based on content type
- **WriterAgent**: Handles quiz, story (text-based content)
- **DesignerAgent**: Handles game, simulation (structural content)

## Testing

```bash
pytest tests/ -v
```

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture details
- [src/adk_agentic_writer/protocols/README.md](src/adk_agentic_writer/protocols/README.md) - Protocol interfaces
- [src/adk_agentic_writer/models/README.md](src/adk_agentic_writer/models/README.md) - Data models
- [src/adk_agentic_writer/tasks/README.md](src/adk_agentic_writer/tasks/README.md) - Task definitions

## License

MIT License - see [LICENSE](LICENSE) for details.
