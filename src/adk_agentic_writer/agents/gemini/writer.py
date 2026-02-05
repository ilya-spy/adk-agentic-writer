"""Gemini-powered writer agent using Google ADK.

Implements real AI generation via ADK Agent with:
- InMemoryRunner for session management
- Structured JSON output via output_schema
- Support for quiz and story content types
"""

import asyncio
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
from ...utils.content_registry import CONTENT_REGISTRY
from ..content_agent import ContentWriterAgent
from .prompts import (
    QUIZ_SYSTEM_INSTRUCTION,
    STORY_SYSTEM_INSTRUCTION,
    build_generation_prompt,
    get_system_instruction,
    SAMPLE_QUIZ_OUTPUT,
    SAMPLE_STORY_OUTPUT,
)

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
    - Agent initialization with system instruction
    - Session management via InMemoryRunner
    - Async execution with structured output
    """

    def __init__(
        self,
        name: str,
        model_name: str = "gemini-2.5-flash-lite",
        instruction: str = "",
        output_schema: Optional[Type[BaseModel]] = None,
    ):
        self.name = name
        self.model_name = model_name
        self.instruction = instruction
        self.output_schema = output_schema
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
            # Configure retry options (exp_base is the exponential backoff multiplier)
            retry_config = types.HttpRetryOptions(
                attempts=3,
                exp_base=2,
                initial_delay=1,
                http_status_codes=[429, 500, 503, 504],
            )

            # Create ADK Agent
            self._agent = Agent(
                name=self.name,
                model=self.model_name,
                instruction=self.instruction,
                # output_schema requires specific model support
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
            # Run with debug to get full response
            response = await self._runner.run_debug(prompt)

            # Extract text response
            if hasattr(response, "text"):
                return self._parse_json_response(response.text)
            elif isinstance(response, str):
                return self._parse_json_response(response)
            else:
                # Try to get content from response object
                content = str(response)
                return self._parse_json_response(content)

        except Exception as e:
            logger.error(f"ADK agent run failed: {e}")
            raise

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from agent response, handling markdown code blocks."""
        # Clean up response - remove markdown code blocks if present
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
            # Return error structure
            return {"error": "Failed to parse JSON", "raw": text[:1000]}


class GeminiTextProvider:
    """LLM-powered text provider using ADK agents.

    Provides text generation for individual content blocks.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash-lite"):
        self.model_name = model_name
        self._agents: Dict[str, ADKAgentWrapper] = {}

    async def _get_agent(self, prompt_key: str) -> ADKAgentWrapper:
        """Get or create agent for prompt type."""
        if prompt_key not in self._agents:
            # Determine instruction based on prompt key
            if "quiz" in prompt_key:
                instruction = QUIZ_SYSTEM_INSTRUCTION
            elif "story" in prompt_key:
                instruction = STORY_SYSTEM_INSTRUCTION
            else:
                instruction = "You are a helpful content creator."

            self._agents[prompt_key] = ADKAgentWrapper(
                name=f"text_gen_{prompt_key}",
                model_name=self.model_name,
                instruction=instruction,
            )
        return self._agents[prompt_key]

    async def generate_text(self, prompt_key: str, context: Dict[str, Any]) -> str:
        """Generate text using ADK agent."""
        if not ADK_AVAILABLE or not _check_api_key():
            # Fallback to template
            from ...utils.text_provider import TemplateTextProvider

            fallback = TemplateTextProvider()
            return await fallback.generate_text(prompt_key, context)

        agent = await self._get_agent(prompt_key)
        topic = context.get("topic", "the subject")

        prompts = {
            "quiz_question": f"Generate an engaging quiz question about {topic}. Return only the question text, no JSON.",
            "quiz_option": f"Generate a plausible but incorrect answer option for a quiz about {topic}. Return only the option text.",
            "quiz_option_correct": f"Generate the correct answer for a quiz question about {topic}. Return only the option text.",
            "quiz_explanation": f"Explain why this answer is correct in the context of {topic}. Be concise, 1-2 sentences.",
            "story_opening": f"Write an engaging opening paragraph (3-4 sentences) for an interactive story about {topic}.",
            "story_path": f"Write a short paragraph (2-3 sentences) describing the next scene in a story about {topic}.",
            "story_ending": f"Write a satisfying conclusion paragraph (2-3 sentences) for a story about {topic}.",
        }

        prompt = prompts.get(prompt_key, f"Generate content about {topic}")

        try:
            result = await agent.run(prompt)
            if isinstance(result, dict):
                return result.get("text", result.get("content", str(result)))
            return str(result)
        except Exception as e:
            logger.warning(f"ADK text generation failed: {e}, using fallback")
            from ...utils.text_provider import TemplateTextProvider

            fallback = TemplateTextProvider()
            return await fallback.generate_text(prompt_key, context)


class GeminiWriterAgent(ContentWriterAgent):
    """Gemini-powered writer agent for quiz and story generation.

    Uses ADK Agent with InMemoryRunner for real AI generation.
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

        config = CONTENT_REGISTRY.get(content_type)
        if not config:
            raise ValueError(f"Unknown content type: {content_type}")
        if config.category != "writer":
            raise ValueError(f"Content type '{content_type}' is not a writer type")
        self._type_config = config

        # Initialize with Gemini text provider
        text_provider = GeminiTextProvider(model_name=model_name)

        # Create AgentModel matching ADK structure
        model = AgentModel(
            name=agent_id,
            model_name=model_name,
            parameters={"content_type": content_type},
        )

        super().__init__(
            agent_id=agent_id,
            config=config.agent_config,
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

    async def _get_adk_agent(self, task_id: str) -> ADKAgentWrapper:
        """Get or create ADK agent for task."""
        if self._adk_agent is None:
            instruction = get_system_instruction(self._content_type)
            self._adk_agent = ADKAgentWrapper(
                name=f"{self.agent_id}_{task_id}",
                model_name=self._model_name,
                instruction=instruction,
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
        """Build content using ADK agent for full generation."""
        task_id = context.get("task_id", "")
        params = {**self._type_config.default_params, **context}

        # Get appropriate ADK agent
        agent = await self._get_adk_agent(task_id)

        # Build generation prompt with schema
        prompt = build_generation_prompt(task_id, params)

        # Add sample output for guidance
        if "quiz" in task_id:
            prompt += f"\n\nExample of expected output structure:\n{json.dumps(SAMPLE_QUIZ_OUTPUT, indent=2)}"
        elif "story" in task_id:
            prompt += f"\n\nExample of expected output structure:\n{json.dumps(SAMPLE_STORY_OUTPUT, indent=2)}"

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
