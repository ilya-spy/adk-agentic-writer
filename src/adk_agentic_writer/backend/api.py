"""FastAPI backend server for the ADK Agentic Writer system."""

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

load_dotenv()

from ..utils.log_config import configure_logging, log_settings_summary

configure_logging()
logger = logging.getLogger(__name__)
log_settings_summary()

from ..agents.coordinator import Coordinator

# ---------------------------------------------------------------------------
# Global coordinator
# ---------------------------------------------------------------------------
_coordinator: Coordinator | None = None


class GenerateRequest(BaseModel):
    """Request model for content generation."""

    task_id: str = ""
    content_type: str = ""
    topic: str = ""
    parameters: Dict[str, Any] = {}


class GenerateResponse(BaseModel):
    """Response model for content generation."""

    request_id: str
    content_type: str
    content: Dict[str, Any]
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup the coordinator."""
    global _coordinator
    logger.info("Initializing ADK agent system...")

    try:
        _coordinator = Coordinator()
        logger.info("Coordinator initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize coordinator: %s", e)
        _coordinator = None

    yield

    logger.info("Shutting down ADK agent system...")
    _coordinator = None


app = FastAPI(
    title="ADK Agentic Writer API",
    description="Multi-agentic system for interactive content production",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


def _get_coordinator() -> Coordinator:
    if _coordinator is None:
        raise HTTPException(status_code=503, detail="Agent system not available")
    return _coordinator


def _resolve_task(coordinator: Coordinator, request: GenerateRequest):
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


def _build_params(request: GenerateRequest, task) -> Tuple[Dict[str, Any], str]:
    """Merge request parameters with topic and content_type."""
    params = {**(request.parameters or {})}
    if request.topic:
        params["topic"] = request.topic

    base_type = task.content_types[0] if task.content_types else ""
    if base_type:
        params["content_type"] = base_type

    params["content_type_alias"] = (
        request.content_type
        if request.content_type and request.content_type != base_type
        else ""
    )
    content_type_label = request.content_type or base_type
    return params, content_type_label


def _error_response(request_id: str, request: GenerateRequest, error) -> GenerateResponse:
    return GenerateResponse(
        request_id=request_id,
        content_type=request.content_type or "",
        content={"error": str(error), "status": "failed"},
        status="error",
    )


# ---------------------------------------------------------------------------
# Static pages
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root():
    return _serve_html("index.html")


@app.get("/api")
async def api_info():
    return {
        "message": "ADK Agentic Writer API",
        "version": "2.0.0",
        "available": _coordinator is not None,
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy" if _coordinator else "unavailable",
        "coordinator": _coordinator is not None,
    }


@app.get("/showcase", response_class=HTMLResponse)
async def showcase():
    return _serve_html("showcase.html")


@app.get("/frontend", response_class=HTMLResponse)
async def frontend():
    return _serve_html("frontend.html")


@app.get("/tasks")
async def get_tasks():
    coordinator = _get_coordinator()
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
    coordinator = _get_coordinator()
    grouped = coordinator.get_all_content_types()

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
    """Generate content by resolving a task and calling the writer."""
    request_id = str(uuid.uuid4())
    coordinator = _get_coordinator()
    task = _resolve_task(coordinator, request)
    params, content_type_label = _build_params(request, task)

    try:
        result = await coordinator.process_task(task, params)
        return GenerateResponse(
            request_id=request_id,
            content_type=content_type_label,
            content=result,
            status="completed",
        )
    except Exception as e:
        logger.error("Error: %s", e)
        return _error_response(request_id, request, e)


@app.post("/generate/with-validation", response_model=GenerateResponse)
async def generate_with_validation(request: GenerateRequest):
    """Generate content then validate via the validator agent."""
    request_id = str(uuid.uuid4())
    coordinator = _get_coordinator()
    task = _resolve_task(coordinator, request)
    params, content_type_label = _build_params(request, task)

    try:
        result = await coordinator.process_with_validation(task, params)
        return GenerateResponse(
            request_id=request_id,
            content_type=content_type_label,
            content=result,
            status="completed",
        )
    except Exception as e:
        logger.error("Error in validation workflow: %s", e)
        return _error_response(request_id, request, e)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
