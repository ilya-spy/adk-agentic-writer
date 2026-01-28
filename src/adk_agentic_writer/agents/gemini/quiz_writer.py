"""Gemini-powered quiz writer agent.

Generates quizzes using LLM-powered text generation.
Inherits from ContentWriterAgent for unified structure.
ADK integration to be added to GeminiTextProvider.
"""

import logging
import random
from typing import Any, Dict, List

from ...models.content_models import Quiz, QuizQuestion
from ...teams.content_team import QUIZ_WRITER
from ..content_writer import ContentWriterAgent
from ..text_provider import GeminiTextProvider

logger = logging.getLogger(__name__)


class GeminiQuizWriterAgent(ContentWriterAgent):
    """Gemini quiz writer using LLM-powered generation.

    Same structure as StaticQuizWriterAgent but uses
    GeminiTextProvider for natural language generation.
    """

    def __init__(self, agent_id: str = "gemini_quiz_writer"):
        """Initialize Gemini quiz writer.

        Args:
            agent_id: Unique agent identifier
        """
        super().__init__(
            agent_id=agent_id,
            config=QUIZ_WRITER,
            text_provider=GeminiTextProvider(),
        )
        logger.info(f"Initialized GeminiQuizWriterAgent {agent_id}")

    async def _build_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build quiz content using LLM.

        Args:
            context: Parameters including topic, num_questions, difficulty

        Returns:
            Quiz dictionary
        """
        topic = context.get("topic", "general knowledge")
        num_questions = context.get("num_questions", 5)
        difficulty = context.get("difficulty", "medium")

        logger.info(
            f"Generating quiz with Gemini: {topic}, {num_questions} questions, {difficulty}"
        )

        questions = await self._generate_questions(topic, num_questions, difficulty)

        quiz = Quiz(
            title=f"{topic.title()} Quiz",
            description=f"Test your knowledge about {topic}",
            questions=questions,
            passing_score=context.get("passing_score", 70),
            time_limit=context.get("time_limit"),
        )

        return quiz.model_dump()

    async def _generate_questions(
        self, topic: str, num_questions: int, difficulty: str
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions using LLM.

        Args:
            topic: Quiz topic
            num_questions: Number of questions to generate
            difficulty: Question difficulty level

        Returns:
            List of question dictionaries
        """
        questions = []
        ctx = {"topic": topic, "difficulty": difficulty}

        for i in range(num_questions):
            # Generate question text via LLM
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

            # Generate explanation
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


__all__ = ["GeminiQuizWriterAgent"]
