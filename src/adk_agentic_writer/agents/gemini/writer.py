"""Gemini-powered writer agent using Google ADK.

Implements real AI generation via ADK Agent with:
- InMemoryRunner for session management
- Structured JSON output via config schema_description
- Support for quiz and story content types
- Prompts and instructions from AgentConfig
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

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
from ...teams.content_team import get_config_for_role, QUIZ_WRITER, STORY_WRITER
from ...utils.content_registry import CONTENT_REGISTRY
from ..content_agent import ContentWriterAgent

logger = logging.getLogger(__name__)

# ADK imports - wrapped for graceful fallback
try:
    from google.adk.agents import Agent
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    logger.warning("Google ADK not available. Install with: pip install google-adk")


def _check_api_key() -> bool:
    """Check if GOOGLE_API_KEY is configured."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning(
            "GOOGLE_API_KEY not set. Set it in .env or environment. "
            "Get your key at: https://aistudio.google.com/app/apikey"
        )
        return False
    return True


class ADKAgentWrapper:
    """Wrapper for ADK Agent with InMemoryRunner.

    Handles:
    - Agent initialization with system instruction from AgentConfig
    - Session management via InMemoryRunner
    - Async execution with structured output
    """

    def __init__(
        self,
        name: str,
        config: AgentConfig,
        model_name: str = "gemini-2.5-flash-lite",
    ):
        self.name = name
        self.config = config
        self.model_name = model_name
        self._agent: Optional[Any] = None
        self._runner: Optional[Any] = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize ADK agent and runner."""
        if not ADK_AVAILABLE:
            logger.error("ADK not available")
            return False

        if not _check_api_key():
            return False

        try:
            # Configure retry options
            retry_config = types.HttpRetryOptions(
                attempts=3,
                exp_base=2,
                initial_delay=1,
                http_status_codes=[429, 500, 503, 504],
            )

            # Create ADK Agent with instruction from config
            self._agent = Agent(
                name=self.name,
                model=self.model_name,
                instruction=self.config.instruction,
            )

            # Create InMemoryRunner
            self._runner = InMemoryRunner(agent=self._agent)
            self._initialized = True
            logger.info(f"Initialized ADK agent: {self.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize ADK agent: {e}")
            return False

    async def run(self, prompt: str) -> Dict[str, Any]:
        """Run agent with prompt and return response."""
        if not self._initialized:
            if not await self.initialize():
                raise RuntimeError("Failed to initialize ADK agent")

        try:
            response = await self._runner.run_debug(prompt)

            # Extract text response
            if hasattr(response, "text"):
                return self._parse_json_response(response.text)
            elif isinstance(response, str):
                return self._parse_json_response(response)
            else:
                content = str(response)
                return self._parse_json_response(content)

        except Exception as e:
            logger.error(f"ADK agent run failed: {e}")
            raise

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from agent response, handling markdown code blocks."""
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {text[:500]}")
            return {"error": "Failed to parse JSON", "raw": text[:1000]}


