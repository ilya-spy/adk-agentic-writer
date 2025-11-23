"""FastAPI backend server for the ADK Agentic Writer system."""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ..agents.static import (
    CoordinatorAgent as StaticCoordinator,
    StaticQuizWriterAgent,
    StoryWriterAgent,
    GameDesignerAgent,
    SimulationDesignerAgent,
    ReviewerAgent as StaticReviewer,
)
from ..models import ContentType

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini agents are optional
try:
    from ..agents.gemini import (
        GeminiCoordinatorAgent,
        GeminiQuizWriterAgent,
        GeminiStoryWriterAgent,
        GeminiGameDesignerAgent,
        GeminiSimulationDesignerAgent,
        GeminiReviewerAgent,
        SupportedTask,
    )

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Gemini agents not available (google.adk not installed)")

# Global agent systems - initialize with empty dicts
agent_systems: Dict[str, Any] = {
    "static": {"initialized": False, "coordinator": None},
    "gemini": {"initialized": False, "coordinator": None},
}


class GenerateRequest(BaseModel):
    """Request model for content generation."""

    team: str = "static"  # "static" or "gemini"
    content_type: str
    topic: str
    parameters: Dict[str, Any] = {}


class GenerateResponse(BaseModel):
    """Response model for content generation."""

    request_id: str
    team: str
    content_type: str
    content: Dict[str, Any]
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup the agent systems."""
    logger.info("Initializing ADK multi-agent systems...")

    # Initialize Static Team
    try:
        static_coordinator = StaticCoordinator(agent_id="static_coordinator")
        static_coordinator.register_agent(StaticQuizWriterAgent())
        static_coordinator.register_agent(StoryWriterAgent())
        static_coordinator.register_agent(GameDesignerAgent())
        static_coordinator.register_agent(SimulationDesignerAgent())
        static_coordinator.register_agent(StaticReviewer())

        agent_systems["static"]["coordinator"] = static_coordinator
        agent_systems["static"]["initialized"] = True
        logger.info("Static team initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize static team: {e}")
        agent_systems["static"]["initialized"] = False

    # Initialize Gemini Team (if available)
    if GEMINI_AVAILABLE:
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            try:
                gemini_coordinator = GeminiCoordinatorAgent(
                    agent_id="gemini_coordinator"
                )
                gemini_coordinator.register_agent(GeminiQuizWriterAgent())
                gemini_coordinator.register_agent(GeminiStoryWriterAgent())
                gemini_coordinator.register_agent(GeminiGameDesignerAgent())
                gemini_coordinator.register_agent(GeminiSimulationDesignerAgent())
                gemini_coordinator.register_agent(GeminiReviewerAgent())

                agent_systems["gemini"]["coordinator"] = gemini_coordinator
                agent_systems["gemini"]["initialized"] = True
                logger.info("Gemini team initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize gemini team: {e}")
                agent_systems["gemini"]["initialized"] = False
        else:
            logger.warning("No GOOGLE_API_KEY found - Gemini team unavailable")
            agent_systems["gemini"]["initialized"] = False
    else:
        logger.warning("Gemini agents not available (google.adk package not installed)")
        agent_systems["gemini"]["initialized"] = False

    yield

    # Shutdown
    logger.info("Shutting down ADK multi-agent systems...")
    agent_systems.clear()


# Create FastAPI app
app = FastAPI(
    title="ADK Agentic Writer API",
    description="Multi-agentic system for interactive content production",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the server directory page."""
    import pathlib

    # Get the path to the frontend/public/index.html
    current_file = pathlib.Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    index_path = project_root / "frontend" / "public" / "index.html"

    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    else:
        # Fallback to JSON response if file not found
        return HTMLResponse(
            content="""
            <html>
                <head><title>ADK Agentic Writer</title></head>
                <body>
                    <h1>ADK Agentic Writer API</h1>
                    <p>Server is running!</p>
                    <ul>
                        <li><a href="/health">Health Check</a></li>
                        <li><a href="/teams">Available Teams</a></li>
                        <li><a href="/docs">API Documentation</a></li>
                    </ul>
                </body>
            </html>
            """,
            status_code=200,
        )


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "message": "ADK Agentic Writer API",
        "version": "1.0.0",
        "teams": {
            "static": agent_systems["static"].get("initialized", False),
            "gemini": agent_systems["gemini"].get("initialized", False),
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "static_team": agent_systems["static"].get("initialized", False),
        "gemini_team": agent_systems["gemini"].get("initialized", False),
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate_content(request: GenerateRequest):
    """Generate content using specified team."""
    request_id = str(uuid.uuid4())

    # Validate team
    if request.team not in ["static", "gemini"]:
        raise HTTPException(status_code=400, detail=f"Invalid team: {request.team}")

    # Check if team is initialized
    if not agent_systems[request.team].get("initialized"):
        raise HTTPException(
            status_code=503, detail=f"{request.team.capitalize()} team not available"
        )

    # Get coordinator
    coordinator = agent_systems[request.team]["coordinator"]

    try:
        # Prepare parameters
        params = {
            "content_type": request.content_type,
            "topic": request.topic,
            **request.parameters,
        }

        # Generate content based on team
        if request.team == "static":
            # Static team uses simple task description
            result = await coordinator.process_task(
                f"Generate {request.content_type}", params
            )
        else:
            # Gemini team uses structured tasks
            if GEMINI_AVAILABLE and SupportedTask:
                task_mapping = {
                    "quiz": SupportedTask.GENERATE_QUIZ,
                    "branched_narrative": SupportedTask.GENERATE_STORY,
                    "quest_game": SupportedTask.GENERATE_GAME,
                    "web_simulation": SupportedTask.GENERATE_SIMULATION,
                }

                task = task_mapping.get(
                    request.content_type, SupportedTask.GENERATE_QUIZ
                )
                params["task"] = task

            result = await coordinator.process_task(
                f"Generate {request.content_type}", params
            )

        return GenerateResponse(
            request_id=request_id,
            team=request.team,
            content_type=request.content_type,
            content=result,
            status="completed",
        )

    except Exception as e:
        logger.error(f"Error generating content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/showcase", response_class=HTMLResponse)
async def showcase():
    """Serve the showcase page."""
    import pathlib

    # Get the path to the frontend/public/showcase.html
    current_file = pathlib.Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    showcase_path = project_root / "frontend" / "public" / "showcase.html"

    if showcase_path.exists():
        return showcase_path.read_text(encoding="utf-8")
    else:
        return HTMLResponse(
            content="<html><body><h1>Showcase page not found</h1></body></html>",
            status_code=404,
        )


@app.get("/frontend", response_class=HTMLResponse)
async def frontend():
    """Serve the legacy frontend page."""
    import pathlib

    current_file = pathlib.Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    frontend_path = project_root / "frontend" / "public" / "frontend.html"

    if frontend_path.exists():
        return frontend_path.read_text(encoding="utf-8")
    else:
        return HTMLResponse(
            content="<html><body><h1>Frontend page not found</h1></body></html>",
            status_code=404,
        )


@app.get("/teams")
async def get_teams():
    """Get available teams and their status."""
    return {
        "teams": [
            {
                "id": "static",
                "name": "Static Team",
                "description": "Fast, template-based generation. No API calls required.",
                "available": agent_systems["static"].get("initialized", False),
                "icon": "⚡",
            },
            {
                "id": "gemini",
                "name": "Gemini Team",
                "description": "AI-powered generation via Google ADK. High quality, creative.",
                "available": agent_systems["gemini"].get("initialized", False),
                "icon": "🤖",
            },
        ]
    }


@app.get("/content-types")
async def get_content_types():
    """Get available content types."""
    return {
        "content_types": [
            {
                "value": "quiz",
                "label": "Quiz",
                "description": "Interactive quizzes with multiple choice questions",
            },
            {
                "value": "quest_game",
                "label": "Quest Game",
                "description": "Quest-based adventure games with choices and rewards",
            },
            {
                "value": "branched_narrative",
                "label": "Branched Story",
                "description": "Branching storylines with multiple endings",
            },
            {
                "value": "web_simulation",
                "label": "Simulation",
                "description": "Interactive simulations with variables and controls",
            },
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
