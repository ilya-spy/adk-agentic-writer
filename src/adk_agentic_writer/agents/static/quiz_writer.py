"""Quiz writer agent implementing full ContentProtocol.

This agent generates quizzes using:
- Tasks: Predefined content generation tasks
- Teams: Quiz writer team configurations
- Workflows: Content generation workflows (sequential, looped, branched, etc.)
- Runtime: StatefulAgent with variable/parameter management

Implements: AgentProtocol + ContentProtocol
"""

import logging
import random
from typing import Any, Dict, List, Optional

from ...agents.stateful_agent import StatefulAgent
from ...models.agent_models import AgentRole, AgentStatus, AgentTask
from ...models.content_models import Quiz, QuizQuestion
from ...protocols.content_protocol import ContentBlock, ContentBlockType, ContentPattern
from ...tasks import content_tasks
from ...teams.content_team import QUIZ_WRITER, ContentRole

logger = logging.getLogger(__name__)

# Question templates pool for variety
QUESTION_TEMPLATES = [
    "What is the primary purpose of {topic}?",
    "Which of the following best describes {topic}?",
    "In {topic}, what is the most important concept?",
    "How does {topic} relate to modern applications?",
    "What makes {topic} unique compared to alternatives?",
    "Which statement about {topic} is correct?",
    "What is a key characteristic of {topic}?",
    "When working with {topic}, what should you prioritize?",
    "Which approach is recommended for {topic}?",
    "What is the fundamental principle behind {topic}?",
]

# Option templates for variety
OPTION_PREFIXES = [
    "It enables",
    "It provides",
    "It allows",
    "It supports",
    "It facilitates",
    "The key is",
    "The focus is",
    "The goal is",
    "The purpose is",
    "The benefit is",
    "By using",
    "Through",
    "Via",
    "With",
    "Using",
    "This involves",
    "This requires",
    "This includes",
    "This means",
    "This ensures",
]

OPTION_SUFFIXES = [
    "efficient processing",
    "better performance",
    "improved reliability",
    "enhanced functionality",
    "greater flexibility",
    "optimal results",
    "seamless integration",
    "robust solutions",
    "scalable architecture",
    "maintainable code",
    "clear structure",
    "effective patterns",
]


