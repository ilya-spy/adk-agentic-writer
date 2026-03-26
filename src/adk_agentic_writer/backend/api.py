"""FastAPI backend -- task-driven API for the ADK Agentic Writer."""

from ..utils.proxy import clear_proxy_env

clear_proxy_env()

import asyncio
import json as _json
import logging
import pathlib
import time
import uuid
from typing import Any, Dict, List, Optional

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

from ..agents.base import SESSION_APP_NAME
from ..agents.coordinator import CoordinatorService
from .runtime import get_runtime, get_coordinator, get_session_service, lifespan


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class AgentRequest(BaseModel):
    """All task parameters go here."""
    parameters: Dict[str, Any] = {}
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    request_id: str
    task_id: str
    output_key: str = ""
    content: Dict[str, Any] = {}
    stages: List[Dict[str, Any]] = []
    status: str = "completed"
    session_id: Optional[str] = None


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


@app.get("/content-renderer.js")
async def content_renderer_js():
    from starlette.responses import Response

    path = _PROJECT_ROOT / "frontend" / "public" / "content-renderer.js"
    if path.exists():
        return Response(path.read_text(encoding="utf-8"), media_type="application/javascript")
    return Response("// not found", status_code=404, media_type="application/javascript")


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
# Session management
# ---------------------------------------------------------------------------

@app.get("/sessions")
async def list_sessions():
    """List active sessions in the shared InMemorySessionService."""
    svc = get_session_service()
    result = await svc.list_sessions(app_name=SESSION_APP_NAME, user_id="default")
    return {
        "sessions": [
            {"session_id": s.id, "app_name": s.app_name, "events": len(s.events)}
            for s in result.sessions
        ]
    }


@app.get("/sessions/{session_id}")
async def get_session_detail(session_id: str):
    """Return session events for debugging / session viewer."""
    svc = get_session_service()
    session = await svc.get_session(
        app_name=SESSION_APP_NAME, user_id="default", session_id=session_id,
    )
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    events_out = []
    for ev in session.events:
        text_parts = []
        role = ""
        if ev.content:
            role = ev.content.role or ""
            for p in (ev.content.parts or []):
                if p.text:
                    text_parts.append(p.text)
                elif p.function_call:
                    text_parts.append(f"[tool_call: {p.function_call.name}]")
                elif p.function_response:
                    text_parts.append(f"[tool_response: {p.function_response.name}]")
        events_out.append({
            "id": ev.id,
            "author": ev.author,
            "role": role,
            "text": "\n".join(text_parts) if text_parts else None,
            "timestamp": ev.timestamp,
            "turn_complete": ev.turn_complete,
        })
    return {
        "session_id": session.id,
        "app_name": session.app_name,
        "event_count": len(session.events),
        "state": dict(session.state) if session.state else {},
        "events": events_out,
    }


@app.post("/sessions")
async def create_session(name: Optional[str] = None):
    """Create a new named session (or auto-generate an id)."""
    svc = get_session_service()
    session_id = name or f"session_{uuid.uuid4().hex[:8]}"
    session = await svc.create_session(
        app_name=SESSION_APP_NAME, user_id="default", session_id=session_id,
    )
    return {"session_id": session.id, "app_name": session.app_name}


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
    session_id = request.session_id
    if session_id:
        params["session_id"] = session_id

    try:
        result = await coordinator.process_task(task_id, params)

        output_key = task.output_key or ""
        content = result
        stages: List[Dict[str, Any]] = []
        if isinstance(result, dict) and "session_id" in result:
            session_id = result.pop("session_id")

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
            session_id=session_id,
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
