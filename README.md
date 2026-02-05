# ADK Agentic Writer

> Multi-agent content generation system with task-based orchestration

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

Generate interactive educational content (quizzes, stories, games, simulations) using multi-agent systems.

## Features

**Two Agent Teams**
- **Static Team**: Fast, template-based, no API calls
- **Gemini Team**: AI-powered via Google ADK with real LLM generation

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

### 2. Configure API Key (for Gemini Team)

The Gemini team uses Google's Agent Development Kit (ADK) for real AI generation.

**Get your API key:**
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the generated key

**Set the API key:**

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your key
# GOOGLE_API_KEY=your_api_key_here
```

Or set directly in terminal:
```bash
# Windows PowerShell
$env:GOOGLE_API_KEY="your_api_key_here"

# Linux/macOS
export GOOGLE_API_KEY="your_api_key_here"
```

> **Note**: Without an API key, Gemini team falls back to static templates.

### 3. Run Server

```bash
# Direct
cd src && uvicorn adk_agentic_writer.backend.api:app --reload

# Or with Makefile
make run-backend
```

Server runs at: `http://localhost:8000`

### 4. Run ADK Web UI (Interactive Testing)

For interactive agent testing with the ADK dev interface:

```bash
# From project root, with virtual env activated
cd src/adk_agentic_writer/agents/gemini
adk web --port 8080
```

Access at: `http://localhost:8080`

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

## Gemini Team (ADK-Powered)

The Gemini team uses Google's Agent Development Kit (ADK) for real AI content generation.

### Features

- **Real AI Generation**: Uses Gemini LLM for creative, engaging content
- **Structured Output**: JSON schema validation for consistent responses
- **InMemoryRunner**: Fast session management without persistence
- **Graceful Fallback**: Falls back to static templates if API unavailable

### Usage

```python
from adk_agentic_writer.agents.gemini import GeminiWriterAgent

# Create Gemini-powered writer
writer = GeminiWriterAgent(content_type="quiz")

# Check if ADK is enabled
print(f"ADK enabled: {writer.adk_enabled}")

# Generate content (uses ADK if available, else templates)
result = await writer.process_task(GENERATE_QUIZ, {
    "topic": "Python Programming",
    "num_questions": 5
})
```

### Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `GOOGLE_API_KEY` | Google AI Studio API key | (required for ADK) |
| `GEMINI_MODEL` | Model to use | `gemini-2.5-flash-lite` |

### Testing Gemini Agents

```bash
# Run all tests (fallback mode without API key)
pytest tests/integration/test_gemini_writer.py -v

# Run live tests with API key
GOOGLE_API_KEY=your_key pytest tests/integration/test_gemini_writer.py -v
```

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
