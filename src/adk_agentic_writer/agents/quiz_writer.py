"""Quiz writer agent for generating interactive quizzes."""

import logging
from typing import Any, Dict

from ..models.agent_models import AgentRole, AgentStatus
from ..models.content_models import Quiz, QuizQuestion
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class QuizWriterAgent(BaseAgent):
    """Agent specialized in creating interactive quizzes."""

    def __init__(self, agent_id: str = "quiz_writer_1", config: Dict[str, Any] | None = None):
        """Initialize the quiz writer agent."""
        super().__init__(agent_id, AgentRole.QUIZ_WRITER, config)

    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a quiz based on the given topic and parameters.

        Args:
            task_description: Description of the quiz to create
            parameters: Parameters including topic, difficulty, num_questions

        Returns:
            Dict containing the generated quiz
        """
        await self.update_status(AgentStatus.WORKING)
        
        topic = parameters.get("topic", "general knowledge")
        num_questions = parameters.get("num_questions", 5)
        difficulty = parameters.get("difficulty", "medium")
        
        logger.info(f"Generating quiz about {topic} with {num_questions} questions")
        
        # Generate quiz questions
        questions = await self._generate_questions(topic, num_questions, difficulty)
        
        # Create quiz object
        quiz = Quiz(
            title=f"{topic.title()} Quiz",
            description=f"Test your knowledge about {topic}",
            questions=questions,
            passing_score=parameters.get("passing_score", 70),
            time_limit=parameters.get("time_limit"),
        )
        
        await self.update_status(AgentStatus.COMPLETED)
        
        return quiz.model_dump()

    async def _generate_questions(
        self, topic: str, num_questions: int, difficulty: str
    ) -> list[QuizQuestion]:
        """Generate quiz questions for the given topic."""
        questions = []
        
        # Template-based question generation (in production, would use LLM)
        question_templates = self._get_question_templates(topic, difficulty)
        
        for i in range(min(num_questions, len(question_templates))):
            template = question_templates[i]
            questions.append(QuizQuestion(**template))
        
        return questions

    def _get_question_templates(self, topic: str, difficulty: str) -> list[Dict[str, Any]]:
        """Get question templates based on topic and difficulty."""
        # This is a simplified version - in production, this would use an LLM
        templates = [
            {
                "question": f"What is a key concept in {topic}?",
                "options": [
                    f"Primary principle of {topic}",
                    "Unrelated concept",
                    "Another unrelated concept",
                    "Yet another unrelated concept",
                ],
                "correct_answer": 0,
                "explanation": f"The primary principle is fundamental to understanding {topic}.",
                "difficulty": difficulty,
            },
            {
                "question": f"Which statement best describes {topic}?",
                "options": [
                    "Incorrect description",
                    f"Accurate description of {topic}",
                    "Misleading description",
                    "Vague description",
                ],
                "correct_answer": 1,
                "explanation": f"This accurately captures the essence of {topic}.",
                "difficulty": difficulty,
            },
            {
                "question": f"What is an important application of {topic}?",
                "options": [
                    "Unrelated application",
                    "Theoretical application",
                    f"Practical application in {topic}",
                    "Fictional application",
                ],
                "correct_answer": 2,
                "explanation": f"This is a common practical use of {topic}.",
                "difficulty": difficulty,
            },
            {
                "question": f"How does {topic} relate to real-world scenarios?",
                "options": [
                    "It doesn't relate",
                    "Only in theory",
                    "In limited cases",
                    f"It's widely applicable in {topic} contexts",
                ],
                "correct_answer": 3,
                "explanation": f"{topic} has broad real-world applications.",
                "difficulty": difficulty,
            },
            {
                "question": f"What is a common misconception about {topic}?",
                "options": [
                    f"That {topic} is simple when it's complex",
                    "That it's well understood",
                    "That it's not important",
                    "That it's only theoretical",
                ],
                "correct_answer": 0,
                "explanation": f"Many people underestimate the complexity of {topic}.",
                "difficulty": difficulty,
            },
        ]
        
        return templates
