# 🤖 ADK Agentic Writer

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-blue.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A comprehensive multi-agentic system for interactive content production, built with the Google Agent Development Kit. This project demonstrates a team of specialized AI agents working together to create engaging educational content including quizzes, quest games, branched narratives, and interactive simulations.

## 🌟 Features

- **Multi-Agent Architecture**: Coordinated team of specialized agents
  - Coordinator Agent: Orchestrates the entire content generation process
  - Quiz Writer Agent: Creates interactive quizzes with multiple choice questions
  - Story Writer Agent: Generates branched narratives with multiple endings
  - Game Designer Agent: Builds quest-based adventure games
  - Simulation Designer Agent: Creates interactive web simulations
  - Reviewer Agent: Reviews and improves content quality

- **Content Types**:
  - 📝 **Quizzes**: Interactive multiple-choice quizzes with explanations
  - 🎮 **Quest Games**: Choice-driven adventure games with rewards and requirements
  - 📖 **Branched Narratives**: Non-linear stories with multiple paths and endings
  - 🔬 **Web Simulations**: Interactive simulations with variables and controls

- **Modern Tech Stack**:
  - Backend: FastAPI (Python 3.11+)
  - Frontend: React with TypeScript
  - Containerization: Docker & Docker Compose
  - API Documentation: Auto-generated with OpenAPI/Swagger

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (React)                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │   Quiz UI  │  │  Story UI  │  │   Game UI  │             │
│  └────────────┘  └────────────┘  └────────────┘             │
└─────────────────────────────────────────────────────────────┘
                            │ ▲
                            ▼ │
┌─────────────────────────────────────────────────────────────┐
│                     Backend API (FastAPI)                   │
│  ┌────────────────────────────────────────────────────┐     │
│  │              Coordinator Agent                     │     │
│  └────────────────────────────────────────────────────┘     │
│                            │                                │
│    ┌───────────┬───────────┼───────────┬──────────┐         │
│    ▼           ▼           ▼           ▼          ▼         │
│  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐  ┌──────┐        │
│  │ Quiz │   │Story │   │ Game │   │ Sim  │  │Review│        │
│  │Writer│   │Writer│   │Design│   │Design│  │ er   │        │
│  └──────┘   └──────┘   └──────┘   └──────┘  └──────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher (for frontend)
- Docker and Docker Compose (optional, for containerized deployment)

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/ilya-spy/adk-agentic-writer.git
cd adk-agentic-writer
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install frontend dependencies**:
```bash
cd frontend
npm install
cd ..
```

### Running the Application

#### Option 1: Run with Docker Compose (Recommended)

```bash
docker-compose up --build
```

- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- API Documentation: http://localhost:8000/docs

#### Option 2: Run Manually

**Start the backend**:
```bash
uvicorn src.adk_agentic_writer.backend.api:app --reload --host 0.0.0.0 --port 8000
```

**Start the frontend** (in a separate terminal):
```bash
cd frontend
npm start
```

## 📖 Usage

### Web Interface

1. Open http://localhost:3000 in your browser
2. Select a content type (Quiz, Quest Game, Branched Story, or Simulation)
3. Enter a topic (e.g., "Ancient Rome", "Climate Change", "Space Exploration")
4. Click "Generate Content"
5. View the generated content with agent collaboration details

### API Usage

**Generate a quiz**:
```bash
curl -X POST "http://localhost:8000/generate/quiz?topic=Python&num_questions=5"
```

**Generate a branched narrative**:
```bash
curl -X POST "http://localhost:8000/generate/story?topic=Space%20Adventure&genre=sci-fi"
```

**Generate a quest game**:
```bash
curl -X POST "http://localhost:8000/generate/game?topic=Ancient%20Treasure"
```

**Generate a simulation**:
```bash
curl -X POST "http://localhost:8000/generate/simulation?topic=Physics"
```

### Python API

```python
from adk_agentic_writer import CoordinatorAgent, ContentType
from adk_agentic_writer.agents import QuizWriterAgent, ReviewerAgent

# Initialise agents
coordinator = CoordinatorAgent()
quiz_writer = QuizWriterAgent()
reviewer = ReviewerAgent()

# Register agents
coordinator.register_agent(quiz_writer)
coordinator.register_agent(reviewer)

# Generate content
result = await coordinator.process_task(
    "Create a quiz about Python",
    {
        "content_type": ContentType.QUIZ,
        "topic": "Python programming",
        "num_questions": 5,
    }
)
```

## 🧪 Testing

Run the test suite:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src/adk_agentic_writer --cov-report=html

# Run specific test file
pytest tests/unit/test_quiz_writer.py
```

## 📁 Project Structure

```
adk-agentic-writer/
├── src/
│   └── adk_agentic_writer/
│       ├── agents/              # Agent implementations
│       │   ├── base_agent.py
│       │   ├── coordinator.py
│       │   ├── quiz_writer.py
│       │   ├── story_writer.py
│       │   ├── game_designer.py
│       │   ├── simulation_designer.py
│       │   └── reviewer.py
│       ├── backend/             # FastAPI backend
│       │   └── api.py
│       ├── models/              # Data models
│       │   ├── agent_models.py
│       │   └── content_models.py
│       └── templates/           # Content templates
├── frontend/                    # React frontend
│   ├── public/
│   └── src/
│       ├── App.tsx
│       ├── App.css
│       └── index.tsx
├── tests/                       # Test suite
│   ├── unit/
│   └── integration/
├── Dockerfile                   # Backend Docker config
├── docker-compose.yml          # Multi-container setup
├── pyproject.toml              # Python project config
├── requirements.txt            # Python dependencies
└── README.md
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Backend
PYTHONUNBUFFERED=1

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🎯 Roadmap

- [ ] Integration with Google Gemini API for enhanced content generation
- [ ] User authentication and content saving
- [ ] Export content to various formats (PDF, HTML, JSON)
- [ ] Real-time collaboration features
- [ ] Advanced content customization options
- [ ] Analytics dashboard for content performance
- [ ] Plugin system for custom content types

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Google Agent Development Kit](https://github.com/google/adk)
- Powered by [FastAPI](https://fastapi.tiangolo.com/)
- UI built with [React](https://reactjs.org/)

## 📧 Contact

Project Link: [https://github.com/ilya-spy/adk-agentic-writer](https://github.com/ilya-spy/adk-agentic-writer)

---

Made with ❤️ for the Agent Development Kit community
