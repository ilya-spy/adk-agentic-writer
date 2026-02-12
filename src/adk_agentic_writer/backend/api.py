"""FastAPI backend server for the ADK Agentic Writer system."""

# Clear proxy FIRST before any network imports
from ..utils.proxy_utils import clear_proxy_env

clear_proxy_env()

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ..agents.static import CoordinatorAgent as StaticCoordinator

# Load environment variables
load_dotenv()

# Centralized logging (reads LOG_LEVEL, LOG_LLM_IO, etc. from env)
from ..utils.log_config import configure_logging, log_settings_summary

configure_logging()
logger = logging.getLogger(__name__)
log_settings_summary()

# Gemini agents
from ..agents.gemini import GeminiCoordinatorAgent

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

    # Ensure keys exist (may have been cleared by a previous lifespan cycle)
    agent_systems.setdefault("static", {"initialized": False, "coordinator": None})
    agent_systems.setdefault("gemini", {"initialized": False, "coordinator": None})

    # Initialize Static Team
    try:
        # New coordinator auto-registers agents via runtime
        static_coordinator = StaticCoordinator(agent_id="static_coordinator")

        agent_systems["static"]["coordinator"] = static_coordinator
        agent_systems["static"]["initialized"] = True
        logger.info("Static team initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize static team: {e}")
        agent_systems["static"]["initialized"] = False

    # Initialize Gemini Team
    try:
        gemini_coordinator = GeminiCoordinatorAgent(agent_id="gemini_coordinator")
        agent_systems["gemini"]["coordinator"] = gemini_coordinator
        agent_systems["gemini"]["initialized"] = True
        logger.info(
            "Gemini team initialized (requires GOOGLE_API_KEY for LLM generation)"
        )
    except Exception as e:
        logger.warning(f"Gemini team initialization failed: {e}")
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
    """Generate content using coordinator.generate_content()."""
    request_id = str(uuid.uuid4())

    if request.team not in ["static", "gemini"]:
        raise HTTPException(status_code=400, detail=f"Invalid team: {request.team}")

    if not agent_systems[request.team].get("initialized"):
        raise HTTPException(
            status_code=503, detail=f"{request.team} team not available"
        )

    coordinator = agent_systems[request.team]["coordinator"]

    try:
        # Use coordinator's generate_content convenience method
        result = await coordinator.generate_content(
            content_type=request.content_type,
            topic=request.topic,
            **(request.parameters or {}),
        )

        return GenerateResponse(
            request_id=request_id,
            team=request.team,
            content_type=request.content_type,
            content=result,
            status="completed",
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        return GenerateResponse(
            request_id=request_id,
            team=request.team,
            content_type=request.content_type,
            content={"error": str(e), "status": "failed"},
            status="error",
        )


@app.post("/generate/with-validation", response_model=GenerateResponse)
async def generate_with_validation(request: GenerateRequest):
    """Generate content with ValidationEditorialWorkflow (writer → validator).

    Returns a JSON response with:
      - content: generated content (writer output)
      - validation_result: validation summary (validator output)
      - status: "validated"

    Supports both static and gemini teams.
    """
    request_id = str(uuid.uuid4())

    if request.team not in ["static", "gemini"]:
        raise HTTPException(status_code=400, detail=f"Invalid team: {request.team}")

    if not agent_systems[request.team].get("initialized"):
        raise HTTPException(
            status_code=503, detail=f"{request.team} team not available"
        )

    coordinator = agent_systems[request.team]["coordinator"]

    try:
        result = await coordinator.generate_with_validation(
            content_type=request.content_type,
            topic=request.topic,
            **(request.parameters or {}),
        )

        # result already has {"content": ..., "validation_result": ..., "status": "validated"}
        return GenerateResponse(
            request_id=request_id,
            team=request.team,
            content_type=request.content_type,
            content=result,
            status="completed",
        )

    except Exception as e:
        logger.error(f"Error in validation workflow: {e}")
        return GenerateResponse(
            request_id=request_id,
            team=request.team,
            content_type=request.content_type,
            content={"error": str(e), "status": "failed"},
            status="error",
        )


@app.post("/generate/multimodal-story")
async def generate_multimodal_story(request: GenerateRequest):
    """Generate complex multimodal story with embedded games and quizzes."""
    request_id = str(uuid.uuid4())

    if request.team != "static":
        raise HTTPException(
            status_code=400,
            detail="Multimodal stories only available for static team",
        )

    if not agent_systems["static"].get("initialized"):
        raise HTTPException(status_code=503, detail="Static team not available")

    coordinator = agent_systems["static"]["coordinator"]

    try:
        params = request.parameters.copy() if request.parameters else {}
        num_story_nodes = params.get("num_story_nodes", 8)
        num_mini_games = params.get("num_mini_games", 2)
        num_mini_quizzes = params.get("num_mini_quizzes", 2)
        genre = params.get("genre", "adventure")

        # Parallel generation
        results = await asyncio.gather(
            coordinator.generate_content(
                "branched_narrative",
                request.topic,
                num_nodes=num_story_nodes,
                genre=genre,
            ),
            *[
                coordinator.generate_content(
                    "quest_game", f"{request.topic} Mini-Game {i+1}", num_nodes=4
                )
                for i in range(num_mini_games)
            ],
            *[
                coordinator.generate_content(
                    "quiz", f"{request.topic} Quiz {i+1}", num_questions=3
                )
                for i in range(num_mini_quizzes)
            ],
            return_exceptions=True,
        )

        # Extract and integrate
        story_result = results[0] if not isinstance(results[0], Exception) else None
        if not story_result:
            raise ValueError("Story generation failed")

        story_content = story_result["content"]
        nodes = story_content.get("nodes", {})

        # Inject games and quizzes
        game_results = results[1 : 1 + num_mini_games]
        quiz_results = results[1 + num_mini_games :]

        for i, result in enumerate(game_results):
            if not isinstance(result, Exception) and i + 1 < len(nodes):
                node_id = list(nodes.keys())[i + 1]
                nodes[node_id]["embedded_game"] = result["content"]

        for i, result in enumerate(quiz_results):
            if not isinstance(result, Exception) and num_mini_games + i + 1 < len(
                nodes
            ):
                node_id = list(nodes.keys())[num_mini_games + i + 1]
                nodes[node_id]["embedded_quiz"] = result["content"]

        multimodal_result = {
            "content_type": "multimodal_story",
            "content": story_content,
            "embedded_games": sum(
                1 for r in game_results if not isinstance(r, Exception)
            ),
            "embedded_quizzes": sum(
                1 for r in quiz_results if not isinstance(r, Exception)
            ),
            "total_nodes": len(nodes),
            "generation_method": "parallel_mixed_team",
        }

        return GenerateResponse(
            request_id=request_id,
            team=request.team,
            content_type="multimodal_story",
            content=multimodal_result,
            status="completed",
        )

    except Exception as e:
        logger.error(f"Error generating multimodal story: {e}")
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


@app.get("/tasks")
async def get_tasks():
    """Get available tasks with their content_types aliases."""
    if not agent_systems["static"].get("initialized"):
        return {"tasks": []}

    coordinator = agent_systems["static"]["coordinator"]
    return {
        "tasks": [
            {
                "task_id": t.task_id,
                "label": t.task_id.replace("generate_", "").replace("_", " ").title(),
                "content_types": t.content_types,
                "parameters": list((t.parameters or {}).keys()),
            }
            for t in coordinator.get_supported_tasks()
        ]
    }


@app.get("/content-types")
async def get_content_types():
    """Get all content type aliases from tasks."""
    if not agent_systems["static"].get("initialized"):
        return {"content_types": [], "grouped": {}}

    coordinator = agent_systems["static"]["coordinator"]
    grouped = coordinator.get_all_content_types()

    # Flatten for simple UI selector
    content_types = []
    for task in coordinator.get_supported_tasks():
        for ct in task.content_types:
            content_types.append(
                {
                    "value": ct,
                    "task_id": task.task_id,
                    "label": ct.replace("_", " ").title(),
                }
            )

    return {"content_types": content_types, "grouped": grouped}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
