"""Coordinator agent – orchestrates WriterAgent and ValidatorAgent.

Provides the public API consumed by backend/api.py:
- get_supported_tasks()
- resolve_task(task_id, content_type)
- get_all_content_types()
- process_task(task, params)
- process_with_validation(task, params)
"""

import logging
from typing import Any, Dict, List, Optional

from ..models.agent_models import AgentTask
from ..tasks.content_tasks import (
    GENERATE_QUIZ,
    GENERATE_STORY,
    GENERATE_GAME,
    GENERATE_SIMULATION,
)
from .writer import WriterAgent
from .validator import ValidatorAgent

logger = logging.getLogger(__name__)

_PRIMARY_TASKS: List[AgentTask] = [
    GENERATE_QUIZ,
    GENERATE_STORY,
    GENERATE_GAME,
    GENERATE_SIMULATION,
]


class Coordinator:
    """Lightweight coordinator that routes tasks to writer/validator.

    No LLM call for routing — task resolution is deterministic.
    The LLM work happens inside WriterAgent and ValidatorAgent.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash-lite"):
        self._writer = WriterAgent(model_name=model_name)
        self._validator = ValidatorAgent(model_name=model_name)
        self._tasks = list(_PRIMARY_TASKS)

        self._task_by_id: Dict[str, AgentTask] = {
            t.task_id: t for t in self._tasks
        }
        self._type_to_task: Dict[str, AgentTask] = {}
        for t in self._tasks:
            for ct in t.content_types:
                self._type_to_task[ct] = t

        logger.info(
            "Coordinator ready: %d tasks, %d content-type aliases",
            len(self._task_by_id),
            len(self._type_to_task),
        )

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def get_supported_tasks(self) -> List[AgentTask]:
        return list(self._tasks)

    def get_all_content_types(self) -> Dict[str, List[str]]:
        """Return {task_id: [content_type, ...]} mapping."""
        return {t.task_id: list(t.content_types) for t in self._tasks}

    def resolve_task(
        self,
        task_id: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Optional[AgentTask]:
        """Resolve a task by ID or content-type alias."""
        if task_id and task_id in self._task_by_id:
            return self._task_by_id[task_id]
        if content_type and content_type in self._type_to_task:
            return self._type_to_task[content_type]
        return None

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def process_task(
        self,
        task: AgentTask,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate content for a task (writer only, no validation)."""
        content_type = self._effective_content_type(task, params)
        topic = params.get("topic", "general")

        logger.info(
            "Processing task=%s content_type=%s topic=%r",
            task.task_id, content_type, topic,
        )

        result = await self._writer.generate(
            content_type=content_type,
            topic=topic,
            **params,
        )
        return result

    async def process_with_validation(
        self,
        task: AgentTask,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate content, then validate it. Returns combined result."""
        content = await self.process_task(task, params)
        content_type = self._effective_content_type(task, params)

        validation = await self._validator.validate(content, content_type)

        return {
            "content": content,
            "validation_result": validation,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _effective_content_type(
        task: AgentTask, params: Dict[str, Any]
    ) -> str:
        """Determine the canonical content type for a task + params."""
        ct = params.get("content_type")
        if ct:
            return ct
        if task.content_types:
            return task.content_types[0]
        return "quiz"


__all__ = ["Coordinator"]
