# Quick Start

> Get running in 5 minutes

## Installation

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Optional: Configure Gemini team
echo "GOOGLE_API_KEY=your-key" > .env
```

---

## Run

```bash
# Method 1: Makefile
make run-backend

# Method 2: Direct
uvicorn src.adk_agentic_writer.backend.api:app --reload --host 0.0.0.0 --port 8000

# Method 3: Docker
docker-compose up --build
```

**Access**: http://localhost:8000

---

## Usage

### Web UI
1. Open http://localhost:8000
2. Choose team (Static/Gemini)
3. Select content type
4. Enter topic
5. Generate

### REST API

```bash
# Generate Quiz
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "team": "static",
    "content_type": "quiz",
    "topic": "Python",
    "parameters": {"num_questions": 5}
  }'

# Check teams
curl http://localhost:8000/teams
```

### Python API

**Static Team**:
```python
from src.adk_agentic_writer.agents.static import CoordinatorAgent, StaticQuizWriterAgent

coordinator = CoordinatorAgent()
coordinator.register_agent(StaticQuizWriterAgent())

result = await coordinator.process_task(
    "Generate quiz",
    {"content_type": "quiz", "topic": "Python", "num_questions": 10}
)
```

**Gemini Team**:
```python
from src.adk_agentic_writer.agents.gemini import GeminiCoordinatorAgent, GeminiQuizWriterAgent, SupportedTask

coordinator = GeminiCoordinatorAgent()
coordinator.register_agent(GeminiQuizWriterAgent())

result = await coordinator.process_task(
    "Generate quiz",
    {"task": SupportedTask.GENERATE_QUIZ, "topic": "ML", "num_questions": 15}
)
```

---

## Content Types

| Type | Parameters |
|------|------------|
| **Quiz** | `num_questions`, `difficulty` |
| **Branched Narrative** | `genre`, `num_nodes` |
| **Quest Game** | `num_quests`, `difficulty` |
| **Web Simulation** | `num_variables`, `visualization_type` |

---

## Teams

| | Static | Gemini |
|-|--------|--------|
| Speed | Instant | 2-5 sec |
| Quality | Good | Excellent |
| API Key | Not needed | Required |
| Use for | Testing | Production |

---

## Makefile Commands

```bash
make run-backend    # Run server
make test           # Run tests
make lint           # Run linters
make format         # Format code
make docker-up      # Docker start
make clean          # Clean artifacts
```

---

## Troubleshooting

**Port 8000 in use**:
```bash
uvicorn src.adk_agentic_writer.backend.api:app --port 8080
```

**Gemini unavailable**: Check `GOOGLE_API_KEY` in `.env`

**Import errors**:
```bash
pip install -e .
```

---

## Testing

```bash
pytest                                    # Run all
pytest --cov=src/adk_agentic_writer      # With coverage
pytest tests/unit/test_quiz_writer.py    # Specific test
```

---

## Next Steps

- 📖 [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- 🤝 [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guide
- 📚 http://localhost:8000/docs - API documentation

---

🚀 Start at http://localhost:8000
