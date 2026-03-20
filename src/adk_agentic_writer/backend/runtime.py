"""Multi-store runtime, agent graph assembly, and app lifespan."""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI

from ..agents.coordinator import CoordinatorService
from ..agents.publisher import PublisherAgentService
from ..agents.ideator import IdeatorAgentService, create_ideator
from ..agents.refiner import RefinerAgentService, create_refiner
from ..agents.reviewer import ReviewerAgentService, create_reviewer
from ..agents.writer import WriterAgentService, create_writer

from ..formats import list_formats
from ..workflows.tools import exit_loop

logger = logging.getLogger(__name__)


class NamedStore:
    """Simple typed key-value store."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def keys(self) -> List[str]:
        return list(self._data.keys())

    def all(self) -> Dict[str, Any]:
        return dict(self._data)

    def clear(self) -> None:
        self._data.clear()


class RuntimeStore:
    """Holds multiple named sub-stores.

    Built-in stores:
      - ``outputs``  -- task output_keys (draft_content, review_result, etc.)
      - ``agents``   -- raw ADK Agent instances (created by factory functions)
      - ``services`` -- BaseAgentService instances (high-level wrappers)
    """

    def __init__(self) -> None:
        self._stores: Dict[str, NamedStore] = {}

    def store(self, name: str) -> NamedStore:
        """Get or create a named sub-store."""
        if name not in self._stores:
            self._stores[name] = NamedStore()
        return self._stores[name]

    @property
    def outputs(self) -> NamedStore:
        return self.store("outputs")

    @property
    def agents(self) -> NamedStore:
        return self.store("agents")

    @property
    def services(self) -> NamedStore:
        return self.store("services")


# ---------------------------------------------------------------------------
# Process-wide singletons (populated in lifespan)
# ---------------------------------------------------------------------------

_runtime = RuntimeStore()


def get_runtime() -> RuntimeStore:
    return _runtime


def get_coordinator() -> Optional[CoordinatorService]:
    return _runtime.services.get("coordinator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing ADK agent system...")
    try:
        # -- Raw ADK agents via factories (used in pipeline composition) --
        ideator_adk = create_ideator()
        reviewer_adk = create_reviewer()
        refiner_adk = create_refiner(exit_loop)
        writers_adk = {fmt.name: create_writer(fmt) for fmt in list_formats()}

        _runtime.agents.set("ideator", ideator_adk)
        _runtime.agents.set("reviewer", reviewer_adk)
        _runtime.agents.set("refiner", refiner_adk)
        _runtime.agents.set("writers", writers_adk)

        # -- Leaf services (self-contained, handle individual tasks) --
        ideator = IdeatorAgentService()
        writer = WriterAgentService()
        reviewer = ReviewerAgentService()

        # -- Composite services (receive ADK agents for pipeline composition) --
        refiner = RefinerAgentService(reviewer_adk, refiner_adk)
        publisher = PublisherAgentService(
            ideator_adk,
            writers_adk,
            reviewer_adk,
            refiner_adk,
        )

        _runtime.services.set("ideator", ideator)
        _runtime.services.set("writer", writer)
        _runtime.services.set("reviewer", reviewer)
        _runtime.services.set("refiner", refiner)
        _runtime.services.set("publisher", publisher)

        # -- Routing service --
        coordinator = CoordinatorService(
            sub_agents=[ideator, writer, reviewer, refiner, publisher],
        )
        _runtime.services.set("coordinator", coordinator)

        logger.info(
            "Agent system assembled: agents=%s, services=%s",
            _runtime.agents.keys(),
            _runtime.services.keys(),
        )
    except Exception as e:
        logger.error("Failed to initialize agent system: %s", e)
    yield
    logger.info("Shutting down ADK agent system...")
    _runtime.agents.clear()
    _runtime.services.clear()
    _runtime.outputs.clear()
