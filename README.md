# ADK Agentic Writer

> Task-driven multi-agent content production system powered by Google ADK

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

Generate interactive educational content (quizzes, stories, games, simulations) using coordinated AI agents with Google's Agent Development Kit.

## Features

- **5 Unified Tasks**: `ideate`, `write`, `review`, `refine`, `publish`
- **4 Content Formats with Flavors**: quiz (trivia, test), story (narrative, adventure), game (quest, rpg), simulation (simulator)
- **Task-driven API**: Single `POST /task/{task_id}` endpoint, auto-discovery via `GET /tasks`
- **Runtime State Store**: Output keys persist between task invocations
- **Robust LLM Integration**: JSON parsing with truncation repair, refusal detection, schema validation fallback

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
cp .env.example .env
# Edit .env: GOOGLE_API_KEY=your_key_from_aistudio.google.com
```

### 3. Run Server

```bash
python -m uvicorn adk_agentic_writer.backend.api:app --host 127.0.0.1 --port 8000
```

Open `http://localhost:8000/showcase` for the interactive UI.

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/task/{task_id}` | POST | Execute a task with parameters |
| `/tasks` | GET | List available tasks with parameter specs |
| `/content-types` | GET | List formats with flavors and parameters |
| `/outputs` | GET | View stored output keys |
| `/outputs/clear` | POST | Clear stored outputs |
| `/supported-outputs` | GET | List all possible output key names |
| `/showcase` | GET | Interactive content showcase UI |
| `/health` | GET | Health check |

### Example

```bash
# Generate a quiz
curl -X POST http://localhost:8000/task/write \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"format": "quiz", "topic": "Python", "num_questions": 5}}'

# Review it (uses stored draft_content)
curl -X POST http://localhost:8000/task/review \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"format": "quiz"}}'
```

### Python API

```python
from adk_agentic_writer.agents import Coordinator

coordinator = Coordinator()

# List tasks
for t in coordinator.get_supported_tasks():
    print(f"{t.task_id}: output={t.output_key}")

# Execute a task
result = await coordinator.process_task("write", {
    "format": "quiz", "topic": "Space", "num_questions": 3
})
```

## Testing

```bash
pytest tests/ -v
```

58 tests covering: response parsing, format registry, flavors, unified tasks, prompt building, schema validation, runtime store, workflow construction, and agent service registration.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.

## License

MIT License
