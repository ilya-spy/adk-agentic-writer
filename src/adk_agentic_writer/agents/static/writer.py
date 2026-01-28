"""Unified writer agent for text-based content.

Handles multiple content types (Quiz, Story) using a registry pattern.
New text-based content types can be added via the content registry
without creating new agent classes.
"""

import logging
import random
from typing import Any, Dict, List, Optional

from ...models.content_models import (
    Quiz,
    QuizQuestion,
    BranchedNarrative,
    StoryNode,
)
from ..content_agent import ContentWriterAgent
from ...utils.content_registry import CONTENT_REGISTRY, ContentTypeConfig
from ...utils.text_provider import TextProvider, TemplateTextProvider

logger = logging.getLogger(__name__)


class WriterAgent(ContentWriterAgent):
    """Unified writer agent for text-based content generation.

    Supports multiple content types via the content registry:
    - quiz: Multiple choice questions with explanations
    - branched_narrative/story: Interactive stories with branches

    New content types can be registered without modifying this class.
    """

    def __init__(
        self,
        agent_id: str = "writer",
        content_type: str = "quiz",
        text_provider: Optional[TextProvider] = None,
    ):
        """Initialize unified writer agent.

        Args:
            agent_id: Unique agent identifier
            content_type: Type of content to generate (quiz, story, etc.)
            text_provider: Optional custom text provider
        """
        self._content_type = content_type
        config = CONTENT_REGISTRY.get(content_type)

        if not config:
            raise ValueError(f"Unknown content type: {content_type}")
        if config.category != "writer":
            raise ValueError(f"Content type '{content_type}' is not a writer type")

        self._type_config = config

        super().__init__(
            agent_id=agent_id,
            config=config.agent_config,
            text_provider=text_provider or TemplateTextProvider(),
        )
        logger.info(f"Initialized WriterAgent {agent_id} for {content_type}")

    @property
    def content_type(self) -> str:
        """Get the content type this writer handles."""
        return self._content_type

    async def _build_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build content based on registered type.

        Args:
            context: Parameters for content generation

        Returns:
            Content dictionary
        """
        # Merge default params with provided context
        params = {**self._type_config.default_params, **context}
        topic = params.get("topic", "general")

        logger.info(f"Building {self._content_type} content for: {topic}")

        # Route to appropriate builder
        if self._content_type == "quiz":
            return await self._build_quiz(params)
        elif self._content_type in ("branched_narrative", "story"):
            return await self._build_story(params)
        else:
            # Generic fallback - try to construct from model
            return await self._build_generic(params)

    # =========================================================================
    # Quiz Builder
    # =========================================================================

    async def _build_quiz(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build quiz content.

        Args:
            params: Parameters including topic, num_questions, difficulty

        Returns:
            Quiz dictionary
        """
        topic = params.get("topic", "general knowledge")
        num_questions = params.get("num_questions", 5)
        difficulty = params.get("difficulty", "medium")

        logger.info(
            f"Generating quiz: {topic}, {num_questions} questions, {difficulty}"
        )

        questions = await self._generate_questions(topic, num_questions, difficulty)

        quiz = Quiz(
            title=self._type_config.title_template.format(topic=topic.title()),
            description=self._type_config.description_template.format(topic=topic),
            questions=questions,
            passing_score=params.get("passing_score", 70),
            time_limit=params.get("time_limit"),
        )

        return quiz.model_dump()

    async def _generate_questions(
        self, topic: str, num_questions: int, difficulty: str
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions."""
        questions = []
        ctx = {"topic": topic, "difficulty": difficulty}

        for _ in range(num_questions):
            question_text = await self._generate_text("quiz_question", ctx)

            # Generate options (one correct, three incorrect)
            correct_idx = random.randint(0, 3)
            options = []

            for j in range(4):
                if j == correct_idx:
                    option = await self._generate_text("quiz_option_correct", ctx)
                else:
                    option = await self._generate_text("quiz_option", ctx)
                options.append(option)

            explanation = await self._generate_text("quiz_explanation", ctx)

            questions.append(
                QuizQuestion(
                    question=question_text,
                    options=options,
                    correct_answer=correct_idx,
                    explanation=explanation,
                    difficulty=difficulty,
                ).model_dump()
            )

        return questions

    # =========================================================================
    # Story Builder
    # =========================================================================

    async def _build_story(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build branched narrative content.

        Args:
            params: Parameters including topic, genre, num_nodes

        Returns:
            BranchedNarrative dictionary
        """
        topic = params.get("topic", "adventure")
        genre = params.get("genre", "fantasy")
        num_nodes = params.get("num_nodes", 7)

        logger.info(f"Generating story: {topic}, genre: {genre}, nodes: {num_nodes}")

        nodes = await self._generate_story_nodes(topic, genre, num_nodes)

        narrative = BranchedNarrative(
            title=self._type_config.title_template.format(topic=topic.title()),
            synopsis=self._type_config.description_template.format(topic=topic),
            genre=genre,
            start_node="start",
            nodes=nodes,
            characters=["Protagonist", "Guide", "Antagonist"],
        )

        return narrative.model_dump()

    async def _generate_story_nodes(
        self, topic: str, genre: str, num_nodes: int
    ) -> Dict[str, Dict[str, Any]]:
        """Generate story nodes with branches."""
        nodes = {}
        ctx = {"topic": topic, "genre": genre}

        # Opening node
        opening_text = await self._generate_text("story_opening", ctx)
        nodes["start"] = StoryNode(
            node_id="start",
            content=opening_text,
            branches=[
                {"text": "Take the bold path", "next_node_id": "bold_path"},
                {"text": "Proceed with caution", "next_node_id": "cautious_path"},
            ],
            tags=["opening", genre],
            is_ending=False,
        ).model_dump()

        # Path nodes
        if num_nodes >= 3:
            bold_text = await self._generate_text(
                "story_path", {**ctx, "path_type": "bold"}
            )
            nodes["bold_path"] = StoryNode(
                node_id="bold_path",
                content=bold_text,
                branches=[
                    {"text": "Face the challenge", "next_node_id": "challenge"},
                    {"text": "Find allies", "next_node_id": "allies"},
                ],
                tags=["bold"],
                is_ending=False,
            ).model_dump()

            cautious_text = await self._generate_text(
                "story_path", {**ctx, "path_type": "cautious"}
            )
            nodes["cautious_path"] = StoryNode(
                node_id="cautious_path",
                content=cautious_text,
                branches=[
                    {"text": "Continue alone", "next_node_id": "challenge"},
                    {"text": "Seek wisdom", "next_node_id": "wisdom_ending"},
                ],
                tags=["cautious"],
                is_ending=False,
            ).model_dump()

        # Intermediate nodes
        if num_nodes >= 5:
            challenge_text = await self._generate_text(
                "story_path", {**ctx, "path_type": "challenge"}
            )
            nodes["challenge"] = StoryNode(
                node_id="challenge",
                content=challenge_text,
                branches=[{"text": "Claim victory", "next_node_id": "victory_ending"}],
                tags=["challenge"],
                is_ending=False,
            ).model_dump()

            allies_text = await self._generate_text(
                "story_path", {**ctx, "path_type": "allies"}
            )
            nodes["allies"] = StoryNode(
                node_id="allies",
                content=allies_text,
                branches=[
                    {"text": "Continue together", "next_node_id": "alliance_ending"}
                ],
                tags=["allies"],
                is_ending=False,
            ).model_dump()

        # Endings
        for ending_type, node_id in [
            ("victory", "victory_ending"),
            ("alliance", "alliance_ending"),
            ("wisdom", "wisdom_ending"),
        ]:
            ending_text = await self._generate_text(
                "story_ending", {**ctx, "ending_type": ending_type}
            )
            nodes[node_id] = StoryNode(
                node_id=node_id,
                content=ending_text,
                branches=[],
                tags=["ending", ending_type],
                is_ending=True,
            ).model_dump()

        return nodes

    # =========================================================================
    # Generic Builder (for future extensibility)
    # =========================================================================

    async def _build_generic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generic builder for new content types.

        Falls back to basic model construction with title/description.
        """
        topic = params.get("topic", "general")
        model_class = self._type_config.model_class

        # Try to construct with basic fields
        return model_class(
            title=self._type_config.title_template.format(topic=topic.title()),
            description=self._type_config.description_template.format(topic=topic),
            **{k: v for k, v in params.items() if k not in ("topic",)},
        ).model_dump()


# Convenience factory functions for backward compatibility
def create_quiz_writer(agent_id: str = "quiz_writer") -> WriterAgent:
    """Create a writer agent configured for quizzes."""
    return WriterAgent(agent_id=agent_id, content_type="quiz")


def create_story_writer(agent_id: str = "story_writer") -> WriterAgent:
    """Create a writer agent configured for stories."""
    return WriterAgent(agent_id=agent_id, content_type="story")


# Backward-compatible class aliases
class StaticQuizWriterAgent(WriterAgent):
    """Backward-compatible alias for quiz writer."""

    def __init__(self, agent_id: str = "quiz_writer"):
        super().__init__(agent_id=agent_id, content_type="quiz")


class StoryWriterAgent(WriterAgent):
    """Backward-compatible alias for story writer."""

    def __init__(self, agent_id: str = "story_writer"):
        super().__init__(agent_id=agent_id, content_type="story")


__all__ = [
    "WriterAgent",
    "StaticQuizWriterAgent",
    "StoryWriterAgent",
    "create_quiz_writer",
    "create_story_writer",
]
