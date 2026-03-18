"""FastAPI backend server for the ADK Agentic Writer system."""

from ..utils.proxy import clear_proxy_env

clear_proxy_env()

import logging
import pathlib
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

load_dotenv()

from ..utils.log import configure_logging, log_settings_summary

configure_logging()
logger = logging.getLogger(__name__)
log_settings_summary()

from ..agents.coordinator import Coordinator

# ---------------------------------------------------------------------------
# Global coordinator
# ---------------------------------------------------------------------------
_coordinator: Coordinator | None = None


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class AgentRequest(BaseModel):
    """Unified request model for all agent endpoints."""

    prompt: str = ""
    content_types: List[str] = []
    content: Dict[str, Any] = {}
    parameters: Dict[str, Any] = {}
    # Legacy compat
    task_id: str = ""
    content_type: str = ""
    topic: str = ""


class AgentResponse(BaseModel):
    """Unified response model for all agent endpoints."""

    request_id: str
    action: str
    content_type: str = ""
    content: Dict[str, Any] = {}
    stages: List[Dict[str, Any]] = []
    status: str = "completed"


# Legacy compat aliases
GenerateRequest = AgentRequest
GenerateResponse = AgentResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    version="3.0.0",
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
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s (%.0fms)", request.method, request.url.path, response.status_code, ms)
    return response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent


def _serve_html(filename: str) -> HTMLResponse:
    path = _PROJECT_ROOT / "frontend" / "public" / filename
    if path.exists():
        return HTMLResponse(path.read_text(encoding="utf-8"))
    return HTMLResponse(f"<html><body><h1>{filename} not found</h1></body></html>", status_code=404)


def _get_coordinator() -> Coordinator:
    if _coordinator is None:
        raise HTTPException(status_code=503, detail="Agent system not available")
    return _coordinator


def _resolve_content_type(req: AgentRequest) -> str:
    """Extract effective content type from request."""
    if req.content_type:
        return req.content_type
    if req.content_types:
        return req.content_types[0]
    return ""


def _build_prompt(req: AgentRequest) -> str:
    """Build the user prompt from request fields."""
    parts = []
    if req.prompt:
        parts.append(req.prompt)
    elif req.topic:
        parts.append(f"Create content about: {req.topic}")
    if req.content_types and len(req.content_types) > 1:
        parts.append(f"Requested formats: {', '.join(req.content_types)}")
    return "\n".join(parts) if parts else "Create interesting content."


