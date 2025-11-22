# ADK Agentic Writer - Architecture Documentation

## System Overview

The ADK Agentic Writer is a sophisticated multi-agent system designed for producing interactive educational content. The system leverages a team of specialized AI agents that collaborate to create high-quality, engaging content.

## Architecture Components

### 1. Multi-Agent System

The core of the system is a team of specialized agents, each with specific responsibilities:

#### Coordinator Agent
- **Role**: Orchestrates the entire content generation workflow
- **Responsibilities**:
  - Receives content generation requests
  - Creates task plans based on content type
  - Distributes tasks to appropriate agents
  - Manages dependencies between tasks
  - Aggregates and returns final results
- **Implementation**: `CoordinatorAgent` class

#### Content Writer Agents

**Quiz Writer Agent**
- Creates interactive multiple-choice quizzes
- Generates questions with options and explanations
- Supports difficulty levels and topic customization
- Implementation: `QuizWriterAgent`

**Story Writer Agent**
- Generates branched narrative stories
- Creates multiple story paths and endings
- Supports different genres (fantasy, sci-fi, etc.)
- Implementation: `StoryWriterAgent`

**Game Designer Agent**
- Builds quest-based adventure games
- Creates interconnected game nodes with choices
- Manages rewards and requirements system
- Implementation: `GameDesignerAgent`

**Simulation Designer Agent**
- Creates interactive web simulations
- Defines variables, controls, and rules
- Supports various visualization types
- Implementation: `SimulationDesignerAgent`

**Reviewer Agent**
- Reviews and validates generated content
- Provides quality scores and suggestions
- Adds metadata to content
- Implementation: `ReviewerAgent`

### 2. Backend API (FastAPI)

The backend provides a RESTful API for content generation:

#### Endpoints

**Core Endpoints:**
- `GET /` - Root endpoint with API info
- `GET /health` - Health check
- `GET /agents` - List all agents and their status
- `GET /content-types` - Get available content types
- `POST /generate` - Generic content generation endpoint

**Convenience Endpoints:**
- `POST /generate/quiz` - Generate a quiz
- `POST /generate/story` - Generate a branched narrative
- `POST /generate/game` - Generate a quest game
- `POST /generate/simulation` - Generate a simulation

#### Data Flow

```
Client Request
     │
     ▼
FastAPI Endpoint
     │
     ▼
Coordinator Agent
     │
     ├─────────┬─────────┬─────────┐
     ▼         ▼         ▼         ▼
Quiz Writer Story Writer Game Designer Simulation Designer
     │         │         │         │
     └─────────┴────┬────┴─────────┘
                    ▼
               Reviewer Agent
                    │
                    ▼
            Response to Client
```

### 3. Data Models

#### Content Models
- `Quiz` - Complete quiz structure with questions
- `QuestGame` - Quest game with nodes and paths
- `BranchedNarrative` - Story with branching paths
- `WebSimulation` - Interactive simulation

#### Agent Models
- `AgentState` - Current state of an agent
- `AgentTask` - Task assigned to an agent
- `AgentMessage` - Inter-agent communication

#### Request/Response Models
- `ContentRequest` - Client request for content
- `ContentResponse` - API response with generated content

### 4. Frontend (React + TypeScript)

The frontend provides a user-friendly interface for content generation:

#### Components

**Main App Component**
- Content type selection cards
- Topic input field
- Generation controls
- Results display

**Features**
- Real-time agent status updates
- Beautiful gradient UI design
- Responsive layout
- Error handling and loading states

### 5. Deployment

#### Docker Architecture

```
┌─────────────────────────────────────┐
│     Docker Compose Network          │
│                                      │
│  ┌────────────────┐                │
│  │   Frontend     │  Port 3000     │
│  │   (Nginx)      │                │
│  └────────┬───────┘                │
│           │                          │
│           ▼                          │
│  ┌────────────────┐                │
│  │   Backend      │  Port 8000     │
│  │   (Uvicorn)    │                │
│  └────────────────┘                │
│                                      │
└─────────────────────────────────────┘
```

