# Architecture

> Multi-agent content generation system with Static and Gemini teams

## System Overview

ADK Agentic Writer generates interactive educational content (Quiz, Story, Game, Simulation) using coordinated agents. Two teams: **Static** (template-based, fast) and **Gemini** (AI-powered, quality).

**Key Principles**: Protocol-driven design, single base class, FastAPI backend serves both API and static HTML on port 8000.

---

## Architecture

```
Frontend (Static HTML: index.html, showcase.html, frontend.html)
    ↓
Backend (FastAPI :8000)
    ↓
Agent Teams (Static | Gemini)
    ↓
Protocols + Models + Workflows
```

---

## Directory Structure

```
adk-agentic-writer/
├── src/adk_agentic_writer/
│   ├── protocols/              # Interface definitions
│   │   ├── agent_protocol.py   # AgentProtocol (process_task)
│   │   ├── content_protocol.py # ContentProtocol (UX patterns)
│   │   └── editorial_protocol.py # EditorialProtocol (review/refine)
│   ├── models/                 # Data structures
│   │   ├── agent_models.py     # Agent states, configs, roles
│   │   ├── content_models.py   # Quiz, Story, Game, Simulation
│   │   └── editorial_models.py # Feedback, QualityMetrics, Revisions
│   ├── workflows/              # Orchestration patterns
│   │   ├── base_workflow.py    # Sequential, Parallel, Loop, Conditional
│   │   ├── agent_workflows.py
│   │   ├── editorial_workflows.py
│   │   └── content_workflows.py
│   ├── agents/                 # Agent implementations
│   │   ├── base_agent.py       # Single base class
│   │   ├── static/             # Template-based (6 agents)
│   │   └── gemini/             # AI-powered (6 agents)
│   └── backend/
│       └── api.py              # FastAPI server
├── frontend/public/            # Static HTML files
├── tests/                      # Unit & integration tests
├── requirements.txt
└── requirements-dev.txt
```

---

## Core Components

### Protocols (Interfaces)
- **AgentProtocol**: `process_task(task_description, parameters) -> Dict`
- **EditorialProtocol**: `review_content()`, `refine_content()`, `validate_content()`
- **ContentProtocol**: `stream_content()`, `generate_block()`, `interactive_update()`

### Models
- **Agent**: `AgentRole`, `AgentState`, `AgentStatus`, `AgentMessage`, `AgentTask`
- **Content**: `Quiz`, `BranchedNarrative`, `QuestGame`, `WebSimulation`
- **Editorial**: `Feedback`, `QualityMetrics`, `ContentRevision`, `ValidationResult`

### Agents

**6 Types** × **2 Teams** = **12 Agents**

| Type | Role | Responsibility |
|------|------|----------------|
| Coordinator | COORDINATOR | Orchestrates workflows |
| Quiz Writer | CONTENT_CREATOR | Generates quizzes |
| Story Writer | CONTENT_CREATOR | Generates narratives |
| Game Designer | CONTENT_CREATOR | Generates games |
| Simulation Designer | CONTENT_CREATOR | Generates simulations |
| Reviewer | REVIEWER | Reviews content |

**Teams**:
- **Static** (`agents/static/`): Templates, no API, instant
- **Gemini** (`agents/gemini/`): AI-powered, requires API key, 2-5s

### Backend (FastAPI)

**Endpoints** (port 8000):
- `GET /` → index.html
- `GET /showcase` → showcase.html
- `GET /frontend` → frontend.html
- `POST /generate` → Generate content
- `GET /teams` → List teams
- `GET /health` → Health check
- `GET /docs` → OpenAPI docs

---

## Data Flow

```
1. User Request (HTTP)
2. FastAPI (/generate)
3. Coordinator Agent
4. Specialized Agent (Quiz/Story/Game/Simulation)
5. Optional: Reviewer Agent
6. JSON Response
7. Frontend Rendering
```

---

## Content Types

**Quiz**: `{title, questions: [{question, options, correct_answer, explanation}]}`

**Branched Narrative**: `{title, synopsis, start_node, nodes: {node_id: {content, branches}}}`

**Quest Game**: `{title, description, quests: [{quest_id, objectives, rewards}]}`

**Web Simulation**: `{title, variables, controls, rules, visualization_type}`

---

## Team Comparison

| | Static | Gemini |
|-|--------|--------|
| Speed | ⚡ <100ms | 🐢 2-5s |
| Quality | Good | Excellent |
| Creativity | Template | AI-generated |
| API Key | ❌ | ✅ Required |
| Cost | Free | API costs |
| Tasks | 1 basic | 9 specialized |

---

## Deployment

**Local**:
```bash
pip install -r requirements.txt
uvicorn src.adk_agentic_writer.backend.api:app --reload
# http://localhost:8000
```

**Docker**:
```bash
docker-compose up --build
```

---

## Extension Points

**New Content Type**: Define model → Add to enum → Create agents → Update coordinator → Add frontend rendering

**New Agent**: Inherit BaseAgent → Implement process_task() → Register with coordinator

**New Workflow**: Inherit base pattern → Implement execution logic

---

## Design Decisions

- **Single base class**: Reduces duplication, consistent behavior
- **Protocol-driven**: Clear contracts, type-safe
- **Static HTML frontend**: No build process, simple deployment, one port
- **Two teams**: Fast prototyping (Static) + Production quality (Gemini)

---

Built with FastAPI, Pydantic, and Google ADK.