class StaticQuizWriterAgent(StatefulAgent):
    """Static quiz writer implementing full ContentProtocol.

    Implements:
    - AgentProtocol: process_task, update_status, get_state
    - ContentProtocol: generate_block, generate_sequential_blocks, etc.

    Uses:
    - Tasks from content_tasks
    - Configuration from QUIZ_WRITER team config
    - StatefulAgent for variable/parameter management
    """

    def __init__(self, agent_id: str = "static_quiz_writer"):
        """Initialize the static quiz writer agent."""
        super().__init__(
            agent_id=agent_id,
            config=QUIZ_WRITER,
        )
        logger.info(f"Initialized StaticQuizWriterAgent {agent_id}")

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute task based on task_id.

        Routes to appropriate method based on task type.
        """
        # Route to appropriate handler
        if task.task_id == "generate_block":
            return await self._handle_generate_block(task, resolved_prompt)
        elif task.task_id == "generate_sequential_blocks":
            return await self._handle_generate_sequential_blocks(task, resolved_prompt)
        elif task.task_id == "generate_looped_blocks":
            return await self._handle_generate_looped_blocks(task, resolved_prompt)
        elif task.task_id == "generate_branched_blocks":
            return await self._handle_generate_branched_blocks(task, resolved_prompt)
        elif task.task_id == "generate_conditional_blocks":
            return await self._handle_generate_conditional_blocks(task, resolved_prompt)
        else:
            # Default: treat as quiz generation
            return await self._generate_quiz_content(resolved_prompt)

    # ========================================================================
    # ContentProtocol Implementation
    # ========================================================================

    async def generate_block(
        self,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        previous_blocks: Optional[List[ContentBlock]] = None,
    ) -> ContentBlock:
        """Generate a single quiz content block.

        Implements ContentProtocol.
        """
        topic = context.get("topic", "general knowledge")
        num_questions = context.get("num_questions", 5)
        difficulty = context.get("difficulty", "medium")

        # Generate quiz
        quiz_data = await self._generate_quiz_data(topic, num_questions, difficulty)

        # Create content block
        block = ContentBlock(
            block_id=f"quiz_{topic.replace(' ', '_')}",
            block_type=block_type,
            content=quiz_data,
            pattern=ContentPattern.SEQUENTIAL,
            navigation={"next": None, "prev": None},
        )

        return block

    async def generate_sequential_blocks(
        self,
        num_blocks: int,
        block_type: ContentBlockType,
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate sequential quiz blocks (e.g., quiz sections).

        Implements ContentProtocol.
        """
        blocks = []
        topic = context.get("topic", "general knowledge")
        questions_per_block = context.get("questions_per_block", 3)

        for i in range(num_blocks):
            block_id = f"quiz_section_{i+1}"
            section_topic = f"{topic} - Section {i+1}"

            quiz_data = await self._generate_quiz_data(
                section_topic, questions_per_block, context.get("difficulty", "medium")
            )

            # Set up navigation
            navigation = {
                "next": f"quiz_section_{i+2}" if i < num_blocks - 1 else None,
                "prev": f"quiz_section_{i}" if i > 0 else None,
            }

            block = ContentBlock(
                block_id=block_id,
                block_type=block_type,
                content=quiz_data,
                pattern=ContentPattern.SEQUENTIAL,
                navigation=navigation,
            )
            blocks.append(block)

        return blocks

    async def generate_looped_blocks(
        self,
        num_blocks: int,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        exit_condition: Dict[str, Any],
        allow_back: bool = True,
    ) -> List[ContentBlock]:
        """Generate looped quiz blocks (e.g., practice mode with retry).

        Implements ContentProtocol.
        """
        blocks = []
        topic = context.get("topic", "general knowledge")

        for i in range(num_blocks):
            block_id = f"practice_quiz_{i+1}"

            quiz_data = await self._generate_quiz_data(
                topic,
                context.get("num_questions", 3),
                context.get("difficulty", "medium"),
            )

            # Set up loop navigation
            navigation = {
                "next": f"practice_quiz_{(i+1) % num_blocks + 1}",  # Loop back
                "prev": f"practice_quiz_{i}" if allow_back and i > 0 else None,
                "exit": "check_exit_condition",
            }

            block = ContentBlock(
                block_id=block_id,
                block_type=block_type,
                content=quiz_data,
                pattern=ContentPattern.LOOPED,
                navigation=navigation,
                exit_condition=exit_condition,
            )
            blocks.append(block)

        return blocks

    async def generate_branched_blocks(
        self,
        branch_points: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate branched quiz blocks (e.g., adaptive difficulty).

        Implements ContentProtocol.
        """
        blocks = []
        topic = context.get("topic", "general knowledge")

        # Create initial assessment quiz
        initial_quiz = await self._generate_quiz_data(topic, 3, "medium")

        choices = [
            {"text": "Easy Path", "next_block": "easy_quiz"},
            {"text": "Medium Path", "next_block": "medium_quiz"},
            {"text": "Hard Path", "next_block": "hard_quiz"},
        ]

        initial_block = ContentBlock(
            block_id="assessment_quiz",
            block_type=ContentBlockType.QUESTION,
            content=initial_quiz,
            pattern=ContentPattern.BRANCHED,
            choices=choices,
        )
        blocks.append(initial_block)

        # Create difficulty-specific branches
        for difficulty in ["easy", "medium", "hard"]:
            quiz_data = await self._generate_quiz_data(topic, 5, difficulty)

            branch_block = ContentBlock(
                block_id=f"{difficulty}_quiz",
                block_type=ContentBlockType.QUESTION,
                content=quiz_data,
                pattern=ContentPattern.BRANCHED,
                navigation={"next": "completion"},
            )
            blocks.append(branch_block)

        return blocks

    async def generate_conditional_blocks(
        self,
        blocks_config: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate conditional quiz blocks (e.g., bonus questions).

        Implements ContentProtocol.
        """
        blocks = []
        topic = context.get("topic", "general knowledge")

        for config in blocks_config:
            condition = config.get("condition", {})
            num_questions = config.get("num_questions", 3)

            quiz_data = await self._generate_quiz_data(
                topic, num_questions, config.get("difficulty", "medium")
            )

            block = ContentBlock(
                block_id=config.get("block_id", f"conditional_quiz_{len(blocks)}"),
                block_type=ContentBlockType.QUESTION,
                content=quiz_data,
                pattern=ContentPattern.CONDITIONAL,
                metadata={"display_condition": condition},
            )
            blocks.append(block)

        return blocks

    # ========================================================================
    # Task Handlers
    # ========================================================================

    async def _handle_generate_block(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Handle generate_block task."""
        context = self.prepare_task_context(task)
        block_type = ContentBlockType(context.get("block_type", "question"))

        block = await self.generate_block(block_type, context)
        return block.content

    async def _handle_generate_sequential_blocks(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Handle generate_sequential_blocks task."""
        context = self.prepare_task_context(task)
        num_blocks = context.get("num_blocks", 3)
        block_type = ContentBlockType(context.get("block_type", "question"))

        blocks = await self.generate_sequential_blocks(num_blocks, block_type, context)
        return {"blocks": [b.content for b in blocks]}

    async def _handle_generate_looped_blocks(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Handle generate_looped_blocks task."""
        context = self.prepare_task_context(task)
        num_blocks = context.get("num_blocks", 3)
        block_type = ContentBlockType(context.get("block_type", "question"))
        exit_condition = context.get("exit_condition", {"score": ">=80"})

        blocks = await self.generate_looped_blocks(
            num_blocks, block_type, context, exit_condition
        )
        return {"blocks": [b.content for b in blocks]}

    async def _handle_generate_branched_blocks(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Handle generate_branched_blocks task."""
        context = self.prepare_task_context(task)
        branch_points = context.get("branch_points", [])

        blocks = await self.generate_branched_blocks(branch_points, context)
        return {"blocks": [b.content for b in blocks]}

    async def _handle_generate_conditional_blocks(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Handle generate_conditional_blocks task."""
        context = self.prepare_task_context(task)
        blocks_config = context.get("blocks_config", [])

        blocks = await self.generate_conditional_blocks(blocks_config, context)
        return {"blocks": [b.content for b in blocks]}

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _generate_quiz_content(self, resolved_prompt: str) -> Dict[str, Any]:
        """Generate quiz content from resolved prompt."""
        # Extract parameters from variables
        topic = self.get_parameter("topic", "general knowledge")
        num_questions = self.get_parameter("num_questions", 5)
        difficulty = self.get_parameter("difficulty", "medium")

        quiz_data = await self._generate_quiz_data(topic, num_questions, difficulty)
        return quiz_data

    async def _generate_quiz_data(
        self, topic: str, num_questions: int, difficulty: str
    ) -> Dict[str, Any]:
        """Generate quiz data using templates."""
        logger.info(
            f"Generating quiz: {topic}, {num_questions} questions, {difficulty}"
        )

        # Template-based generation with variety
        questions = []
        used_templates = set()

        for i in range(num_questions):
            # Select unique question template
            available_templates = [
                t for t in QUESTION_TEMPLATES if t not in used_templates
            ]
            if not available_templates:
                available_templates = QUESTION_TEMPLATES
                used_templates.clear()

            question_template = random.choice(available_templates)
            used_templates.add(question_template)

            # Generate varied options
            correct_idx = random.randint(0, 3)
            options = []
            used_combinations = set()

            for j in range(4):
                # Create unique option combinations
                prefix = random.choice(OPTION_PREFIXES)
                suffix = random.choice(OPTION_SUFFIXES)
                combo = f"{prefix}, {suffix}"

                # Ensure uniqueness
                attempts = 0
                while combo in used_combinations and attempts < 10:
                    prefix = random.choice(OPTION_PREFIXES)
                    suffix = random.choice(OPTION_SUFFIXES)
                    combo = f"{prefix}, {suffix}"
                    attempts += 1

                used_combinations.add(combo)

                if j == correct_idx:
                    options.append(f"{prefix} {suffix} in {topic}")
                else:
                    options.append(f"{prefix} {suffix}")

            questions.append(
                QuizQuestion(
                    question=question_template.format(topic=topic),
                    options=options,
                    correct_answer=correct_idx,
                    explanation=f"This answer correctly identifies the core aspect of {topic} that {options[correct_idx].lower()}.",
                    difficulty=difficulty,
                ).model_dump()
            )

        quiz = Quiz(
            title=f"{topic.title()} Quiz",
            description=f"Test your knowledge about {topic}",
            questions=questions,
            passing_score=self.get_parameter("passing_score", 70),
            time_limit=self.get_parameter("time_limit"),
        )

        return quiz.model_dump()


__all__ = ["StaticQuizWriterAgent"]