class GeminiTextProvider:
    """LLM-powered text provider using ADK agents.

    Uses prompt templates from AgentConfig for text generation.
    """

    def __init__(
        self,
        config: AgentConfig,
        model_name: str = "gemini-2.5-flash-lite",
    ):
        self.config = config
        self.model_name = model_name
        self._agent: Optional[ADKAgentWrapper] = None

    async def _ensure_agent(self) -> ADKAgentWrapper:
        """Ensure ADK agent is initialized."""
        if self._agent is None:
            self._agent = ADKAgentWrapper(
                name="text_generator",
                config=self.config,
                model_name=self.model_name,
            )
        return self._agent

    def _get_prompt(self, key: str, context: Dict[str, Any]) -> str:
        """Get prompt template from config with variable substitution."""
        template = self.config.prompt_templates.get(key, "")
        if not template:
            return ""
        try:
            return template.format(**context)
        except KeyError:
            return template

    async def generate_text(self, prompt_key: str, context: Dict[str, Any]) -> str:
        """Generate text using ADK agent with config prompt templates."""
        if not ADK_AVAILABLE or not _check_api_key():
            # Fallback to template
            from ...utils.text_provider import TemplateTextProvider

            fallback = TemplateTextProvider()
            return await fallback.generate_text(prompt_key, context)

        # Get prompt from config templates
        prompt = self._get_prompt(prompt_key, context)
        if not prompt:
            # Fallback if template not defined
            topic = context.get("topic", "the subject")
            prompt = f"Generate content about {topic} for {prompt_key}."

        try:
            agent = await self._ensure_agent()
            result = await agent.run(prompt)
            if isinstance(result, dict):
                # For text prompts, try to get raw text
                if "error" not in result:
                    return str(result.get("text", result.get("content", str(result))))
                # Parse error, return raw
                return result.get("raw", str(result))[:500]
            return str(result)
        except Exception as e:
            logger.warning(f"ADK text generation failed: {e}, using fallback")
            from ...utils.text_provider import TemplateTextProvider

            fallback = TemplateTextProvider()
            return await fallback.generate_text(prompt_key, context)


