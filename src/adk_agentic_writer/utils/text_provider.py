"""Text generation providers for content agents.

TextProvider abstracts text generation:
- TemplateTextProvider: Static template-based text (fast, no API)
- GeminiTextProvider: LLM-powered text (to be implemented with ADK)
"""

import logging
import random
from typing import Any, Dict, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class TextProvider(Protocol):
    """Protocol for text generation providers."""

    async def generate_text(self, prompt_key: str, context: Dict[str, Any]) -> str:
        """Generate text based on prompt key and context.

        Args:
            prompt_key: Key identifying the type of text to generate
            context: Context variables for text generation

        Returns:
            Generated text string
        """
        ...


class TemplateTextProvider:
    """Template-based text provider for static agents.

    Uses predefined templates with variable substitution.
    Fast, deterministic, no API calls required.
    """

    # Quiz templates
    QUIZ_QUESTION_TEMPLATES = [
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

    QUIZ_OPTION_PREFIXES = [
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

    QUIZ_OPTION_SUFFIXES = [
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

    # Story templates
    STORY_OPENINGS = [
        "You find yourself at the beginning of an extraordinary journey into {topic}.",
        "As dawn breaks, you stand at the threshold of {topic}.",
        "A mysterious force draws you toward {topic}.",
        "The ancient texts spoke of {topic}, but nothing prepared you for this moment.",
    ]

    STORY_PATH_TEMPLATES = {
        "bold": "Your bold approach to {topic} leads you to unexpected discoveries.",
        "cautious": "Your careful consideration of {topic} reveals hidden details.",
        "challenge": "The challenge tests your understanding of {topic}.",
        "allies": "You find companions who share your interest in {topic}.",
    }

    STORY_ENDINGS = {
        "victory": "Through courage and determination, you've mastered {topic}.",
        "alliance": "Your alliance has transformed the understanding of {topic}.",
        "wisdom": "The wisdom you've gained about {topic} becomes a beacon for others.",
    }

    # Game templates
    GAME_QUEST_TEMPLATES = [
        "Discover the secrets of {topic}",
        "Master the fundamentals of {topic}",
        "Explore the depths of {topic}",
        "Unlock the mysteries of {topic}",
    ]

    GAME_OBJECTIVE_TEMPLATES = [
        "Learn about {aspect} in {topic}",
        "Complete the {aspect} challenge",
        "Gather knowledge about {aspect}",
        "Demonstrate understanding of {aspect}",
    ]

    # Simulation templates
    SIMULATION_DESCRIPTION_TEMPLATES = [
        "Interactive simulation exploring {topic}",
        "Hands-on experience with {topic} concepts",
        "Dynamic visualization of {topic} principles",
    ]

    async def generate_text(self, prompt_key: str, context: Dict[str, Any]) -> str:
        """Generate text using templates.

        Args:
            prompt_key: Type of text to generate (quiz_question, story_opening, etc.)
            context: Variables for template substitution

        Returns:
            Generated text
        """
        generators = {
            "quiz_question": self._generate_quiz_question,
            "quiz_option": self._generate_quiz_option,
            "quiz_option_correct": self._generate_quiz_option_correct,
            "quiz_explanation": self._generate_quiz_explanation,
            "story_opening": self._generate_story_opening,
            "story_path": self._generate_story_path,
            "story_ending": self._generate_story_ending,
            "game_quest": self._generate_game_quest,
            "game_objective": self._generate_game_objective,
            "simulation_description": self._generate_simulation_description,
        }

        generator = generators.get(prompt_key, self._generate_default)
        return generator(context)

    def _generate_quiz_question(self, context: Dict[str, Any]) -> str:
        topic = context.get("topic", "the subject")
        template = random.choice(self.QUIZ_QUESTION_TEMPLATES)
        return template.format(topic=topic)

    def _generate_quiz_option(self, context: Dict[str, Any]) -> str:
        prefix = random.choice(self.QUIZ_OPTION_PREFIXES)
        suffix = random.choice(self.QUIZ_OPTION_SUFFIXES)
        return f"{prefix} {suffix}"

    def _generate_quiz_option_correct(self, context: Dict[str, Any]) -> str:
        topic = context.get("topic", "the subject")
        prefix = random.choice(self.QUIZ_OPTION_PREFIXES)
        suffix = random.choice(self.QUIZ_OPTION_SUFFIXES)
        return f"{prefix} {suffix} in {topic}"

    def _generate_quiz_explanation(self, context: Dict[str, Any]) -> str:
        topic = context.get("topic", "the subject")
        return f"This answer correctly identifies the core aspect of {topic}."

    def _generate_story_opening(self, context: Dict[str, Any]) -> str:
        topic = context.get("topic", "adventure")
        template = random.choice(self.STORY_OPENINGS)
        return template.format(topic=topic)

    def _generate_story_path(self, context: Dict[str, Any]) -> str:
        topic = context.get("topic", "adventure")
        path_type = context.get("path_type", "bold")
        template = self.STORY_PATH_TEMPLATES.get(
            path_type, self.STORY_PATH_TEMPLATES["bold"]
        )
        return template.format(topic=topic)

    def _generate_story_ending(self, context: Dict[str, Any]) -> str:
        topic = context.get("topic", "adventure")
        ending_type = context.get("ending_type", "victory")
        template = self.STORY_ENDINGS.get(ending_type, self.STORY_ENDINGS["victory"])
        return template.format(topic=topic)

    def _generate_game_quest(self, context: Dict[str, Any]) -> str:
        topic = context.get("topic", "adventure")
        template = random.choice(self.GAME_QUEST_TEMPLATES)
        return template.format(topic=topic)

    def _generate_game_objective(self, context: Dict[str, Any]) -> str:
        topic = context.get("topic", "adventure")
        aspect = context.get("aspect", "core concepts")
        template = random.choice(self.GAME_OBJECTIVE_TEMPLATES)
        return template.format(topic=topic, aspect=aspect)

    def _generate_simulation_description(self, context: Dict[str, Any]) -> str:
        topic = context.get("topic", "the system")
        template = random.choice(self.SIMULATION_DESCRIPTION_TEMPLATES)
        return template.format(topic=topic)

    def _generate_default(self, context: Dict[str, Any]) -> str:
        topic = context.get("topic", "the subject")
        return f"Content about {topic}"


class GeminiTextProvider:
    """LLM-powered text provider using Google ADK.

    This is a boilerplate implementation. ADK integration will be added later.
    Currently falls back to template-based generation.
    """

    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """Initialize Gemini text provider.

        Args:
            model: Gemini model to use
        """
        self.model = model
        self._fallback = TemplateTextProvider()
        self._adk_agent = None  # To be initialized with ADK
        logger.info(f"Initialized GeminiTextProvider with model {model}")

    async def generate_text(self, prompt_key: str, context: Dict[str, Any]) -> str:
        """Generate text using Gemini LLM.

        Currently uses fallback templates. ADK integration to be added.

        Args:
            prompt_key: Type of text to generate
            context: Variables for generation

        Returns:
            Generated text
        """
        # TODO: Implement ADK LLM call
        if self._adk_agent is None:
            logger.debug(f"Using template fallback for {prompt_key}")
            return await self._fallback.generate_text(prompt_key, context)

        # Future ADK implementation:
        # prompt = self._build_prompt(prompt_key, context)
        # result = await self._adk_agent.run(prompt)
        # return result.get("text", "")

        return await self._fallback.generate_text(prompt_key, context)

    def _build_prompt(self, prompt_key: str, context: Dict[str, Any]) -> str:
        """Build LLM prompt for text generation."""
        topic = context.get("topic", "the subject")

        prompts = {
            "quiz_question": f"Generate an engaging quiz question about {topic}. Return only the question text.",
            "quiz_option": f"Generate a plausible but incorrect answer option for a quiz about {topic}. Return only the option text.",
            "quiz_option_correct": f"Generate the correct answer for a quiz question about {topic}. Return only the option text.",
            "quiz_explanation": f"Explain why this answer is correct in the context of {topic}. Be concise.",
            "story_opening": f"Write an engaging opening paragraph for an interactive story about {topic}.",
            "story_path": f"Write a short paragraph describing the next scene in a story about {topic}.",
            "story_ending": f"Write a satisfying conclusion for a story about {topic}.",
            "game_quest": f"Create a quest title for a game about {topic}.",
            "game_objective": f"Create a specific objective for a quest about {topic}.",
            "simulation_description": f"Write a brief description for an interactive simulation about {topic}.",
        }

        return prompts.get(prompt_key, f"Generate content about {topic}")


__all__ = ["TextProvider", "TemplateTextProvider", "GeminiTextProvider"]
