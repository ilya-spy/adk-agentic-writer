"""In-process event bus for streaming agent lifecycle events to SSE clients.

Uses asyncio.Queue per subscriber so multiple SSE connections each get
every event independently.  All public helpers are safe to call from
any coroutine; the bus itself is a process-wide singleton.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional, Set

_bus: Optional["EventBus"] = None


class EventBus:
    """Fan-out event bus backed by per-subscriber asyncio.Queues."""

    def __init__(self) -> None:
        self._subscribers: Set[asyncio.Queue] = set()

    def emit(self, event: Dict[str, Any]) -> None:
        event.setdefault("ts", time.time())
        for q in self._subscribers:
            q.put_nowait(event)

    @asynccontextmanager
    async def subscribe(self) -> AsyncIterator[asyncio.Queue]:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(q)
        try:
            yield q
        finally:
            self._subscribers.discard(q)


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus


def emit_event(
    category: str,
    message: str,
    *,
    level: str = "info",
    **extra: Any,
) -> None:
    """Convenience: emit a structured event to all SSE subscribers."""
    get_event_bus().emit({
        "category": category,
        "message": message,
        "level": level,
        **extra,
    })
