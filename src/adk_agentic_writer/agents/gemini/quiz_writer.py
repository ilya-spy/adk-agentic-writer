"""Gemini-powered quiz writer agent using Google ADK."""

import json
import logging
from typing import Any, Dict

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

from ...models.agent_models import AGENT_TEAM_CONFIGS, AgentRole, AgentStatus
from ...models.content_models import Quiz, QuizQuestion
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)


class GeminiQuizWriterAgent(BaseAgent):
    """Agent specialized in creating interactive quizzes using Google ADK."""

    def __init__(
        self,
        agent_id: str = "gemini_quiz_writer_1",
        config: Dict[str, Any] | None = None,
    ):
        """Initialize the Gemini quiz writer agent with Google ADK."""
        super().__init__(agent_id, AgentRole.QUIZ_WRITER, config)
        
        # Get system instruction from AGENT_TEAM_CONFIGS
        agent_config = AGENT_TEAM_CONFIGS.get(AgentRole.QUIZ_WRITER)
        
        # Create Google ADK Agent instance
        self.adk_agent = Agent(
            name="QuizWriterAgent",
            model=Gemini(model="gemini-2.0-flash-exp"),
            instruction=agent_config.system_instruction if agent_config else self._get_default_instruction(),
            output_key="quiz_content",
        )
        self.runner = InMemoryRunner(agent=self.adk_agent)
    
    def _get_default_instruction(self) -> str:
        """Default instruction if not in config."""
        return """You are an expert quiz creator. Generate engaging, educational quizzes 
with clear questions, multiple choice options, and detailed explanations."""

    # System instruction now loaded from AGENT_TEAM_CONFIGS in base class

    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a quiz using Google ADK Agent.

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

        logger.info(f"Generating quiz about {topic} with {num_questions} questions using Google ADK")

        # Generate quiz using Google ADK Agent
        quiz_data = await self._generate_quiz_with_adk(topic, num_questions, difficulty)

        await self.update_status(AgentStatus.COMPLETED)

        return quiz_data

    async def _generate_quiz_with_adk(
        self, topic: str, num_questions: int, difficulty: str
    ) -> Dict[str, Any]:
        """Generate quiz questions using Google ADK Agent."""
        
        prompt = f"""Create an interactive quiz about "{topic}" with the following specifications:

Topic: {topic}
Number of Questions: {num_questions}
Difficulty Level: {difficulty}

For each question, provide:
1. A clear, well-written question
2. Exactly 4 answer options
3. The index (0-3) of the correct answer
4. A detailed explanation of why the answer is correct
5. The difficulty level

Return the quiz in the following JSON format:
{{
    "title": "Quiz title",
    "description": "Brief description of what the quiz covers",
    "questions": [
        {{
            "question": "Question text",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "correct_answer": 0,
            "explanation": "Detailed explanation",
            "difficulty": "{difficulty}"
        }}
    ],
    "passing_score": 70,
    "time_limit": null
}}

Make the questions engaging, educational, and appropriate for the {difficulty} difficulty level."""

        try:
            # ADK integration is complex - use fallback for now
            logger.warning("Using fallback generation (ADK integration needs proper implementation)")
            return await self._generate_fallback_quiz(topic, num_questions, difficulty)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ADK response as JSON: {e}")
            # Fallback to template-based generation
            return await self._generate_fallback_quiz(topic, num_questions, difficulty)
        except Exception as e:
            logger.error(f"Error generating quiz with Google ADK: {e}")
            raise

    async def _generate_fallback_quiz(
        self, topic: str, num_questions: int, difficulty: str
    ) -> Dict[str, Any]:
        """Fallback quiz generation if Gemini fails."""
        logger.warning("Using fallback quiz generation")
        
        questions = []
        for i in range(num_questions):
            questions.append(
                QuizQuestion(
                    question=f"Question {i+1} about {topic}",
                    options=[
                        f"Option A for {topic}",
                        f"Option B for {topic}",
                        f"Option C for {topic}",
                        f"Option D for {topic}",
                    ],
                    correct_answer=0,
                    explanation=f"This is the correct answer about {topic}.",
                    difficulty=difficulty,
                )
            )

        quiz = Quiz(
            title=f"{topic.title()} Quiz",
            description=f"Test your knowledge about {topic}",
            questions=questions,
            passing_score=70,
            time_limit=None,
        )

        return quiz.model_dump()


