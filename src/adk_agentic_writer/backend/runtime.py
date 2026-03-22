"""Multi-store runtime, service graph assembly, and app lifespan."""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI

from ..agents.coordinator import CoordinatorService
from ..agents.ideator import IdeatorAgentService
from ..agents.writer import WriterAgentService
from ..agents.reviewer import ReviewerAgentService
from ..agents.refiner import RefinerAgentService
from ..agents.verifier import VerifierAgentService
from ..agents.publisher import PublisherAgentService

logger = logging.getLogger(__name__)

BACKEND_LLM = "gemini-2.5-flash"


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
        # -- Leaf services (create their own ADK agents internally) --
        ideator = IdeatorAgentService()
        writer = WriterAgentService()
        reviewer = ReviewerAgentService()
        verifier = VerifierAgentService()
        [ideator_adk] = ideator.get_agents("pipeline")
        [reviewer_adk] = reviewer.get_agents("pipeline")
        [verifier_adk] = verifier.get_agents("pipeline")

        # -- Composite services (receive pipeline ADK agents) --
        refiner = RefinerAgentService(reviewer_adk)
        [refiner_adk] = refiner.get_agents("pipeline")

        publisher = PublisherAgentService(
            ideator_adk,
            writer.get_agents("pipeline"),
            reviewer_adk,
            refiner_adk,
            verifier_adk,
        )

        _runtime.services.set("ideator", ideator)
        _runtime.services.set("writer", writer)
        _runtime.services.set("reviewer", reviewer)
        _runtime.services.set("verifier", verifier)
        _runtime.services.set("refiner", refiner)
        _runtime.services.set("publisher", publisher)

        # -- Routing service --
        coordinator = CoordinatorService(
            sub_agents=[publisher, ideator, writer, reviewer, verifier, refiner],
        )
        _runtime.services.set("coordinator", coordinator)

        logger.info(
            "Agent system assembled: services=%s",
            _runtime.services.keys(),
        )
    except Exception as e:
        logger.error("Failed to initialize agent system: %s", e)
    yield
    logger.info("Shutting down ADK agent system...")
    _runtime.services.clear()
    _runtime.outputs.clear()
