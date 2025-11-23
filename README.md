# ADK Agentic Writer

> Multi-agent content generation system with strategic orchestration

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)

Generate interactive educational content (quizzes, stories, games, simulations) using AI-powered multi-agent systems.

---

## Features

✅ **Two Agent Teams**
- **Static Team**: Fast, template-based, no API calls
- **Gemini Team**: AI-powered via Google ADK, high quality

✅ **4 Content Types**
- Interactive Quizzes
- Branched Narratives
- Quest Games
- Web Simulations

✅ **9 Coordinator Tasks** (Gemini)
- Generate Quiz/Story/Game/Simulation
- Review/Refine/Validate Content
- Complete Workflow (Generate → Review → Refine)
- **Multimodal Generation** (4 strategies: Sequential, Loop, Conditional, Adaptive)

✅ **Quality Control**
- Editorial models for feedback tracking
- Automated review and refinement
- Quality metrics and validation

✅ **Strategic Orchestration**
- AI-driven planning via Google ADK
- Supportive coordination pattern
- Iterative refinement workflows

---

## Quick Start

### 1. Install Dependencies

```bash
# Backend
pip install -r requirements.txt

# For Gemini team (optional)
pip install google-adk

# Frontend
cd frontend
npm install
```

### 2. Configure API Key (for Gemini team)

```bash
# Create .env file
echo "GOOGLE_API_KEY=your-api-key-here" > .env
```

### 3. Run Backend

```bash
# From project root
python -m src.adk_agentic_writer.backend.api

# Or with uvicorn
uvicorn src.adk_agentic_writer.backend.api:app --reload
```

Backend runs at: `http://localhost:8000`

### 4. Run Frontend

```bash
cd frontend
npm start
```

Frontend runs at: `http://localhost:3000`

---

## Usage

### Web UI

1. Open `http://localhost:3000`
2. **Select Agent Team**: Choose Static (fast) or Gemini (AI-powered)
3. **Select Content Type**: Quiz, Story, Game, or Simulation
4. **Enter Topic**: e.g., "Ancient Rome", "Climate Change"
5. **Generate**: Click to create content

### Python API

#### Static Team

```python
from adk_agentic_writer.agents.static import (
    CoordinatorAgent,
    StaticQuizWriterAgent,
    ReviewerAgent
)

# Initialize
coordinator = CoordinatorAgent()
coordinator.register_agent(StaticQuizWriterAgent())
coordinator.register_agent(ReviewerAgent())

# Generate
result = await coordinator.process_task(
    "Generate quiz",
    {
        "content_type": "quiz",
        "topic": "Python Programming",
        "num_questions": 10
    }
)
```

#### Gemini Team

```python
from adk_agentic_writer.agents.gemini import (
    GeminiCoordinatorAgent,
    GeminiQuizWriterAgent,
    GeminiReviewerAgent,
    SupportedTask
)

# Initialize
coordinator = GeminiCoordinatorAgent()
coordinator.register_agent(GeminiQuizWriterAgent())
coordinator.register_agent(GeminiReviewerAgent())

# Simple generation
result = await coordinator.process_task(
    "Generate quiz",
    {
        "task": SupportedTask.GENERATE_QUIZ,
        "topic": "Machine Learning",
        "num_questions": 15
    }
)

# Complete workflow (Generate → Review → Refine)
result = await coordinator.process_task(
    "Generate with quality control",
    {
        "task": SupportedTask.COMPLETE_WORKFLOW,
        "content_type": "quiz",
        "topic": "Data Science",
        "num_questions": 20
    }
)

# Multimodal generation
result = await coordinator.process_task(
    "Create learning module",
    {
        "task": SupportedTask.GENERATE_MULTIMODAL,
        "topic": "Web Development",
        "content_strategy": "sequential",
        "components": [
            {"type": "story", "purpose": "introduction"},
            {"type": "quiz", "purpose": "assessment", "num_questions": 10},
            {"type": "simulation", "purpose": "practice"}
        ],
        "quality_threshold": 85.0
    }
)
```

### REST API

```bash
# Generate with Static team
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "team": "static",
    "content_type": "quiz",
    "topic": "Python",
    "parameters": {"num_questions": 10}
  }'

# Generate with Gemini team
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "team": "gemini",
    "content_type": "quiz",
    "topic": "Machine Learning",
    "parameters": {"num_questions": 15, "difficulty": "medium"}
  }'

# Check available teams
curl http://localhost:8000/teams

# Health check
curl http://localhost:8000/health
```

---

## Architecture

```
src/adk_agentic_writer/
├── protocols/          # Interface definitions
│   ├── agent_protocol.py
│   ├── editorial_protocol.py
│   └── content_protocol.py
├── models/             # Data structures
│   ├── agent_models.py
│   ├── content_models.py
│   └── editorial_models.py
├── workflows/          # Orchestration patterns
│   ├── agent_workflows.py
│   ├── editorial_workflows.py
│   └── content_workflows.py
└── agents/             # Agent implementations
    ├── base_agent.py   # Single base for all agents
    ├── static/         # Template-based (6 agents)
    └── gemini/         # AI-powered (6 agents)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.

---

## Comparison: Static vs Gemini

| Feature | Static Team | Gemini Team |
|---------|-------------|-------------|
| **Speed** | ⚡ Fast | 🐢 Moderate |
| **Quality** | ✅ Good | 🌟 Excellent |
| **Creativity** | 📋 Template-based | 🎨 AI-powered |
| **API Calls** | ❌ None | ✅ Required |
| **Cost** | 💰 Free | 💳 API costs |
| **Use Case** | Testing, prototyping | Production, high-quality |
| **Tasks** | Basic orchestration | 9 specialized tasks |
| **Multimodal** | ❌ No | ✅ Yes (4 strategies) |

**Choose Static** for: Fast prototyping, testing, no API costs
**Choose Gemini** for: Production, high-quality, creative content

---

## Live Demo

Try the interactive showcase (no server needed):
```bash
start frontend/public/showcase.html  # Windows
open frontend/public/showcase.html   # Mac/Linux
```

Features:
- Real-time agent logs
- All 4 content types
- Minimalistic rendering
- Works offline!

---

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contributing guidelines

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/adk_agentic_writer

# Run specific test
pytest tests/unit/test_quiz_writer.py
```

---

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

---

## Project Structure

```
adk-agentic-writer/
├── src/adk_agentic_writer/    # Main package
├── frontend/                   # React UI
├── examples/                   # Usage examples
├── tests/                      # Test suite
├── requirements.txt            # Dependencies
├── README.md                   # This file
└── ARCHITECTURE.md             # Architecture docs
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Support

- 🐛 [Issue Tracker](https://github.com/yourusername/adk-agentic-writer/issues)
- 💬 [Discussions](https://github.com/yourusername/adk-agentic-writer/discussions)

---

## Acknowledgments

Built with:
- [Google ADK](https://github.com/google/adk) - Agent Development Kit
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://reactjs.org/) - Frontend framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation

---

Made with ❤️ by the ADK Agentic Writer team
