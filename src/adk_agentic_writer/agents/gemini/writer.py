"""Gemini-powered writer agent using Google ADK.

LLM-only implementation for quiz and story generation.
Requires GOOGLE_API_KEY environment variable.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from ...models.agent_models import AgentConfig, AgentModel, AgentTask, AgentStatus
from ...models.content_models import (
    ContentBlock,
    ContentBlockType,
    ContentPattern,
    Quiz,
    QuizQuestion,
    BranchedNarrative,
    StoryNode,
)
from ...tasks.content_tasks import GENERATE_QUIZ, GENERATE_STORY
from ...teams.content_team import get_config_for_role
from ...utils.content_registry import CONTENT_REGISTRY
from ..content_agent import ContentWriterAgent

logger = logging.getLogger(__name__)

# ADK imports
try:
    from google.adk.agents import Agent
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False


class ADKAgentWrapper:
    """Wrapper for ADK Agent with InMemoryRunner."""

    def __init__(self, name: str, config: AgentConfig, model_name: str):
        if not ADK_AVAILABLE:
            raise RuntimeError("Google ADK not installed. Run: pip install google-adk")
        if not os.environ.get("GOOGLE_API_KEY"):
            raise RuntimeError(
                "GOOGLE_API_KEY not set. Get key at: https://aistudio.google.com/app/apikey"
            )

        self.name = name
        self.config = config
        self.model_name = model_name
        self._agent: Optional[Agent] = None
        self._runner: Optional[InMemoryRunner] = None

    async def _ensure_initialized(self) -> None:
        """Initialize ADK agent on first use."""
        if self._agent is not None:
            return

        self._agent = Agent(
            name=self.name,
            model=self.model_name,
            instruction=self.config.instruction,
        )
        self._runner = InMemoryRunner(agent=self._agent)
        logger.info(f"Initialized ADK agent: {self.name}")

    async def run(self, prompt: str) -> Dict[str, Any]:
        """Run agent with prompt and return parsed JSON response."""
        await self._ensure_initialized()

        response = await self._runner.run_debug(prompt)

        # Extract text from response
        if hasattr(response, "text"):
            text = response.text
        elif isinstance(response, str):
            text = response
        else:
            text = str(response)

        return self._parse_json(text)

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON from response, handling markdown code blocks."""
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}\nRaw: {text[:500]}")


