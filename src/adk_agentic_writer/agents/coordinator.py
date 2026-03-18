"""Coordinator -- LLM-powered root agent with sub-agents.

Inherits runner pool and task registry from BaseAgentService.
Adds orchestration: ideate, generate, review, refine, publish.
"""

import json
import logging
from typing import Any, Dict, List

from google.adk.agents import Agent

from ..formats import get_format, list_formats
from ..tasks.content_tasks import PRIMARY_TASKS
from .base import BaseAgentService, MODEL
from .ideator import create_ideator
from .writer import create_writer
from .reviewer import create_reviewer, schema_validate
from .refiner import create_refiner

logger = logging.getLogger(__name__)


class Coordinator(BaseAgentService):
    """LLM-powered coordinator with sub-agent orchestration.

    Creates all agent runners at init, delegates via direct methods.
    """

    def __init__(self, model_name: str = MODEL):
        super().__init__(model=model_name)
        self._register_tasks(PRIMARY_TASKS)

        self._ideator = create_ideator(model_name)
        self._writers: Dict[str, Agent] = {}
        for fmt in list_formats():
            self._writers[fmt.name] = create_writer(fmt, model_name)
        self._reviewer = create_reviewer(model_name)
        self._refiner = create_refiner(model_name)

        logger.info(
            "Coordinator ready: %d formats, %d task aliases",
            len(self._writers),
            len(self._type_to_task),
        )

    # ------------------------------------------------------------------
    # Action methods
    # ------------------------------------------------------------------

    async def ideate(self, prompt: str) -> Dict[str, Any]:
        runner = self._ensure_runner("ideator", self._ideator)
        return await self._run(runner, "IdeatorAgent", prompt)

    async def generate(self, content_type: str, prompt: str) -> Dict[str, Any]:
        fmt = get_format(content_type)
        writer_name = fmt.name if fmt else content_type
        writer = self._writers.get(writer_name)
        if not writer:
            writer = self._writers.get("quiz")
            logger.warning("Unknown format %r, falling back to quiz", content_type)

        runner = self._ensure_runner(f"writer_{writer_name}", writer)
        return await self._run(runner, writer.name, prompt)

    async def review(
        self, content: Dict[str, Any], content_type: str = "unknown",
    ) -> Dict[str, Any]:
        try:
            runner = self._ensure_runner("reviewer", self._reviewer)
            prompt = (
                f"Content type: {content_type}\n\n"
                f"Content to review:\n{json.dumps(content, indent=2, ensure_ascii=False)}"
            )
            result = await self._run(runner, "ReviewerAgent", prompt)
            result.setdefault("valid", len(result.get("errors", [])) == 0)
            result.setdefault("score", 100 if result["valid"] else 50)
            result.setdefault("errors", [])
            result.setdefault("warnings", [])
            result.setdefault("summary", "Review complete")
            return result
        except Exception as exc:
            logger.warning("LLM review failed, falling back to schema: %s", exc)
            return schema_validate(content, content_type)

    async def refine(
        self, content: Dict[str, Any], review_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        runner = self._ensure_runner("refiner", self._refiner)
        prompt = (
            f"Content to refine:\n{json.dumps(content, indent=2, ensure_ascii=False)}\n\n"
            f"Review feedback:\n{json.dumps(review_result, indent=2, ensure_ascii=False)}"
        )
        return await self._run(runner, "RefinerAgent", prompt)

    async def publish(self, content_type: str, prompt: str) -> Dict[str, Any]:
        stages: List[Dict[str, Any]] = []

        draft = await self.generate(content_type, prompt)
        stages.append({"stage": "generate", "output": draft})

        review = await self.review(draft, content_type)
        stages.append({"stage": "review", "output": review})

        if not review.get("valid", True) or review.get("score", 100) < 90:
            refined = await self.refine(draft, review)
            stages.append({"stage": "refine", "output": refined})
            final_content = refined
        else:
            final_content = draft

        return {
            "content": final_content,
            "validation_result": review,
            "stages": stages,
        }

    # ------------------------------------------------------------------
    # Legacy compat
    # ------------------------------------------------------------------

    async def process_task(self, task, params: Dict[str, Any]) -> Dict[str, Any]:
        content_type = self._effective_content_type(task, params)
        topic = params.get("topic", "general")
        fmt = get_format(content_type) or get_format("quiz")

        merged = dict(fmt.default_params) if fmt else {}
        merged.update(params)
        merged["topic"] = topic

        try:
            prompt_text = fmt.writer_prompt.format(**merged)
        except KeyError:
            prompt_text = f"Generate {content_type} content about {topic}."

        return await self.generate(content_type, prompt_text)

    async def process_with_validation(self, task, params: Dict[str, Any]) -> Dict[str, Any]:
        content = await self.process_task(task, params)
        content_type = self._effective_content_type(task, params)
        validation = await self.review(content, content_type)
        return {"content": content, "validation_result": validation}


__all__ = ["Coordinator"]
