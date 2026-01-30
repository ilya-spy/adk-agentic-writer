"""Writer agent for text-based content with universal block generators."""

import logging
import random
from typing import Any, Dict, List, Optional

from ...models.content_models import (
    ContentBlock,
    ContentBlockType,
    ContentPattern,
    Quiz,
    QuizQuestion,
    BranchedNarrative,
    StoryNode,
)
from ...utils.content_registry import CONTENT_REGISTRY
from ...utils.text_provider import TextProvider, TemplateTextProvider
from ..content_agent import ContentWriterAgent

logger = logging.getLogger(__name__)


class WriterAgent(ContentWriterAgent):
    """Writer implementing ContentProtocol with universal block generators."""

    def __init__(
        self,
        agent_id: str = "writer",
        content_type: str = "quiz",
        text_provider: Optional[TextProvider] = None,
    ):
        self._content_type = content_type
        config = CONTENT_REGISTRY.get(content_type)
        if not config:
            raise ValueError(f"Unknown content type: {content_type}")
        if config.category != "writer":
            raise ValueError(f"Content type '{content_type}' is not a writer type")
        self._type_config = config
        super().__init__(
            agent_id,
            config.agent_config,
            text_provider=text_provider or TemplateTextProvider(),
        )

    @property
    def content_type(self) -> str:
        return self._content_type

    # ContentProtocol
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

    async def generate_patterned_blocks(
        self,
        block_type: ContentBlockType,
        pattern: ContentPattern,
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate blocks with navigation based on pattern."""
        count, blocks = context.get("count", 3), []
        for i in range(count):
            block = await self.generate_block(
                block_type,
                {**context, "block_id": f"{block_type.value}_{i}", "index": i},
            )
            block.pattern = pattern
            if pattern == ContentPattern.SEQUENTIAL and i < count - 1:
                block.navigation = {"next": f"{block_type.value}_{i + 1}"}
            elif pattern == ContentPattern.LOOPED:
                block.navigation = {"next": f"{block_type.value}_{(i + 1) % count}"}
                block.exit_condition = context.get(
                    "exit_condition", {"max_iterations": 3}
                )
            elif pattern == ContentPattern.BRANCHED:
                block.choices = [
                    {"text": f"Go to {j}", "target": f"{block_type.value}_{j}"}
                    for j in range(count)
                    if j != i
                ]
            blocks.append(block)
        return blocks

    # Universal Block Generators
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
        ctx = {"topic": topic, "difficulty": difficulty}

        # Generate or use provided values
        q_text = question or await self._generate_text("quiz_question", ctx)
        correct_idx = (
            correct_answer if correct_answer is not None else random.randint(0, 3)
        )

        if options:
            opts = options
        else:
            opts = []
            for i in range(4):
                key = "quiz_option_correct" if i == correct_idx else "quiz_option"
                opts.append(await self._generate_text(key, ctx))

        expl = explanation or await self._generate_text("quiz_explanation", ctx)
        return QuizQuestion(
            question=q_text,
            options=opts,
            correct_answer=correct_idx,
            explanation=expl,
            difficulty=difficulty,
        )

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
            content = await self._generate_text(key, ctx)

        return StoryNode(
            node_id=node_id,
            content=content,
            branches=branches or [],
            tags=tags or [],
            is_ending=is_ending,
        )

    async def generate_chapter(
        self, title: str = "Chapter", text: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Create a generic text chapter/section."""
        if text is None:
            text = await self._generate_text(
                "chapter_content", {"title": title, **kwargs}
            )
        return {"title": title, "text": text, "metadata": kwargs.get("metadata", {})}

    # Batch generators
    async def generate_questions_set(
        self, topic: str, count: int = 5, difficulty: str = "medium"
    ) -> List[QuizQuestion]:
        """Generate a set of quiz questions."""
        return [await self.generate_question(topic, difficulty) for _ in range(count)]

    async def generate_story_nodes_set(
        self, topic: str, genre: str = "fantasy", num_nodes: int = 7
    ) -> Dict[str, StoryNode]:
        """Generate connected story nodes with branches."""
        nodes = {}
        ctx = {"topic": topic, "genre": genre}

        # Start node
        nodes["start"] = await self.generate_story_node(
            "start",
            tags=["opening", genre],
            branches=[
                {"text": "Take bold path", "next_node_id": "bold_path"},
                {"text": "Proceed cautiously", "next_node_id": "cautious_path"},
            ],
            **ctx,
        )

        # Path nodes
        if num_nodes >= 3:
            nodes["bold_path"] = await self.generate_story_node(
                "bold_path",
                tags=["bold"],
                path_type="bold",
                branches=[
                    {"text": "Face challenge", "next_node_id": "challenge"},
                    {"text": "Find allies", "next_node_id": "allies"},
                ],
                **ctx,
            )
            nodes["cautious_path"] = await self.generate_story_node(
                "cautious_path",
                tags=["cautious"],
                path_type="cautious",
                branches=[
                    {"text": "Continue alone", "next_node_id": "challenge"},
                    {"text": "Seek wisdom", "next_node_id": "wisdom_ending"},
                ],
                **ctx,
            )

        # Intermediate nodes
        if num_nodes >= 5:
            nodes["challenge"] = await self.generate_story_node(
                "challenge",
                tags=["challenge"],
                path_type="challenge",
                branches=[{"text": "Claim victory", "next_node_id": "victory_ending"}],
                **ctx,
            )
            nodes["allies"] = await self.generate_story_node(
                "allies",
                tags=["allies"],
                path_type="allies",
                branches=[
                    {"text": "Continue together", "next_node_id": "alliance_ending"}
                ],
                **ctx,
            )

        # Endings
        for etype, nid in [
            ("victory", "victory_ending"),
            ("alliance", "alliance_ending"),
            ("wisdom", "wisdom_ending"),
        ]:
            nodes[nid] = await self.generate_story_node(
                nid, tags=["ending", etype], is_ending=True, ending_type=etype, **ctx
            )

        return nodes

    # Content builders
    async def _build_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        params = {**self._type_config.default_params, **context}
        if self._content_type == "quiz":
            return await self._build_quiz(params)
        elif self._content_type in ("branched_narrative", "story"):
            return await self._build_story(params)
        return await self._build_generic(params)

    async def _build_quiz(self, p: Dict[str, Any]) -> Dict[str, Any]:
        topic, num_q, difficulty = (
            p.get("topic", "general"),
            p.get("num_questions", 5),
            p.get("difficulty", "medium"),
        )
        questions = await self.generate_questions_set(topic, num_q, difficulty)
        return Quiz(
            title=self._type_config.title_template.format(topic=topic.title()),
            description=self._type_config.description_template.format(topic=topic),
            questions=[q.model_dump() for q in questions],
            passing_score=p.get("passing_score", 70),
            time_limit=p.get("time_limit"),
        ).model_dump()

    async def _build_story(self, p: Dict[str, Any]) -> Dict[str, Any]:
        topic, genre, num_nodes = (
            p.get("topic", "adventure"),
            p.get("genre", "fantasy"),
            p.get("num_nodes", 7),
        )
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
        topic = p.get("topic", "general")
        return self._type_config.model_class(
            title=self._type_config.title_template.format(topic=topic.title()),
            description=self._type_config.description_template.format(topic=topic),
            **{k: v for k, v in p.items() if k != "topic"},
        ).model_dump()


# Aliases
class StaticQuizWriterAgent(WriterAgent):
    def __init__(self, agent_id: str = "quiz_writer"):
        super().__init__(agent_id, "quiz")


class StoryWriterAgent(WriterAgent):
    def __init__(self, agent_id: str = "story_writer"):
        super().__init__(agent_id, "story")


def create_quiz_writer(agent_id: str = "quiz_writer") -> WriterAgent:
    return WriterAgent(agent_id, "quiz")


def create_story_writer(agent_id: str = "story_writer") -> WriterAgent:
    return WriterAgent(agent_id, "story")


__all__ = [
    "WriterAgent",
    "StaticQuizWriterAgent",
    "StoryWriterAgent",
    "create_quiz_writer",
    "create_story_writer",
]