class GeminiWriterAgent(ContentWriterAgent):
    """Gemini-powered writer agent for quiz and story generation.

    Uses ADK Agent with InMemoryRunner for real AI generation.
    Prompts and instructions come from AgentConfig in content_team.py.
    Falls back to static templates if ADK is unavailable.
    """

    def __init__(
        self,
        agent_id: str = "gemini_writer",
        content_type: str = "quiz",
        model_name: str = "gemini-2.5-flash-lite",
    ):
        self._content_type = content_type
        self._model_name = model_name

        # Get content type config from registry (for title templates, etc.)
        type_config = CONTENT_REGISTRY.get(content_type)
        if not type_config:
            raise ValueError(f"Unknown content type: {content_type}")
        if type_config.category != "writer":
            raise ValueError(f"Content type '{content_type}' is not a writer type")
        self._type_config = type_config

        # Get role config with prompts from content_team
        role_config = get_config_for_role(content_type)

        # Initialize with Gemini text provider using role config
        text_provider = GeminiTextProvider(config=role_config, model_name=model_name)

        # Create AgentModel matching ADK structure
        model = AgentModel(
            name=agent_id,
            model_name=model_name,
            parameters={"content_type": content_type},
        )

        super().__init__(
            agent_id=agent_id,
            config=role_config,
            model=model,
            text_provider=text_provider,
        )

        # Publish supported tasks
        self.supported_tasks.extend([GENERATE_QUIZ, GENERATE_STORY])

        # ADK agent wrapper for full content generation
        self._adk_agent: Optional[ADKAgentWrapper] = None
        self._use_adk = ADK_AVAILABLE and _check_api_key()

        logger.info(
            f"Initialized GeminiWriterAgent {agent_id} "
            f"(ADK: {'enabled' if self._use_adk else 'disabled'})"
        )

    @property
    def content_type(self) -> str:
        return self._content_type

    @property
    def adk_enabled(self) -> bool:
        """Check if ADK is available and configured."""
        return self._use_adk

    async def _get_adk_agent(self) -> ADKAgentWrapper:
        """Get or create ADK agent using config."""
        if self._adk_agent is None:
            self._adk_agent = ADKAgentWrapper(
                name=f"{self.agent_id}_generator",
                config=self.config,
                model_name=self._model_name,
            )
        return self._adk_agent

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute task using ADK for content generation."""
        context = self.prepare_task_context(task)

        if self._use_adk:
            try:
                return await self._build_content_with_adk(context)
            except Exception as e:
                logger.warning(f"ADK generation failed: {e}, falling back to static")

        # Fallback to static generation
        return await self._build_content(context)

    async def _build_content_with_adk(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build content using ADK agent with config-based prompts."""
        # Build generation prompt with schema from content registry
        prompt = self.build_generation_prompt(
            context=context,
            schema_description=self._type_config.schema_description,
            sample_output=self._type_config.sample_output,
        )

        # Get ADK agent
        agent = await self._get_adk_agent()

        # Run ADK agent
        await self.update_status(AgentStatus.WORKING)
        result = await agent.run(prompt)

        # Validate and return
        if "error" in result:
            raise ValueError(f"ADK generation error: {result.get('error')}")

        await self.update_status(AgentStatus.COMPLETED)
        return result

    async def _build_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback: Build content using templates."""
        params = {**self._type_config.default_params, **context}
        task_id = context.get("task_id", "")

        if "quiz" in task_id:
            return await self._build_quiz(params)
        elif "story" in task_id:
            return await self._build_story(params)
        return await self._build_generic(params)

    async def _build_quiz(self, p: Dict[str, Any]) -> Dict[str, Any]:
        """Build quiz content."""
        topic = p.get("topic", "general")
        num_q = p.get("num_questions", 5)
        difficulty = p.get("difficulty", "medium")

        questions = await self.generate_questions_set(topic, num_q, difficulty)
        return Quiz(
            title=self._type_config.title_template.format(topic=topic.title()),
            description=self._type_config.description_template.format(topic=topic),
            questions=[q.model_dump() for q in questions],
            passing_score=p.get("passing_score", 70),
            time_limit=p.get("time_limit"),
        ).model_dump()

    async def _build_story(self, p: Dict[str, Any]) -> Dict[str, Any]:
        """Build branched narrative content."""
        topic = p.get("topic", "adventure")
        genre = p.get("genre", "fantasy")
        num_nodes = p.get("num_nodes", 7)

        nodes = await self.generate_story_nodes_set(topic, genre, num_nodes)
        return BranchedNarrative(
            title=self._type_config.title_template.format(topic=topic.title()),
            synopsis=self._type_config.description_template.format(topic=topic),
            genre=genre,
            start_node="start",
            nodes={k: v.model_dump() for k, v in nodes.items()},
            characters=["Protagonist", "Guide", "Antagonist"],
        ).model_dump()

    async def _build_generic(self, p: Dict[str, Any]) -> Dict[str, Any]:
        """Build generic content."""
        topic = p.get("topic", "general")
        return self._type_config.model_class(
            title=self._type_config.title_template.format(topic=topic.title()),
            description=self._type_config.description_template.format(topic=topic),
            **{k: v for k, v in p.items() if k != "topic"},
        ).model_dump()

    # ContentProtocol implementation
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
        elif block_type == ContentBlockType.CHAPTER:
            content = await self.generate_chapter(**context)
        else:
            content = {"text": context.get("text", ""), "data": context}

        return ContentBlock(
            block_id=block_id,
            block_type=block_type,
            content=content,
            pattern=context.get("pattern", ContentPattern.SEQUENTIAL),
            metadata=context.get("metadata", {}),
        )

    # Question generation
    async def generate_question(
        self,
        topic: str = "general",
        difficulty: str = "medium",
        question: Optional[str] = None,
        options: Optional[List[str]] = None,
        correct_answer: Optional[int] = None,
        explanation: Optional[str] = None,
        **_,
    ) -> QuizQuestion:
        """Create a quiz question with options."""
        import random

        ctx = {"topic": topic, "difficulty": difficulty}

        q_text = question or await self.generate_text("quiz_question", ctx)
        correct_idx = (
            correct_answer if correct_answer is not None else random.randint(0, 3)
        )

        if options:
            opts = options
        else:
            opts = []
            for i in range(4):
                key = "quiz_option_correct" if i == correct_idx else "quiz_option"
                opts.append(await self.generate_text(key, ctx))

        expl = explanation or await self.generate_text("quiz_explanation", ctx)
        return QuizQuestion(
            question=q_text,
            options=opts,
            correct_answer=correct_idx,
            explanation=expl,
            difficulty=difficulty,
        )

    async def generate_questions_set(
        self, topic: str, count: int = 5, difficulty: str = "medium"
    ) -> List[QuizQuestion]:
        """Generate a set of quiz questions."""
        return [await self.generate_question(topic, difficulty) for _ in range(count)]

    # Story node generation
    async def generate_story_node(
        self,
        node_id: str,
        content: Optional[str] = None,
        branches: Optional[List[Dict[str, str]]] = None,
        tags: Optional[List[str]] = None,
        is_ending: bool = False,
        **kwargs,
    ) -> StoryNode:
        """Create a story node with branches."""
        if content is None:
            ctx = {
                "topic": kwargs.get("topic", "adventure"),
                "genre": kwargs.get("genre", "fantasy"),
            }
            path_type = kwargs.get("path_type", "main")
            key = (
                "story_ending"
                if is_ending
                else ("story_opening" if node_id == "start" else "story_path")
            )
            if key == "story_path":
                ctx["path_type"] = path_type
            if key == "story_ending":
                ctx["ending_type"] = kwargs.get("ending_type", "neutral")
            content = await self.generate_text(key, ctx)

        return StoryNode(
            node_id=node_id,
            content=content,
            branches=branches or [],
            tags=tags or [],
            is_ending=is_ending,
        )

    async def generate_story_nodes_set(
        self, topic: str, genre: str = "fantasy", num_nodes: int = 7
    ) -> Dict[str, StoryNode]:
        """Generate connected story nodes with branches."""
        nodes = {}
        ctx = {"topic": topic, "genre": genre}

        num_nodes = max(2, num_nodes)
        num_middle = max(0, num_nodes - 2)
        num_endings = min(3, max(1, num_nodes // 3))

        # Start node
        middle_branches = []
        for i in range(min(2, num_middle)):
            middle_branches.append({"text": f"Path {i+1}", "next_node_id": f"node_{i}"})
        if not middle_branches:
            middle_branches.append({"text": "Continue", "next_node_id": "ending_0"})

        nodes["start"] = await self.generate_story_node(
            "start", tags=["opening", genre], branches=middle_branches, **ctx
        )

        # Middle nodes
        for i in range(num_middle):
            is_last_middle = i >= num_middle - num_endings
            if is_last_middle:
                ending_idx = i - (num_middle - num_endings)
                branches = [
                    {"text": "Reach conclusion", "next_node_id": f"ending_{ending_idx}"}
                ]
            else:
                branches = [{"text": "Continue", "next_node_id": f"node_{i+1}"}]
                if i + 2 < num_middle:
                    branches.append(
                        {"text": "Skip ahead", "next_node_id": f"node_{i+2}"}
                    )

            nodes[f"node_{i}"] = await self.generate_story_node(
                f"node_{i}",
                tags=[f"chapter_{i+1}"],
                path_type=f"path_{i}",
                branches=branches,
                **ctx,
            )

        # Endings
        ending_types = ["victory", "alliance", "wisdom", "mystery", "tragic"]
        for i in range(num_endings):
            etype = ending_types[i % len(ending_types)]
            nodes[f"ending_{i}"] = await self.generate_story_node(
                f"ending_{i}",
                tags=["ending", etype],
                is_ending=True,
                ending_type=etype,
                **ctx,
            )

        return nodes

    async def generate_chapter(
        self, title: str = "Chapter", text: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Create a generic text chapter/section."""
        if text is None:
            text = await self.generate_text(
                "chapter_content", {"title": title, **kwargs}
            )
        return {"title": title, "text": text, "metadata": kwargs.get("metadata", {})}


# Backward-compatible aliases
class GeminiQuizWriterAgent(GeminiWriterAgent):
    """Gemini quiz writer agent."""

    def __init__(self, agent_id: str = "gemini_quiz_writer"):
        super().__init__(agent_id=agent_id, content_type="quiz")


class GeminiStoryWriterAgent(GeminiWriterAgent):
    """Gemini story writer agent."""

    def __init__(self, agent_id: str = "gemini_story_writer"):
        super().__init__(agent_id=agent_id, content_type="story")


__all__ = [
    "GeminiWriterAgent",
    "GeminiQuizWriterAgent",
    "GeminiStoryWriterAgent",
    "ADKAgentWrapper",
    "GeminiTextProvider",
]
