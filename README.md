# ADK Agentic Writer

> Multi-agent content generation system powered by Google ADK and task-based orchestration

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-113-brightgreen.svg)]()

Generate interactive educational content (quizzes, stories, games, simulations) using coordinated AI agents.

## Features

**Two Agent Teams**
- **Static Team**: Fast, template-based generation — no API calls required
- **Gemini Team**: AI-powered via Google ADK with real LLM generation, structured JSON output, refusal detection, and post-processing

**4 Primary Tasks with 15 Content Type Aliases**
- `generate_quiz` → quiz, trivia, test
- `generate_story` → story, narrative, branched_narrative, adventure
- `generate_game` → game, quest_game, quest, rpg
- `generate_simulation` → simulation, web_simulation, interactive, simulator

**Quiz Scoring System**
- Overall quiz **difficulty**: easy, medium, hard
- Per-question **scoring tiers**: low (1pt), mid (2pt), high (3pt)
- Deterministic 3-tier enforcement with automatic passing score calculation

**Resilient LLM Integration**
- LLM refusal detection for sensitive/harmful topics
- Fuzzy key normalization for inconsistent LLM output (story branches, quiz fields)
- Post-processing validation with fallback defaults

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

> **Note**: Without an API key, the Gemini team falls back to static templates.

### 3. Run Server

```bash
# From project root
python -m uvicorn adk_agentic_writer.backend.api:app --host 127.0.0.1 --port 8000

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
│   │   └── gemini/            # Gemini team (Writer, Designer, Coordinator, Wrapper)
│   ├── backend/               # FastAPI server
│   ├── models/                # Pydantic data models
│   ├── protocols/             # Interface definitions
│   ├── tasks/                 # Task templates with content_types
│   ├── teams/                 # Agent configs + prompt templates
│   ├── utils/                 # Content registry, schema helpers, text providers
│   └── workflows/             # Orchestration patterns
├── frontend/public/           # Static HTML UI (showcase, home)
├── examples/                  # Interactive demo script
├── tests/                     # 113 tests (unit + integration)
└── requirements.txt
```

## Usage

### Web UI (Showcase)

1. Open `http://localhost:8000/showcase`
2. Select **Team** (Static or Gemini)
3. Select **Content Type** (quiz, story, game, etc.)
4. Enter topic, adjust parameters (difficulty, number of questions, answer options)
5. Click **Generate & Display**

The showcase provides:
- Color-coded generation process logs
- Quiz rendering with tier/score labels per question
- Interactive story navigation with branching choices
- Error/refusal display for blocked topics

### REST API

```bash
# Generate a quiz
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "team": "gemini",
    "content_type": "quiz",
    "topic": "Space Exploration",
    "parameters": {
      "num_questions": 6,
      "difficulty": "hard",
      "num_options": 3
    }
  }'

# Generate a story
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "team": "gemini",
    "content_type": "story",
    "topic": "Haunted lighthouse mystery",
    "parameters": {"num_nodes": 7}
  }'

# Get available tasks with content type aliases
curl http://localhost:8000/tasks

# Get content types (flat + grouped)
curl http://localhost:8000/content-types

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
    content_type="quiz",
    topic="Python Programming",
    num_questions=5,
    difficulty="medium"
)
```

## Architecture

```
Request → FastAPI → CoordinatorAgent → WriterAgent / DesignerAgent → Response
                         ↓                    ↓
              get_task_for_content_type()    ADKAgentWrapper (Gemini)
                         ↓                    ↓
                   process_task()       LLM → JSON parse → validate → post-process
```

**Key Concepts:**
- **AgentTask**: Template with `task_id`, `prompt`, `parameters`, `content_types`
- **content_types**: Aliases that map to tasks (e.g., "trivia" → generate_quiz)
- **Coordinator**: Routes requests to appropriate agent based on content type
- **WriterAgent**: Handles quiz, story (text-based content)
- **DesignerAgent**: Handles game, simulation (structural content)
- **ADKAgentWrapper**: Centralizes Gemini LLM interaction, JSON parsing, and refusal detection

## Gemini Team (ADK-Powered)

The Gemini team uses Google's Agent Development Kit (ADK) for real AI content generation.

### Components

| Module | Purpose |
|--------|---------|
| `gemini/wrapper.py` | ADK agent wrapper — LLM interaction, JSON parsing, refusal detection |
| `gemini/writer.py` | Quiz and story generation with post-processing and validation |
| `gemini/designer.py` | Game and simulation generation |
| `gemini/coordinator.py` | Routes content types to Gemini agents |

### Features

- **Real AI Generation**: Uses Gemini LLM for creative, engaging content
- **Structured Output**: JSON schema validation for consistent responses
- **InMemoryRunner**: Fast session management without persistence
- **LLM Refusal Detection**: Catches safety refusals before JSON parsing fails
- **3-Tier Quiz Scoring**: Enforces low/mid/high tier distribution across questions
- **Fuzzy Key Matching**: Normalizes inconsistent LLM output keys for story branches
- **Graceful Fallback**: Falls back to static templates if API unavailable

### Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `GOOGLE_API_KEY` | Google AI Studio API key | (required for ADK) |
| `GEMINI_MODEL` | Model to use | `gemini-2.5-flash-lite` |

## Testing

```bash
# Run all 113 tests
pytest tests/ -v

# Unit tests only (fast, no API)
pytest tests/unit/ -v

# Integration tests (requires GOOGLE_API_KEY for live LLM tests)
pytest tests/integration/ -v

# Skip slow LLM tests
pytest -m "not slow"
```

Tests cover: content models, agent behavior, quiz tier enforcement, story branch normalization, API endpoints, Gemini generation with various difficulty/option configurations, and static team output.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — System architecture details
- [src/adk_agentic_writer/models/README.md](src/adk_agentic_writer/models/README.md) — Data models
- [src/adk_agentic_writer/teams/README.md](src/adk_agentic_writer/teams/README.md) — Team configs and prompts
- [src/adk_agentic_writer/protocols/README.md](src/adk_agentic_writer/protocols/README.md) — Protocol interfaces
- [src/adk_agentic_writer/tasks/README.md](src/adk_agentic_writer/tasks/README.md) — Task definitions
- [src/adk_agentic_writer/workflows/README.md](src/adk_agentic_writer/workflows/README.md) — Orchestration patterns
- [tests/README.md](tests/README.md) — Testing guide

## License

MIT License — see [LICENSE](LICENSE) for details.
