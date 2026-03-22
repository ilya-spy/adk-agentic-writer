"""FastAPI backend -- task-driven API for the ADK Agentic Writer."""

from ..utils.proxy import clear_proxy_env

clear_proxy_env()

import asyncio
import json as _json
import logging
import pathlib
import time
import uuid
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from starlette.responses import StreamingResponse

load_dotenv()

from ..utils.event_bus import get_event_bus
from ..utils.log import configure_logging, log_settings_summary

configure_logging()
logger = logging.getLogger(__name__)
log_settings_summary()

from ..agents.coordinator import CoordinatorService
from .runtime import get_runtime, get_coordinator, lifespan


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class AgentRequest(BaseModel):
    """All task parameters go here."""
    parameters: Dict[str, Any] = {}


class AgentResponse(BaseModel):
    request_id: str
    task_id: str
    output_key: str = ""
    content: Dict[str, Any] = {}
    stages: List[Dict[str, Any]] = []
    status: str = "completed"


app = FastAPI(
    title="ADK Agentic Writer API",
    description="Task-driven multi-agentic content production system",
    version="4.0.0",
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


_PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent


def _serve_html(filename: str) -> HTMLResponse:
    path = _PROJECT_ROOT / "frontend" / "public" / filename
    if path.exists():
        return HTMLResponse(path.read_text(encoding="utf-8"))
    return HTMLResponse(f"<html><body><h1>{filename} not found</h1></body></html>", status_code=404)


def _get_coordinator() -> CoordinatorService:
    coordinator = get_coordinator()
    if coordinator is None:
        raise HTTPException(status_code=503, detail="Agent system not available")
    return coordinator


# ---------------------------------------------------------------------------
# Static pages
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def root():
    return _serve_html("index.html")


@app.get("/api")
async def api_info():
    return {"message": "ADK Agentic Writer API", "version": "4.0.0", "available": get_coordinator() is not None}


@app.get("/health")
async def health():
    c = get_coordinator()
    return {"status": "healthy" if c else "unavailable", "coordinator": c is not None}


@app.get("/showcase", response_class=HTMLResponse)
async def showcase():
    return _serve_html("showcase.html")


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

@app.get("/tasks")
async def get_tasks():
    coordinator = _get_coordinator()
    return {
        "tasks": [
            {
                "task_id": t.task_id,
                "label": t.task_id.replace("_", " ").title(),
                "output_key": t.output_key or "",
                "parameters": t.parameters or {},
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
            "flavors": fmt.flavors,
            "parameters": [
                {"name": p.name, "type": p.type, "default": p.default, "description": p.description}
                for p in fmt.parameter_specs
            ],
        })
    return {"content_types": content_types}


@app.get("/services")
async def get_services():
    """List registered service names."""
    return {"services": get_runtime().services.keys()}


@app.get("/outputs")
async def get_outputs():
    return {"outputs": get_runtime().outputs.all()}


@app.post("/outputs/clear")
async def clear_outputs():
    get_runtime().outputs.clear()
    return {"status": "cleared"}


# ---------------------------------------------------------------------------
# Server-Sent Events (SSE) for real-time agent activity
# ---------------------------------------------------------------------------

async def _sse_generator(request: Request):
    bus = get_event_bus()
    async with bus.subscribe() as queue:
        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15)
                yield f"data: {_json.dumps(event, default=str)}\n\n"
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"


@app.get("/events")
async def sse_events(request: Request):
    return StreamingResponse(
        _sse_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Generic task execution
# ---------------------------------------------------------------------------

@app.post("/task/{task_id}", response_model=AgentResponse)
async def run_task(task_id: str, request: AgentRequest):
    request_id = str(uuid.uuid4())
    coordinator = _get_coordinator()

    task = coordinator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Unknown task: {task_id}")

    params = dict(request.parameters)

    try:
        result = await coordinator.process_task(task_id, params)

        output_key = task.output_key or ""
        content = result
        stages: List[Dict[str, Any]] = []

        if isinstance(result, dict) and "stages" in result:
            stages = result.get("stages", [])
            content = result.get("content", result)
            if output_key:
                get_runtime().outputs.set(output_key, content)
        elif output_key:
            get_runtime().outputs.set(output_key, result)

        return AgentResponse(
            request_id=request_id,
            task_id=task_id,
            output_key=output_key,
            content=content if isinstance(content, dict) else {"result": content},
            stages=stages,
            status="completed",
        )
    except Exception as e:
        logger.error("Task %s error: %s", task_id, e)
        return AgentResponse(
            request_id=request_id,
            task_id=task_id,
            content={"error": str(e), "status": "failed"},
            status="error",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
