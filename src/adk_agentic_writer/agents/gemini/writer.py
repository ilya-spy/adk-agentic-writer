"""Gemini-powered writer agent using Google ADK.

LLM-only implementation supporting all writer content types.
Requires GOOGLE_API_KEY environment variable.
"""

import json
import logging
from typing import Any, Dict, List, Optional

# Clear proxy before ADK imports
from ...utils.proxy_utils import clear_proxy_env

clear_proxy_env()

from ...models.agent_models import AgentModel, AgentTask, AgentStatus
from ...models.content_models import (
    BranchedNarrative,
    ContentBlock,
    ContentBlockType,
    ContentPattern,
    Quiz,
    QuizQuestion,
    StoryNode,
)
from ...tasks.content_tasks import GENERATE_QUIZ, GENERATE_STORY
from ...teams.content_team import get_config_for_role, CONTENT_WRITER
from ...utils.content_registry import CONTENT_REGISTRY
from ..content_agent import ContentWriterAgent
from .wrapper import ADKAgentWrapper

logger = logging.getLogger(__name__)


class GeminiWriterAgent(ContentWriterAgent):
    """Gemini-powered writer supporting all content types.

    Delegates scoring, tiering, and timing to the LLM via clear prompts.
    Post-processing is limited to light validation and logging.
    """

    def __init__(
        self,
        agent_id: str = "gemini_writer",
        content_type: Optional[str] = None,
        model_name: str = "gemini-2.5-flash-lite",
    ):
        self._model_name = model_name
        self._content_type = content_type

        if content_type:
            type_config = CONTENT_REGISTRY.get(content_type)
            if not type_config:
                raise ValueError(f"Unknown content type: {content_type}")
            if type_config.category != "writer":
                raise ValueError(f"Content type '{content_type}' is not a writer type")
            role_config = get_config_for_role(content_type)
        else:
            role_config = CONTENT_WRITER

        super().__init__(
            agent_id=agent_id,
            config=role_config,
            model=AgentModel(name=agent_id, model_name=model_name),
            text_provider=None,
        )

        self.supported_tasks.extend([GENERATE_QUIZ, GENERATE_STORY])
        self._adk_agents: Dict[str, ADKAgentWrapper] = {}

        logger.info(
            f"Initialized GeminiWriterAgent: {agent_id}"
            + (f" ({content_type})" if content_type else " (dynamic)")
        )

    @property
    def content_type(self) -> Optional[str]:
        return self._content_type

    def _get_effective_content_type(self, task: Optional[AgentTask] = None) -> str:
        """Get content type from init or task parameters."""
        if self._content_type:
            return self._content_type
        if task:
            ct = task.parameters.get("content_type") if task.parameters else None
            if ct:
                return ct
            if "quiz" in task.task_id:
                return "quiz"
            if "story" in task.task_id:
                return "story"
        return "quiz"

    async def _get_agent_for_type(self, content_type: str) -> ADKAgentWrapper:
        """Get or create ADK agent for specific content type."""
        if content_type not in self._adk_agents:
            config = get_config_for_role(content_type)
            self._adk_agents[content_type] = ADKAgentWrapper(
                name=f"{self.agent_id}_{content_type}",
                instruction=config.instruction,
                model_name=self._model_name,
            )
        return self._adk_agents[content_type]

    # =========================================================================
    # Core generation
    # =========================================================================

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute task, routing quiz/story through dedicated methods."""
        context = self.prepare_task_context(task)
        content_type = self._get_effective_content_type(task)

        if content_type == "quiz":
            quiz = await self.generate_quiz(
                topic=context.get("topic", "general"),
                num_questions=int(context.get("num_questions", 5)),
                difficulty=context.get("difficulty", "medium"),
                num_options=int(context.get("num_options", 4)),
            )
            return quiz.model_dump()

        if content_type in ("branched_narrative", "story"):
            story = await self.generate_story(
                topic=context.get("topic", "general"),
                num_nodes=int(context.get("num_nodes", 5)),
            )
            return story.model_dump()

        context["content_type"] = content_type
        return await self._generate_content(content_type, context)

    async def _generate_content(
        self, content_type: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate content using LLM with type-specific config."""
        type_config = CONTENT_REGISTRY.get(content_type)
        if not type_config:
            raise ValueError(f"Unknown content type: {content_type}")

        role_config = get_config_for_role(content_type)
        full_context = {**type_config.default_params, **context}

        prompt = role_config.generation_prompt.format(**full_context)
        if type_config.schema_description:
            prompt += f"\n\n{type_config.schema_description}"
        if type_config.sample_output:
            prompt += f"\n\nExample output:\n{json.dumps(type_config.sample_output, indent=2)}"

        agent = await self._get_agent_for_type(content_type)
        await self.update_status(AgentStatus.WORKING)
        result = await agent.run(prompt)
        await self.update_status(AgentStatus.COMPLETED)

        ADKAgentWrapper.validate_content_fields(
            result, content_type, agent_name=agent.name
        )
        return result

    # =========================================================================
    # Quiz generation
    # =========================================================================

    async def generate_question(
        self, topic: str = "general", difficulty: str = "medium", **kwargs
    ) -> QuizQuestion:
        """Generate a single quiz question."""
        num_options = kwargs.get("num_options", 4)
        config = get_config_for_role("quiz")
        prompt = config.prompt_templates.get("quiz_question_complete", "").format(
            topic=topic, difficulty=difficulty, num_options=num_options
        )
        if not prompt:
            raise ValueError("Missing 'quiz_question_complete' prompt template")

        agent = await self._get_agent_for_type("quiz")
        result = await agent.run(
            prompt,
            required_fields={"question", "options", "correct_answer"},
            optional_fields={"explanation", "tier"},
        )

        return QuizQuestion(
            question=result["question"],
            options=result["options"],
            correct_answer=result["correct_answer"],
            explanation=result.get("explanation", ""),
            tier=result.get("tier", result.get("difficulty", "mid")),
        )

    async def generate_quiz(
        self, topic: str, num_questions: int = 5, difficulty: str = "medium", **params
    ) -> Quiz:
        """Generate a complete quiz. Trusts LLM for scoring; validates lightly."""
        num_options = params.pop("num_options", 4)
        num_questions = max(num_questions, 3)
        context = {
            "topic": topic,
            "num_questions": num_questions,
            "difficulty": difficulty,
            "num_options": num_options,
            **params,
        }
        result = await self._generate_content("quiz", context)
        type_config = CONTENT_REGISTRY.get("quiz")

        questions = result.get("questions", [])

        # Light fix: trim excess options if LLM ignored num_options
        for q in questions:
            if isinstance(q, dict) and len(q.get("options", [])) > num_options:
                correct_idx = q.get("correct_answer", 0)
                opts = q["options"][:num_options]
                if correct_idx >= num_options:
                    # Swap correct answer into last kept slot
                    opts[-1] = q["options"][correct_idx]
                    q["correct_answer"] = num_options - 1
                q["options"] = opts

        # ------------------------------------------------------------------
        # Enforce 3-tier scoring: if LLM didn't produce all tiers, fix it
        # ------------------------------------------------------------------
        _TIER_SCORE = {"low": 1, "mid": 2, "high": 3}
        _TIER_CYCLE = ["low", "mid", "high"]

        dict_qs = [q for q in questions if isinstance(q, dict)]

        # Normalise: LLM may return "difficulty" instead of "tier"
        for q in dict_qs:
            if "tier" not in q and "difficulty" in q:
                q["tier"] = q.pop("difficulty")

        tiers = {q.get("tier") for q in dict_qs}
        if not tiers >= {"low", "mid", "high"}:
            logger.warning(
                f"LLM returned tiers {tiers}, forcing low/mid/high distribution"
            )
            for i, q in enumerate(dict_qs):
                tier = _TIER_CYCLE[i % 3]
                q["tier"] = tier
                q["score"] = _TIER_SCORE[tier]

        # Ensure every question has a valid score matching its tier
        for q in dict_qs:
            tier = q.get("tier")
            if tier in _TIER_SCORE:
                q["score"] = _TIER_SCORE[tier]
            elif q.get("score") not in (1, 2, 3):
                q["score"] = 1  # safe fallback

        # Compute / validate passing_score
        total_pts = sum(q.get("score", 1) for q in dict_qs)
        passing = result.get("passing_score")
        if not isinstance(passing, (int, float)) or total_pts == 0:
            passing = max(1, round(total_pts * 0.65))
            result["passing_score"] = passing
        else:
            pct = passing / total_pts
            if not (0.50 <= pct <= 0.85):
                logger.warning(
                    f"LLM passing_score={passing}/{total_pts} ({pct:.0%}) "
                    "outside acceptable range, recalculating"
                )
                passing = max(1, round(total_pts * 0.65))
                result["passing_score"] = passing

        return Quiz(
            title=result.get(
                "title", type_config.title_template.format(topic=topic.title())
            ),
            description=result.get(
                "description", type_config.description_template.format(topic=topic)
            ),
            difficulty=difficulty,
            questions=questions,
            passing_score=passing,
            time_limit=result.get("time_limit"),
        )

    # =========================================================================
    # Story generation
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
        """Generate a single story node."""
        config = get_config_for_role("story")
        agent = await self._get_agent_for_type("story")

        if is_ending:
            prompt = config.prompt_templates.get("story_ending", "").format(
                topic=topic, genre=genre,
                ending_type=kwargs.get("ending_type", "neutral"),
            )
            result = await agent.run(prompt)
            content = result.get("content", str(result))
            if isinstance(content, dict):
                content = content.get("text", str(content))
            return StoryNode(
                node_id=node_id, content=str(content)[:500],
                branches=[], tags=kwargs.get("tags", ["ending"]), is_ending=True,
            )

        prompt = config.prompt_templates.get("story_node_complete", "").format(
            topic=topic, genre=genre, node_id=node_id,
            node_type="opening" if node_id == "start" else "middle",
            available_nodes=", ".join(available_nodes or []),
        )
        if not prompt:
            raise ValueError("Missing 'story_node_complete' prompt template")

        result = await agent.run(
            prompt,
            required_fields={"content", "branches"},
            optional_fields={"node_id", "tags", "is_ending"},
        )

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
        """Generate a complete branched story."""
        num_endings = min(3, max(1, num_nodes // 3))
        config = get_config_for_role("story")
        prompt = config.prompt_templates.get("story_structure", "").format(
            topic=topic, genre=genre, num_nodes=num_nodes, num_endings=num_endings
        )
        if not prompt:
            raise ValueError("Missing 'story_structure' prompt template")

        agent = await self._get_agent_for_type("story")
        await self.update_status(AgentStatus.WORKING)
        result = await agent.run(
            prompt,
            required_fields={"nodes"},
            optional_fields={"title", "synopsis", "characters"},
        )

        ADKAgentWrapper.validate_content_fields(
            result, "story", agent_name=agent.name
        )

        nodes = {}
        for nid, node_data in result.get("nodes", {}).items():
            if not isinstance(node_data, dict):
                logger.warning(f"Node '{nid}' is not a dict, skipping")
                continue
            # Normalize branch dicts: LLM uses varying key names
            raw_branches = node_data.get("branches", [])
            branches = []
            _text_keys = ("text", "label", "choice", "description", "option")
            _target_keys = ("node", "target", "next", "destination", "goto")
            for b in raw_branches:
                if not isinstance(b, dict):
                    continue
                # Fuzzy key matching: find text-like and target-like values
                text = ""
                target = ""
                for k, v in b.items():
                    kl = k.lower()
                    if not text and any(tk in kl for tk in _text_keys):
                        text = str(v)
                    elif not target and any(tk in kl for tk in _target_keys):
                        target = str(v)
                if text and target:
                    branches.append({"text": text, "next_node_id": target})
                elif b:
                    logger.warning(f"Node '{nid}' branch dropped (unrecognized keys): {list(b.keys())}")
            nodes[nid] = StoryNode(
                node_id=node_data.get("node_id", nid),
                content=node_data.get("content", ""),
                branches=branches,
                tags=node_data.get("tags", []),
                is_ending=node_data.get("is_ending", False),
            )

        if "start" not in nodes:
            raise ValueError("LLM response missing 'start' node")

        await self.update_status(AgentStatus.COMPLETED)
        type_config = CONTENT_REGISTRY.get("story")
        return BranchedNarrative(
            title=result.get(
                "title", type_config.title_template.format(topic=topic.title())
            ),
            synopsis=result.get(
                "synopsis", type_config.description_template.format(topic=topic)
            ),
            genre=genre,
            start_node="start",
            nodes={k: v.model_dump() for k, v in nodes.items()},
            characters=result.get("characters", ["Protagonist"]),
        )

    # =========================================================================
    # Block generation (generic)
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
            content_type = "quiz"
        elif block_type == ContentBlockType.NODE:
            content_type = "story"
        else:
            raise ValueError(f"Unsupported block type: {block_type}")

        result = await self._generate_content(content_type, context)
        return ContentBlock(
            block_id=block_id, block_type=block_type, content=result,
            pattern=context.get("pattern", ContentPattern.SEQUENTIAL),
            metadata=context.get("metadata", {}),
        )


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
]