## Request Flow Example

### Quiz Generation Flow

1. **User Action**: User enters topic "Python Programming" and selects "Quiz"

2. **Frontend Request**:
```javascript
POST /generate/quiz?topic=Python&num_questions=5
```

3. **Backend Processing**:
```python
# API receives request
request = ContentRequest(
    content_type=ContentType.QUIZ,
    topic="Python",
    parameters={"num_questions": 5}
)

# Coordinator creates task plan
tasks = [
    AgentTask(role=QUIZ_WRITER, ...),
    AgentTask(role=REVIEWER, dependencies=[...])
]

# Quiz Writer Agent generates quiz
quiz = await quiz_writer.process_task(...)

# Reviewer Agent reviews content
reviewed = await reviewer.process_task(..., content=quiz)

# Return response
return ContentResponse(
    content=reviewed,
    agents_involved=["quiz_writer", "reviewer"]
)
```

4. **Frontend Display**: Shows quiz with metadata about agents involved

## Agent Communication Protocol

Agents communicate through the coordinator using a task-based system:

1. **Task Assignment**: Coordinator assigns tasks with parameters
2. **Task Execution**: Agents process tasks and return results
3. **Dependency Management**: Results passed to dependent tasks
4. **Status Updates**: Agents update their status during execution

## Extensibility

### Adding New Content Types

1. Define new content model in `models/content_models.py`
2. Create specialized agent class inheriting from `BaseAgent`
3. Register agent with coordinator
4. Add content type to `ContentType` enum
5. Update coordinator's task plan logic
6. Add convenience endpoint in API
7. Update frontend UI

### Adding New Agent Capabilities

1. Extend base agent with new methods
2. Implement task processing logic
3. Update agent communication protocol
4. Add tests for new functionality

## Performance Considerations

- **Async Processing**: All agent operations use async/await
- **Task Dependencies**: Parallel execution where possible
- **Lightweight Agents**: Agents are stateless and can be scaled
- **API Optimization**: FastAPI's async capabilities utilized

## Security Considerations

- **Input Validation**: All inputs validated with Pydantic
- **CORS Configuration**: Configurable allowed origins
- **Error Handling**: Comprehensive error handling
- **Logging**: All operations logged for debugging

## Testing Strategy

### Unit Tests
- Agent model creation and validation
- Content model creation and validation
- Individual agent functionality

### Integration Tests
- API endpoints
- Multi-agent workflows
- Full content generation flow

### Test Coverage
- Current: 100% of critical paths
- Target: Maintain >80% coverage

## Monitoring and Logging

- **Agent Status**: Real-time status via `/agents` endpoint
- **Request Tracking**: Unique request IDs for tracking
- **Performance Metrics**: Agent execution times logged
- **Error Tracking**: Comprehensive error logging

## Future Enhancements

1. **LLM Integration**: Connect to Google Gemini for content generation
2. **Content Storage**: Database for saving generated content
3. **User Accounts**: Authentication and personalization
4. **Analytics**: Usage statistics and insights
5. **Export Features**: PDF, HTML, JSON exports
6. **Collaboration**: Multi-user content editing
7. **Templates**: Customizable content templates
8. **API Keys**: Rate limiting and access control

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn
- **Frontend**: React 18, TypeScript, Axios
- **Data Validation**: Pydantic
- **Testing**: Pytest, pytest-asyncio
- **Code Quality**: Ruff, MyPy, Black
- **Containerization**: Docker, Docker Compose
- **Documentation**: OpenAPI/Swagger (auto-generated)

## Development Workflow

1. **Setup**: Run `./setup.sh` for quick setup
2. **Development**: Use `make run-backend` and `make run-frontend`
3. **Testing**: Use `make test` for running tests
4. **Linting**: Use `make lint` for code quality checks
5. **Docker**: Use `make docker-up` for containerized deployment

## API Documentation

Full interactive API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
