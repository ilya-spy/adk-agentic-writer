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

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      AgentRuntime                           │
│  - Instantiates agents and teams                            │
│  - Manages workflows                                        │
│  - Routes tasks to agents                                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ├─────────────────┬─────────────────┐
                 ▼                 ▼                 ▼
        ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
        │  Team 1        │ │  Team 2        │ │  Team 3        │
        │  Quiz Writers  │ │  Reviewers     │ │  Story Writers │
        └────────┬───────┘ └────────┬───────┘ └────────┬───────┘
                 │                  │                  │
        ┌────────┴────────┐         │         ┌────────┴────────┐
        ▼                 ▼         ▼         ▼                 ▼
   ┌─────────┐      ┌─────────┐ ┌─────────┐ ┌─────────┐  ┌─────────┐
   │ Agent 1 │      │ Agent 2 │ │ Agent 3 │ │ Agent 4 │  │ Agent 5 │
   └─────────┘      └─────────┘ └─────────┘ └─────────┘  └─────────┘
```

## StatefulAgent Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     StatefulAgent                            │
├──────────────────────────────────────────────────────────────┤
│  State Management:                                           │
│  ┌────────────────┐  ┌────────────────┐                      │
│  │   Variables    │  │   Parameters   │                      │
│  │  (runtime)     │  │  (config)      │                      │
│  ├────────────────┤  ├────────────────┤                      │
│  │ content_block  │  │ topic          │                      │
│  │ feedback       │  │ num_questions  │                      │
│  │ content_stream │  │ difficulty     │                      │
│  │ review_result  │  │ passing_score  │                      │
│  └────────────────┘  └────────────────┘                      │
├──────────────────────────────────────────────────────────────┤
│  Protocol Implementation:                                    │
│  • AgentProtocol: process_task, update_status, get_state     │
│  • ContentProtocol: generate_block, generate_sequential...   │
│  • EditorialProtocol: validate_content, refine_content       │
├──────────────────────────────────────────────────────────────┤
│  Task Execution:                                             │
│  1. Receive AgentTask                                        │
│  2. Substitute {variables} in prompt                         │
│  3. Validate requirements                                    │
│  4. Execute task logic                                       │
│  5. Store result in variables[output_key]                    │
│  6. Update status                                            │
└──────────────────────────────────────────────────────────────┘
```

## Task-Based Execution Flow

```
┌─────────────┐
│  AgentTask  │
│             │
│ task_id     │──────┐
│ agent_role  │      │
│ prompt      │      │  "Generate quiz about {topic}"
│ parameters  │      │
│ output_key  │      │
└─────────────┘      │
                     ▼
              ┌──────────────────┐
              │ Variable         │
              │ Substitution     │
              └────────┬─────────┘
                       │
                       │  "Generate quiz about Python"
                       ▼
              ┌──────────────────┐
              │ Task Handler     │
              │ (_execute_task)  │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Protocol Method  │
              │ (generate_block) │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Store Result     │
              │ variables[       │
              │   output_key     │
              │ ]                │
              └──────────────────┘
```

## ContentProtocol Patterns

```
┌────────────────────────────────────────────────────────────┐
│                  ContentProtocol Methods                   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  1. Sequential Blocks                                      │
│     Block 1 → Block 2 → Block 3 → Block 4                  │
│     Use: Chapters, tutorials, linear stories               │
│                                                            │
│  2. Looped Blocks                                          │
│     ┌─→ Block 1 → Block 2 → Block 3 ─┐                     │
│     │                                  │                   │
│     └──────── (until condition) ←─────┘                    │
│     Use: Practice mode, mini-games, drills                 │
│                                                            │
│  3. Branched Blocks                                        │
│            Block 1 (choice point)                          │
│              ├─→ Block 2a (path A)                         │
│              ├─→ Block 2b (path B)                         │
│              └─→ Block 2c (path C)                         │
│     Use: Adaptive difficulty, story branches               │
│                                                            │
│  4. Conditional Blocks                                     │
│     Block 1 [if score > 80]                                │
│     Block 2 [if completed prerequisite]                    │
│     Block 3 [if achievement unlocked]                      │
│     Use: Bonus content, achievements, prerequisites        │
│                                                            │
│  5. Mixed Patterns                                         │
│     Combine above for complex narratives                   │
│     Sequential → Branched → Looped → Conditional           │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## Data Flow Example

```
1. User Request
   ↓
   topic: "Python"
   num_questions: 5
   difficulty: "medium"