class GeminiWriterAgent(ContentWriterAgent):
    """Gemini-powered writer for quiz and story generation.

    Uses ADK Agent with prompts from content_team and CONTENT_REGISTRY.
    """

    def __init__(
        self,
        agent_id: str = "gemini_writer",
        content_type: str = "quiz",
        model_name: str = "gemini-2.5-flash-lite",
    ):
        # Get content type config from registry
        type_config = CONTENT_REGISTRY.get(content_type)
        if not type_config:
            raise ValueError(f"Unknown content type: {content_type}")
        if type_config.category != "writer":
            raise ValueError(f"Content type '{content_type}' is not a writer type")

        self._type_config = type_config
        self._content_type = content_type
        self._model_name = model_name

        # Get role config with prompts
        role_config = get_config_for_role(content_type)

        # Create AgentModel
        model = AgentModel(
            name=agent_id,
            model_name=model_name,
            parameters={"content_type": content_type},
        )

        super().__init__(
            agent_id=agent_id,
            config=role_config,
            model=model,
            text_provider=None,  # Not using text_provider
        )

        self.supported_tasks.extend([GENERATE_QUIZ, GENERATE_STORY])
        self._adk_agent: Optional[ADKAgentWrapper] = None

        logger.info(f"Initialized GeminiWriterAgent: {agent_id} ({content_type})")

    @property
    def content_type(self) -> str:
        return self._content_type

    async def _get_agent(self) -> ADKAgentWrapper:
        """Get or create ADK agent."""
        if self._adk_agent is None:
            self._adk_agent = ADKAgentWrapper(
                name=f"{self.agent_id}_generator",
                config=self.config,
                model_name=self._model_name,
            )
        return self._adk_agent

    # =========================================================================
    # Task Execution
    # =========================================================================

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute content generation task."""
        context = self.prepare_task_context(task)
        return await self._generate_content(context)

    async def _generate_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete content using LLM."""
        prompt = self.build_generation_prompt(
            context=context,
            schema_description=self._type_config.schema_description,
            sample_output=self._type_config.sample_output,
        )

        agent = await self._get_agent()
        await self.update_status(AgentStatus.WORKING)

        result = await agent.run(prompt)

        await self.update_status(AgentStatus.COMPLETED)
        return result

    # =========================================================================
    # Quiz Generation
    # =========================================================================

    async def generate_question(
        self, topic: str = "general", difficulty: str = "medium", **_
    ) -> QuizQuestion:
        """Generate a complete quiz question via LLM."""
        prompt = self.get_prompt(
            "quiz_question_complete", {"topic": topic, "difficulty": difficulty}
        )
        if not prompt:
            raise ValueError("Missing 'quiz_question_complete' prompt template")

        agent = await self._get_agent()
        result = await agent.run(prompt)

        return QuizQuestion(
            question=result["question"],
            options=result["options"],
            correct_answer=result["correct_answer"],
            explanation=result["explanation"],
            difficulty=result.get("difficulty", difficulty),
        )

    async def generate_quiz(
        self, topic: str, num_questions: int = 5, difficulty: str = "medium", **params
    ) -> Quiz:
        """Generate a complete quiz via LLM."""
        context = {
            "topic": topic,
            "num_questions": num_questions,
            "difficulty": difficulty,
            **params,
        }

        result = await self._generate_content(context)

        return Quiz(
            title=result.get(
                "title", self._type_config.title_template.format(topic=topic.title())
            ),
            description=result.get(
                "description",
                self._type_config.description_template.format(topic=topic),
            ),
            questions=result.get("questions", []),
            passing_score=result.get("passing_score", params.get("passing_score", 70)),
            time_limit=result.get("time_limit"),
        )

    # =========================================================================
    # Story Generation
    # =========================================================================

    async def generate_story_node(
        self,
        node_id: str,
        topic: str = "adventure",
        genre: str = "fantasy",
        available_nodes: Optional[List[str]] = None,
        is_ending: bool = False,
        **kwargs,
    ) -> StoryNode:
        """Generate a complete story node via LLM."""
        if is_ending:
            # Endings have no branches
            prompt = self.get_prompt(
                "story_ending",
                {
                    "topic": topic,
                    "genre": genre,
                    "ending_type": kwargs.get("ending_type", "neutral"),
                },
            )
            agent = await self._get_agent()
            # For endings, we just need text content
            result = await agent.run(prompt)
            content = result.get("content", result.get("raw", str(result)))
            if isinstance(content, dict):
                content = content.get("text", str(content))

            return StoryNode(
                node_id=node_id,
                content=str(content)[:500],
                branches=[],
                tags=kwargs.get("tags", ["ending"]),
                is_ending=True,
            )

        # Non-ending nodes with branches
        prompt = self.get_prompt(
            "story_node_complete",
            {
                "topic": topic,
                "genre": genre,
                "node_id": node_id,
                "node_type": "opening" if node_id == "start" else "middle",
                "available_nodes": ", ".join(available_nodes or []),
            },
        )
        if not prompt:
            raise ValueError("Missing 'story_node_complete' prompt template")

        agent = await self._get_agent()
        result = await agent.run(prompt)

        return StoryNode(
            node_id=result.get("node_id", node_id),
            content=result["content"],
            branches=result.get("branches", []),
            tags=result.get("tags", kwargs.get("tags", [])),
            is_ending=False,
        )

    async def generate_story(
        self, topic: str, genre: str = "fantasy", num_nodes: int = 7, **params
    ) -> BranchedNarrative:
        """Generate a complete branched story via LLM."""
        num_endings = min(3, max(1, num_nodes // 3))

        prompt = self.get_prompt(
            "story_structure",
            {
                "topic": topic,
                "genre": genre,
                "num_nodes": num_nodes,
                "num_endings": num_endings,
            },
        )
        if not prompt:
            raise ValueError("Missing 'story_structure' prompt template")

        agent = await self._get_agent()
        await self.update_status(AgentStatus.WORKING)
        result = await agent.run(prompt)

        # Parse nodes
        nodes = {}
        for node_id, node_data in result.get("nodes", {}).items():
            nodes[node_id] = StoryNode(
                node_id=node_data.get("node_id", node_id),
                content=node_data["content"],
                branches=node_data.get("branches", []),
                tags=node_data.get("tags", []),
                is_ending=node_data.get("is_ending", False),
            )

        if "start" not in nodes:
            raise ValueError("LLM response missing 'start' node")

        await self.update_status(AgentStatus.COMPLETED)

        return BranchedNarrative(
            title=result.get(
                "title", self._type_config.title_template.format(topic=topic.title())
            ),
            synopsis=result.get(
                "synopsis", self._type_config.description_template.format(topic=topic)
            ),
            genre=genre,
            start_node="start",
            nodes={k: v.model_dump() for k, v in nodes.items()},
            characters=result.get("characters", ["Protagonist"]),
        )

    # =========================================================================
    # ContentProtocol Implementation
    # =========================================================================

    async def generate_block(
        self,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        previous_blocks: Optional[List[ContentBlock]] = None,
    ) -> ContentBlock:
        """Generate a single content block."""
        block_id = context.get("block_id", f"{block_type.value}_{id(context)}")

        if block_type == ContentBlockType.QUESTION:
            content = (await self.generate_question(**context)).model_dump()
        elif block_type == ContentBlockType.NODE:
            content = (await self.generate_story_node(**context)).model_dump()
        else:
            raise ValueError(f"Unsupported block type: {block_type}")

        return ContentBlock(
            block_id=block_id,
            block_type=block_type,
            content=content,
            pattern=context.get("pattern", ContentPattern.SEQUENTIAL),
            metadata=context.get("metadata", {}),
        )


# Convenience aliases
class GeminiQuizWriterAgent(GeminiWriterAgent):
    """Quiz-specialized Gemini writer."""

    def __init__(self, agent_id: str = "gemini_quiz_writer"):
        super().__init__(agent_id=agent_id, content_type="quiz")


class GeminiStoryWriterAgent(GeminiWriterAgent):
    """Story-specialized Gemini writer."""

    def __init__(self, agent_id: str = "gemini_story_writer"):
        super().__init__(agent_id=agent_id, content_type="story")


__all__ = [
    "GeminiWriterAgent",
    "GeminiQuizWriterAgent",
    "GeminiStoryWriterAgent",
    "ADKAgentWrapper",
]
