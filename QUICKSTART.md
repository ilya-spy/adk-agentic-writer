# Quick Start Guide

This guide will help you get the ADK Agentic Writer up and running in minutes.

## Prerequisites

- Python 3.11+ 
- Node.js 18+ (for frontend)
- pip (Python package manager)
- npm (Node package manager)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/ilya-spy/adk-agentic-writer.git
cd adk-agentic-writer
```

### 2. Quick Setup with Script

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Check Python version
- Create virtual environment
- Install all dependencies
- Set up frontend
- Create .env file

### 3. Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install frontend dependencies
cd frontend
npm install
cd ..

# Create environment file
cp .env.example .env
```

## Running the Application

### Option 1: Using Docker (Recommended for Production)

```bash
docker-compose up --build
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Running Locally (Development)

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
make run-backend
# Or: uvicorn src.adk_agentic_writer.backend.api:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## First Steps

1. **Open the Web Interface** at http://localhost:3000

2. **Select a Content Type:**
   - Quiz
   - Quest Game
   - Branched Story
   - Simulation

3. **Enter a Topic:**
   Examples:
   - "Ancient Rome"
   - "Climate Change"
   - "Space Exploration"
   - "Python Programming"

4. **Generate Content:**
   Click the "Generate Content" button and watch the agents work!

## Testing the API Directly

```bash
# Generate a quiz
curl -X POST "http://localhost:8000/generate/quiz?topic=Python&num_questions=5"

# Generate a story
curl -X POST "http://localhost:8000/generate/story?topic=Adventure&genre=fantasy"

# List available agents
curl http://localhost:8000/agents

# Get health status
curl http://localhost:8000/health
```

## Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=src/adk_agentic_writer

# Run specific tests
pytest tests/unit/
pytest tests/integration/
```

## Common Issues and Solutions

### Port Already in Use

If port 8000 or 3000 is already in use:

**Backend:**
```bash
uvicorn src.adk_agentic_writer.backend.api:app --reload --port 8001
```

**Frontend:**
Update `frontend/package.json` to use a different port or set:
```bash
PORT=3001 npm start
```

### Import Errors

Make sure the package is installed in development mode:
```bash
pip install -e .
```

### Docker Issues

```bash
# Rebuild containers
docker-compose down
docker-compose up --build

# View logs
docker-compose logs -f
```

## Next Steps

- Explore the [API Documentation](http://localhost:8000/docs)
- Read the [Contributing Guide](CONTRIBUTING.md)
- Check out the [Full README](README.md)
- Experiment with different content types and topics

## Getting Help

If you encounter any issues:
1. Check the logs for error messages
2. Ensure all dependencies are installed
3. Verify Python and Node versions
4. Open an issue on GitHub

## Architecture Overview

```
┌─────────────────┐
│  React Frontend │ (Port 3000)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI Backend│ (Port 8000)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│        Multi-Agent System           │
│  ┌──────────┐  ┌──────────┐        │
│  │Quiz Agent│  │Story Agent│   ...  │
│  └──────────┘  └──────────┘        │
└─────────────────────────────────────┘
```

Happy content creating! 🚀