2. AgentRuntime
   ↓
   Creates/retrieves agent
   Sets parameters

3. StatefulAgent
   ↓
   agent.parameters = {
     "topic": "Python",
     "num_questions": 5,
     "difficulty": "medium"
   }

4. Task Execution
   ↓
   task.prompt = "Generate quiz about {topic}"
   resolved = "Generate quiz about Python"

5. ContentProtocol
   ↓
   generate_block(
     block_type=QUESTION,
     context=parameters
   )

6. Result Storage
   ↓
   agent.variables["content_block"] = quiz_data

7. Return to User
   ↓
   {
     "title": "Python Quiz",
     "questions": [...],
     "passing_score": 70
   }
```

## Workflow Integration

```
┌─────────────────────────────────────────────────────────┐
│                    Workflow Types                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  SEQUENTIAL: Agent A → Agent B → Agent C                │
│  ├─ Generate → Review → Refine                          │
│  └─ Each output feeds into next                         │
│                                                         │
│  PARALLEL: [Agent A, Agent B, Agent C] → Merge          │
│  ├─ Generate 3 variants simultaneously                  │
│  └─ Select best or combine                              │
│                                                         │
│  LOOP: Agent → Check → Agent → Check → Done             │
│  ├─ Iterative refinement                                │
│  └─ Until quality threshold met                         │
│                                                         │
│  CONDITIONAL: Condition → [Agent A | Agent B | Agent C] │
│  ├─ Route based on content type                         │
│  └─ Different strategies per type                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Team Collaboration

```
┌──────────────────────────────────────────────────────────┐
│                  Quiz Writers Team                       │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Team Metadata:                                          │
│  - name: "quiz_writers_pool"                             │
│  - scope: CONTENT                                        │
│  - roles: [QUIZ_WRITER, QUIZ_WRITER]                     │
│                                                          │
│  ┌─────────────────┐      ┌─────────────────┐            │
│  │  Quiz Writer 1  │      │  Quiz Writer 2  │            │
│  │                 │      │                 │            │
│  │  Variables:     │      │  Variables:     │            │
│  │  - content_1    │      │  - content_2    │            │
│  │                 │      │                 │            │
│  │  Parameters:    │      │  Parameters:    │            │
│  │  - topic: "ML"  │      │  - topic: "AI"  │            │
│  └─────────────────┘      └─────────────────┘            │
│                                                          │
│  Coordination:                                           │
│  - Runtime assigns tasks to available agents             │
│  - Agents work independently                             │
│  - Results merged by workflow                            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Usage Patterns

### Pattern 1: Simple Generation
```python
agent = StaticQuizWriterAgent("quiz_1")
agent.update_parameters({"topic": "Python", "num_questions": 5})
result = await agent.process_task(GENERATE_BLOCK)
```

### Pattern 2: With Runtime
```python
runtime = AgentRuntime()
team = runtime.create_team(QUIZ_WRITERS_POOL, configs)
result = await runtime.execute_task_with_agent(
    team[0].agent_id, task, params
)
```

### Pattern 3: Sequential Workflow
```python
# Generate
quiz = await agent.process_task(GENERATE_TASK)

# Validate
is_valid = await agent.validate_content(quiz)

# Refine
refined = await agent.refine_content(quiz, feedback)
```

## Extension Points

**New Content Type**: Define model → Add to enum → Create agents → Update coordinator → Add frontend rendering

**New Agent**: Inherit BaseAgent → Implement process_task() → Register with coordinator

**New Workflow**: Inherit base pattern → Implement execution logic

---

Built with FastAPI, Pydantic, and Google ADK.
