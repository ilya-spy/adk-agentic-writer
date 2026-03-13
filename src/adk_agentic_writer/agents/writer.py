"""Pure ADK writer agent for content generation.

Uses google.adk.agents.Agent + InMemoryRunner directly,
following the Kaggle Day 1a pattern. Builds prompts from
teams/content_team.py configs and content_registry schema descriptions.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

from ..utils.proxy_utils import clear_proxy_env

clear_proxy_env()

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

from ..teams.content_team import get_config_for_role, CONTENT_WRITER
from ..utils.content_registry import CONTENT_REGISTRY
from ..utils.log_config import log_llm_prompt, log_llm_response
from .adk_utils import extract_text, parse_json

logger = logging.getLogger(__name__)


class WriterAgent:
    """ADK-powered content writer.

    Creates one ADK Agent per content type (lazy), reusing it across calls.
    Prompt construction uses the existing AgentConfig generation_prompt +
    schema descriptions from CONTENT_REGISTRY.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash-lite"):
        if not os.environ.get("GOOGLE_API_KEY"):
            raise RuntimeError("GOOGLE_API_KEY not set")

        self._model_name = model_name
        self._agents: Dict[str, Agent] = {}
        self._runners: Dict[str, InMemoryRunner] = {}
        logger.info("WriterAgent initialized (model=%s)", model_name)

    def _ensure_agent(self, content_type: str) -> InMemoryRunner:
        """Lazily create an ADK Agent + Runner for a content type."""
        if content_type in self._runners:
            return self._runners[content_type]

        try:
            config = get_config_for_role(content_type)
        except ValueError:
            config = CONTENT_WRITER

        agent = Agent(
            name=f"writer_{content_type}",
            model=self._model_name,
            description=f"Generates {content_type} content as structured JSON.",
            instruction=config.instruction,
        )
        runner = InMemoryRunner(agent=agent)

        self._agents[content_type] = agent
        self._runners[content_type] = runner
        logger.info("Created ADK agent: writer_%s", content_type)
        return runner

    def _build_prompt(
        self, content_type: str, params: Dict[str, Any]
    ) -> str:
        """Build generation prompt from config + registry schema."""
        try:
            config = get_config_for_role(content_type)
        except ValueError:
            config = CONTENT_WRITER

        type_config = CONTENT_REGISTRY.get(content_type)

        merged = {}
        if type_config:
            merged.update(type_config.default_params)
        merged.update(params)

        try:
            prompt = config.generation_prompt.format(**merged)
        except KeyError as exc:
            logger.warning("Prompt template key missing: %s – using raw", exc)
            prompt = config.generation_prompt

        if type_config and type_config.schema_description:
            prompt += f"\n\n{type_config.schema_description}"
        if type_config and type_config.sample_output:
            prompt += (
                f"\n\nExample output:\n"
                f"{json.dumps(type_config.sample_output, indent=2)}"
            )

        alias = merged.get("content_type_alias", "")
        if alias:
            prompt += f"\n\nStyle hint: make the output feel more like a {alias.replace('_', ' ')}."

        return prompt

    async def generate(
        self,
        content_type: str,
        topic: str = "general",
        **params: Any,
    ) -> Dict[str, Any]:
        """Generate content for a given type and topic.

        Returns parsed JSON dict from the LLM.
        """
        params["topic"] = topic
        if "content_type" not in params:
            params["content_type"] = content_type

        prompt = self._build_prompt(content_type, params)
        runner = self._ensure_agent(content_type)

        agent_name = f"writer_{content_type}"
        log_llm_prompt(logger, agent_name, prompt)

        response = await runner.run_debug(prompt, quiet=True)
        text = extract_text(response)
        result = parse_json(text, agent_name=agent_name)

        log_llm_response(logger, agent_name, result)
        return result


__all__ = ["WriterAgent"]
