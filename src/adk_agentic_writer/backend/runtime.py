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
        refiner = RefinerAgentService()

        # -- Publish pipeline needs dedicated agent instances (ADK agents
        #    can only belong to one parent) --
        from ..agents.ideator import create_ideator_pipeline
        from ..agents.writer import create_lead_writer_pipeline
        from ..agents.reviewer import create_reviewer_pipeline
        from ..agents.refiner import create_refiner_pipeline
        from ..agents.verifier import create_verifier_pipeline
        from ..workflows.tools import exit_loop

        publisher = PublisherAgentService(
            ideator=create_ideator_pipeline(),
            writer=create_lead_writer_pipeline(),
            reviewer=create_reviewer_pipeline(),
            refiner=create_refiner_pipeline(exit_loop),
            verifier=create_verifier_pipeline(),
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
        logger.error("Failed to initialize agent system: %s", e, exc_info=True)
    yield
    logger.info("Shutting down ADK agent system...")
    _runtime.services.clear()
    _runtime.outputs.clear()
