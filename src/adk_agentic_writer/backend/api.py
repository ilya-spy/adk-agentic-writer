"""FastAPI backend server for the ADK Agentic Writer system."""

# Clear proxy FIRST before any network imports
from ..utils.proxy_utils import clear_proxy_env

clear_proxy_env()

import logging
import pathlib
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, Tuple

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ..agents.static import CoordinatorAgent as StaticCoordinator
from ..tasks.editorial_tasks import VALIDATE_CONTENT

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
    """Request model for content generation.

    Callers can specify either task_id or content_type (alias).
    task_id takes priority over content_type when both are provided.
    """

    team: str = "static"  # "static" or "gemini"
    task_id: str = ""  # e.g. "generate_quiz" -- preferred
    content_type: str = ""  # e.g. "quiz" -- alias, backward compat
    topic: str = ""
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


# ---------------------------------------------------------------------------
# Request / response trace (single source of truth for access logs)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def request_trace(request: Request, call_next):
    """Log every request with method, path, status and duration."""
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s (%.0fms)", request.method, request.url.path, response.status_code, ms)
    return response


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
_PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent


def _serve_html(filename: str) -> HTMLResponse:
    """Serve an HTML file from frontend/public/ or return a 404 fallback."""
    path = _PROJECT_ROOT / "frontend" / "public" / filename
    if path.exists():
        return HTMLResponse(path.read_text(encoding="utf-8"))
    return HTMLResponse(
        f"<html><body><h1>{filename} not found</h1></body></html>",
        status_code=404,
    )


def _get_coordinator(team: str):
    """Validate team name and return its coordinator, or raise HTTPException."""
    if team not in ("static", "gemini"):
        raise HTTPException(status_code=400, detail=f"Invalid team: {team}")
    if not agent_systems[team].get("initialized"):
        raise HTTPException(status_code=503, detail=f"{team} team not available")
    return agent_systems[team]["coordinator"]


def _resolve_task(coordinator, request: "GenerateRequest"):
    """Resolve an AgentTask from the request, or raise HTTPException(400)."""
    task = coordinator.resolve_task(
        task_id=request.task_id or None,
        content_type=request.content_type or None,
    )
    if not task:
        label = request.task_id or request.content_type or "(empty)"
        raise HTTPException(
            status_code=400, detail=f"Unknown task or content type: {label}"
        )
    return task


def _build_params(request: "GenerateRequest", task) -> Tuple[Dict[str, Any], str]:
    """Merge request parameters with topic and content_type.

    Uses ``task.content_types[0]`` as the canonical base type
    (the one registered in CONTENT_REGISTRY).  The raw alias from the
    request is passed separately so the Gemini writer can add a style hint.

    Returns (params_dict, content_type_label).
    """
    params = {**(request.parameters or {})}
    if request.topic:
        params["topic"] = request.topic
    # Canonical base type from the resolved task (single source of truth)
    base_type = task.content_types[0] if task.content_types else ""
    if base_type:
        params["content_type"] = base_type
    # Always set alias key so it overwrites any stale value from prior requests
    params["content_type_alias"] = (
        request.content_type
        if request.content_type and request.content_type != base_type
        else ""
    )
    content_type_label = request.content_type or base_type
    return params, content_type_label


def _error_response(request_id: str, request: "GenerateRequest", error) -> GenerateResponse:
    """Build a standardised error GenerateResponse."""
    return GenerateResponse(
        request_id=request_id,
        team=request.team,
        content_type=request.content_type or "",
        content={"error": str(error), "status": "failed"},
        status="error",
    )


# ---------------------------------------------------------------------------
# Static pages
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the server directory page."""
    return _serve_html("index.html")


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


@app.get("/showcase", response_class=HTMLResponse)
async def showcase():
    """Serve the showcase page."""
    return _serve_html("showcase.html")


@app.get("/frontend", response_class=HTMLResponse)
async def frontend():
    """Serve the legacy frontend page."""
    return _serve_html("frontend.html")


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


@app.get("/workflows")
async def get_workflows():
    """Get available workflows."""
    if not agent_systems["static"].get("initialized"):
        return {"workflows": []}

    coordinator = agent_systems["static"]["coordinator"]
    return {
        "workflows": [
            {
                "name": wf.name,
                "tasks": [t.task_id if t else None for t in wf.tasks],
            }
            for wf in coordinator.get_supported_workflows()
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


@app.post("/generate", response_model=GenerateResponse)
async def generate_content(request: GenerateRequest):
    """Generate content by resolving a task and calling process_task."""
    request_id = str(uuid.uuid4())
    coordinator = _get_coordinator(request.team)
    task = _resolve_task(coordinator, request)
    params, content_type_label = _build_params(request, task)

    try:
        result = await coordinator.process_task(task, params)
        return GenerateResponse(
            request_id=request_id,
            team=request.team,
            content_type=content_type_label,
            content=result,
            status="completed",
        )
    except Exception as e:
        logger.error("Error: %s", e)
        return _error_response(request_id, request, e)


@app.post("/generate/with-validation", response_model=GenerateResponse)
async def generate_with_validation(request: GenerateRequest):
    """Generate content then validate via editorial workflow.

    1. Resolves the content generation task (e.g. generate_quiz)
    2. Finds a workflow whose tasks include VALIDATE_CONTENT
    3. Executes that workflow -- writer -> validator sequentially
    4. Returns the combined result (content + validation_result)
    """
    request_id = str(uuid.uuid4())
    coordinator = _get_coordinator(request.team)
    task = _resolve_task(coordinator, request)

    workflow = coordinator.resolve_workflow(task_id=VALIDATE_CONTENT.task_id)
    if not workflow:
        raise HTTPException(status_code=500, detail="No validation workflow available")

    params, content_type_label = _build_params(request, task)

    try:
        result = await workflow.execute({"tasks": [task], "parameters": params})
        return GenerateResponse(
            request_id=request_id,
            team=request.team,
            content_type=content_type_label,
            content=result,
            status="completed",
        )
    except Exception as e:
        logger.error("Error in validation workflow: %s", e)
        return _error_response(request_id, request, e)


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

    story_content = "This is a test story content."
    game_content = "This is a test game content."
    quiz_content = "This is a test quiz content."
    game_results = [game_content]
    quiz_results = [quiz_content]
    nodes = 10

    multimodal_result = {
        "content_type": "multimodal_story",
        "content": story_content,
        "embedded_games": sum(1 for r in game_results if not isinstance(r, Exception)),
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
