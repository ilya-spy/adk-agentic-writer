"""Static quiz writer agent - template-based quiz generation.

Implements: AgentProtocol + EditorialProtocol
"""

import logging
import random
from typing import Any, Dict

from ...models.agent_models import AgentRole, AgentStatus
from ...models.content_models import Quiz, QuizQuestion
from ..base_agent import BaseAgent

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
    "It enables", "It provides", "It allows", "It supports", "It facilitates",
    "The key is", "The focus is", "The goal is", "The purpose is", "The benefit is",
    "By using", "Through", "Via", "With", "Using",
    "This involves", "This requires", "This includes", "This means", "This ensures",
]

OPTION_SUFFIXES = [
    "efficient processing", "better performance", "improved reliability",
    "enhanced functionality", "greater flexibility", "optimal results",
    "seamless integration", "robust solutions", "scalable architecture",
    "maintainable code", "clear structure", "effective patterns",
]


class StaticQuizWriterAgent(BaseAgent):
    """Static agent for creating quizzes using templates.
    
    Implements:
    - AgentProtocol: process_task, update_status, get_state
    - EditorialProtocol: generate_content, validate_content, refine_content
    """

    def __init__(self, agent_id: str = "static_quiz_writer", config: Dict[str, Any] | None = None):
        """Initialize the static quiz writer agent."""
        super().__init__(agent_id, AgentRole.QUIZ_WRITER, config)

    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process a quiz generation task.
        
        Implements AgentProtocol.
        """
        await self.update_status(AgentStatus.WORKING)
        
        # Generate quiz using EditorialProtocol
        quiz_data = await self.generate_content(task_description, parameters)
        
        # Validate
        is_valid = await self.validate_content(quiz_data)
        
        # Refine if needed
        if not is_valid:
            quiz_data = await self.refine_content(quiz_data, "Improve question quality and clarity")
        
        await self.update_status(AgentStatus.COMPLETED)
        return quiz_data

    async def generate_content(self, prompt: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate quiz content using templates.
        
        Implements EditorialProtocol.
        """
        topic = parameters.get("topic", "general knowledge")
        num_questions = parameters.get("num_questions", 5)
        difficulty = parameters.get("difficulty", "medium")
        
        logger.info(f"Generating static quiz: {topic}, {num_questions} questions, {difficulty}")
        
        # Template-based generation with variety
        questions = []
        used_templates = set()
        
        for i in range(num_questions):
            # Select unique question template
            available_templates = [t for t in QUESTION_TEMPLATES if t not in used_templates]
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
                )
            )
        
        quiz = Quiz(
            title=f"{topic.title()} Quiz",
            description=f"Test your knowledge about {topic}",
            questions=questions,
            passing_score=parameters.get("passing_score", 70),
            time_limit=parameters.get("time_limit"),
        )
        
        return quiz.model_dump()

    async def validate_content(self, content: Dict[str, Any]) -> bool:
        """Validate quiz content.
        
        Implements EditorialProtocol.
        """
        if not content or not isinstance(content, dict):
            return False
        
        # Check required fields
        if "questions" not in content or not content["questions"]:
            return False
        
        # Validate each question
        for q in content["questions"]:
            if not all(key in q for key in ["question", "options", "correct_answer"]):
                return False
            if len(q["options"]) < 2:
                return False
        
        return True

    async def refine_content(self, content: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """Refine quiz content based on feedback.
        
        Implements EditorialProtocol.
        """
        logger.info(f"Refining quiz with feedback: {feedback}")
        
        # Simple refinement: add more detailed explanations
        if "questions" in content:
            for q in content["questions"]:
                if "explanation" not in q or not q["explanation"]:
                    q["explanation"] = f"Detailed explanation for: {q['question']}"
        
        return content


__all__ = ["StaticQuizWriterAgent"]