def _error_response(request_id: str, action: str, error) -> AgentResponse:
    return AgentResponse(
        request_id=request_id,
        action=action,
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
    return {"message": "ADK Agentic Writer API", "version": "3.0.0", "available": _coordinator is not None}


@app.get("/health")
async def health():
    return {"status": "healthy" if _coordinator else "unavailable", "coordinator": _coordinator is not None}


@app.get("/showcase", response_class=HTMLResponse)
async def showcase():
    return _serve_html("showcase.html")


# ---------------------------------------------------------------------------
# Discovery endpoints
# ---------------------------------------------------------------------------

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
    from ..formats import list_formats

    content_types = []
    for fmt in list_formats():
        content_types.append({
            "value": fmt.name,
            "label": fmt.label,
            "aliases": fmt.aliases,
            "parameters": [
                {"name": p.name, "type": p.type, "default": p.default, "description": p.description}
                for p in fmt.parameter_specs
            ],
        })
    return {"content_types": content_types}


# ---------------------------------------------------------------------------
# Agent action endpoints
# ---------------------------------------------------------------------------

@app.post("/ideate", response_model=AgentResponse)
async def ideate(request: AgentRequest):
    """Run ideation on a user prompt."""
    request_id = str(uuid.uuid4())
    coordinator = _get_coordinator()
    prompt = _build_prompt(request)

    try:
        result = await coordinator.ideate(prompt)
        return AgentResponse(
            request_id=request_id, action="ideate", content=result, status="completed",
        )
    except Exception as e:
        logger.error("Ideation error: %s", e)
        return _error_response(request_id, "ideate", e)


@app.post("/generate", response_model=AgentResponse)
async def generate_content(request: AgentRequest):
    """Generate content for a specific format."""
    request_id = str(uuid.uuid4())
    coordinator = _get_coordinator()
    ct = _resolve_content_type(request)

    if not ct:
        # Legacy compat: resolve via task_id
        if request.task_id:
            task = coordinator.resolve_task(task_id=request.task_id)
            if task and task.content_types:
                ct = task.content_types[0]
        if not ct:
            raise HTTPException(status_code=400, detail="No content_type specified")

    prompt = _build_prompt(request)

    # Merge format default params with request params
    from ..formats import get_format
    fmt = get_format(ct)
    if fmt:
        merged = dict(fmt.default_params)
        merged.update(request.parameters)
        merged["topic"] = request.topic or request.prompt or "general"
        try:
            prompt = fmt.writer_prompt.format(**merged)
        except KeyError:
            pass

    try:
        result = await coordinator.generate(ct, prompt)
        return AgentResponse(
            request_id=request_id, action="generate", content_type=ct, content=result, status="completed",
        )
    except Exception as e:
        logger.error("Generate error: %s", e)
        return _error_response(request_id, "generate", e)


@app.post("/review", response_model=AgentResponse)
async def review_content(request: AgentRequest):
    """Review provided content."""
    request_id = str(uuid.uuid4())
    coordinator = _get_coordinator()

    if not request.content:
        raise HTTPException(status_code=400, detail="No content provided for review")

    ct = _resolve_content_type(request) or "unknown"

    try:
        result = await coordinator.review(request.content, ct)
        return AgentResponse(
            request_id=request_id, action="review", content_type=ct, content=result, status="completed",
        )
    except Exception as e:
        logger.error("Review error: %s", e)
        return _error_response(request_id, "review", e)


@app.post("/refine", response_model=AgentResponse)
async def refine_content(request: AgentRequest):
    """Refine content based on review feedback."""
    request_id = str(uuid.uuid4())
    coordinator = _get_coordinator()

    if not request.content:
        raise HTTPException(status_code=400, detail="No content provided for refinement")

    review = request.parameters.get("review_result", {})
    if not review:
        review = {"summary": "Please improve overall quality", "errors": [], "warnings": []}

    try:
        result = await coordinator.refine(request.content, review)
        return AgentResponse(
            request_id=request_id, action="refine", content=result, status="completed",
        )
    except Exception as e:
        logger.error("Refine error: %s", e)
        return _error_response(request_id, "refine", e)


@app.post("/publish", response_model=AgentResponse)
async def publish_content(request: AgentRequest):
    """Full publish pipeline: generate -> review -> refine."""
    request_id = str(uuid.uuid4())
    coordinator = _get_coordinator()
    ct = _resolve_content_type(request)

    if not ct:
        raise HTTPException(status_code=400, detail="No content_type specified for publish")

    prompt = _build_prompt(request)

    from ..formats import get_format
    fmt = get_format(ct)
    if fmt:
        merged = dict(fmt.default_params)
        merged.update(request.parameters)
        merged["topic"] = request.topic or request.prompt or "general"
        try:
            prompt = fmt.writer_prompt.format(**merged)
        except KeyError:
            pass

    try:
        result = await coordinator.publish(ct, prompt)
        return AgentResponse(
            request_id=request_id,
            action="publish",
            content_type=ct,
            content=result.get("content", {}),
            stages=result.get("stages", []),
            status="completed",
        )
    except Exception as e:
        logger.error("Publish error: %s", e)
        return _error_response(request_id, "publish", e)


# Legacy compat endpoint
@app.post("/generate/with-validation", response_model=AgentResponse)
async def generate_with_validation(request: AgentRequest):
    """Generate content then validate (legacy compat)."""
    request_id = str(uuid.uuid4())
    coordinator = _get_coordinator()
    ct = _resolve_content_type(request)

    if not ct and request.task_id:
        task = coordinator.resolve_task(task_id=request.task_id)
        if task and task.content_types:
            ct = task.content_types[0]
    if not ct:
        raise HTTPException(status_code=400, detail="No content_type specified")

    prompt = _build_prompt(request)

    from ..formats import get_format
    fmt = get_format(ct)
    if fmt:
        merged = dict(fmt.default_params)
        merged.update(request.parameters)
        merged["topic"] = request.topic or request.prompt or "general"
        try:
            prompt = fmt.writer_prompt.format(**merged)
        except KeyError:
            pass

    try:
        content = await coordinator.generate(ct, prompt)
        validation = await coordinator.review(content, ct)
        result = {"content": content, "validation_result": validation}
        return AgentResponse(
            request_id=request_id, action="generate_with_validation",
            content_type=ct, content=result, status="completed",
        )
    except Exception as e:
        logger.error("Error in validation workflow: %s", e)
        return _error_response(request_id, "generate_with_validation", e)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
