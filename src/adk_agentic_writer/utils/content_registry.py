"""Content type registry for extensible content generation.

Provides a registry pattern for content types, allowing new content types
to be added without creating new agent classes.

Usage:
    # Register a new content type
    CONTENT_REGISTRY.register(ContentTypeConfig(
        content_type="my_content",
        model_class=MyContentModel,
        agent_config=MY_AGENT_CONFIG,
        category="writer",  # or "designer"
        default_params={"field": "value"},
        schema_description="JSON schema for this content...",
        sample_output={"example": "data"},
    ))

    # Get config for content type
    config = CONTENT_REGISTRY.get("my_content")
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

from ..models.content_models import (
    Quiz,
    QuizQuestion,
    BranchedNarrative,
    StoryNode,
    QuestGame,
    QuestNode,
    WebSimulation,
    SimulationVariable,
    SimulationControl,
)
from ..models.agent_models import AgentConfig
from ..teams.content_team import (
    QUIZ_WRITER,
    STORY_WRITER,
    GAME_WRITER,
    SIMULATION_WRITER,
)
from .schema_helpers import build_schema_instruction


# =============================================================================
# Schema Descriptions (centralized for all content types)
# =============================================================================

QUIZ_SCHEMA_DESCRIPTION = """
Output JSON Schema:
{
  "title": "string - Engaging quiz title",
  "description": "string - Brief quiz description",
  "questions": [
    {
      "question": "string - The question text",
      "options": ["string", "string", ...],
      "correct_answer": 0,
      "explanation": "string - Why this answer is correct",
      "tier": "low|mid|high",
      "score": 1
    }
  ],
  "passing_score": 6,
  "time_limit": 10
}

CRITICAL scoring rules:
- tier MUST be one of exactly: "low", "mid", "high" (NOT the overall difficulty name)
- score MUST match the tier: low=1, mid=2, high=3
- The quiz MUST contain at least one question at EACH tier (low, mid, high)
- passing_score = integer, 60-70% of total points
- time_limit = integer minutes
- Vary correct_answer index across questions"""

STORY_SCHEMA_DESCRIPTION = """
Output JSON Schema:
{
  "title": "string - Story title",
  "synopsis": "string - Brief story overview",
  "genre": "string - Story genre",
  "start_node": "start",
  "nodes": {
    "start": {
      "node_id": "start",
      "content": "string - Opening narrative",
      "branches": [{"text": "choice", "next_node_id": "node_0"}],
      "tags": ["opening"],
      "is_ending": false
    },
    "ending_0": {
      "node_id": "ending_0",
      "content": "string - Ending narrative",
      "branches": [],
      "tags": ["ending"],
      "is_ending": true
    }
  },
  "characters": ["string"]
}"""


# =============================================================================
# Sample Outputs (for model guidance)
# =============================================================================

SAMPLE_QUIZ_OUTPUT = {
    "title": "Python Programming Fundamentals",
    "description": "Test your knowledge of Python basics",
    "questions": [
        {
            "question": "What keyword is used to define a function in Python?",
            "options": ["function", "def", "func", "define"],
            "correct_answer": 1,
            "explanation": "In Python, functions are defined using the 'def' keyword.",
            "tier": "low",
            "score": 1,
        },
        {
            "question": "What does 'list comprehension' do in Python?",
            "options": [
                "Creates a list from a loop expression",
                "Sorts a list in place",
                "Converts a tuple to a list",
                "Removes duplicates from a list",
            ],
            "correct_answer": 0,
            "explanation": "List comprehension creates a new list by applying an expression to each item in an iterable.",
            "tier": "mid",
            "score": 2,
        },
        {
            "question": "What is the output of: print(type(lambda x: x))?",
            "options": ["<class 'function'>", "<class 'lambda'>", "function", "SyntaxError"],
            "correct_answer": 0,
            "explanation": "Lambda expressions create function objects, so type() returns <class 'function'>.",
            "tier": "high",
            "score": 3,
        },
    ],
    "passing_score": 4,
    "time_limit": 5,
}

SAMPLE_STORY_OUTPUT = {
    "title": "The Quest for Knowledge",
    "synopsis": "An adventure through the realm of learning",
    "genre": "fantasy",
    "start_node": "start",
    "nodes": {
        "start": {
            "node_id": "start",
            "content": "You stand at the entrance of the ancient library...",
            "branches": [
                {"text": "Enter through the main door", "next_node_id": "node_0"},
                {"text": "Search for a side entrance", "next_node_id": "node_1"},
            ],
            "tags": ["opening"],
            "is_ending": False,
        },
        "ending_0": {
            "node_id": "ending_0",
            "content": "You emerge victorious with newfound wisdom...",
            "branches": [],
            "tags": ["ending", "victory"],
            "is_ending": True,
        },
    },
    "characters": ["Protagonist", "The Keeper"],
}


@dataclass
class ContentTypeConfig:
    """Configuration for a content type.

    Attributes:
        content_type: Unique identifier (e.g., "quiz", "story")
        model_class: The Pydantic model class for this content
        agent_config: The AgentConfig for agents handling this type
        category: "writer" for text content, "designer" for structural content
        default_params: Default parameters when none provided
        title_template: Template for generating title (uses {topic})
        description_template: Template for description (uses {topic})
        schema_description: JSON schema description for structured output
        sample_output: Sample output for model guidance
    """

    content_type: str
    model_class: Type[BaseModel]
    agent_config: AgentConfig
    category: str  # "writer" or "designer"
    default_params: Dict[str, Any] = field(default_factory=dict)
    title_template: str = "{topic} Content"
    description_template: str = "Content about {topic}"
    component_models: Dict[str, Type[BaseModel]] = field(default_factory=dict)
    schema_description: str = ""
    sample_output: Dict[str, Any] = field(default_factory=dict)


class ContentRegistry:
    """Registry for content type configurations."""

    def __init__(self):
        self._registry: Dict[str, ContentTypeConfig] = {}

    def register(self, config: ContentTypeConfig) -> None:
        """Register a content type configuration."""
        self._registry[config.content_type] = config

    def get(self, content_type: str) -> Optional[ContentTypeConfig]:
        """Get configuration for a content type."""
        return self._registry.get(content_type)

    def get_by_category(self, category: str) -> Dict[str, ContentTypeConfig]:
        """Get all content types in a category."""
        return {k: v for k, v in self._registry.items() if v.category == category}

    def list_types(self) -> list:
        """List all registered content types."""
        return list(self._registry.keys())

    def __contains__(self, content_type: str) -> bool:
        return content_type in self._registry


# Global registry instance
CONTENT_REGISTRY = ContentRegistry()

# =============================================================================
# Register built-in content types
# =============================================================================

CONTENT_REGISTRY.register(
    ContentTypeConfig(
        content_type="quiz",
        model_class=Quiz,
        agent_config=QUIZ_WRITER,
        category="writer",
        default_params={
            "num_questions": 5,
            "difficulty": "medium",
            "num_options": 4,
            "passing_score": 70,
        },
        title_template="{topic} Quiz",
        description_template="Test your knowledge about {topic}",
        component_models={"question": QuizQuestion},
        schema_description=QUIZ_SCHEMA_DESCRIPTION,
        sample_output=SAMPLE_QUIZ_OUTPUT,
    )
)

CONTENT_REGISTRY.register(
    ContentTypeConfig(
        content_type="branched_narrative",
        model_class=BranchedNarrative,
        agent_config=STORY_WRITER,
        category="writer",
        default_params={"genre": "fantasy", "num_nodes": 7},
        title_template="The {topic} Chronicles",
        description_template="An interactive story about {topic}",
        component_models={"node": StoryNode},
        schema_description=STORY_SCHEMA_DESCRIPTION,
        sample_output=SAMPLE_STORY_OUTPUT,
    )
)

CONTENT_REGISTRY.register(
    ContentTypeConfig(
        content_type="story",
        model_class=BranchedNarrative,
        agent_config=STORY_WRITER,
        category="writer",
        default_params={"genre": "fantasy", "num_nodes": 7},
        title_template="The {topic} Chronicles",
        description_template="An interactive story about {topic}",
        component_models={"node": StoryNode},
        schema_description=STORY_SCHEMA_DESCRIPTION,
        sample_output=SAMPLE_STORY_OUTPUT,
    )
)

# Game and simulation use build_schema_instruction for dynamic schema
CONTENT_REGISTRY.register(
    ContentTypeConfig(
        content_type="quest_game",
        model_class=QuestGame,
        agent_config=GAME_WRITER,
        category="designer",
        default_params={"complexity": "medium", "theme": "fantasy", "num_nodes": 5},
        title_template="{topic} Quest",
        description_template="An interactive quest game about {topic}",
        component_models={"node": QuestNode},
        schema_description=build_schema_instruction(QuestGame),
        sample_output={},
    )
)

CONTENT_REGISTRY.register(
    ContentTypeConfig(
        content_type="game",
        model_class=QuestGame,
        agent_config=GAME_WRITER,
        category="designer",
        default_params={"complexity": "medium", "theme": "fantasy", "num_nodes": 5},
        title_template="{topic} Quest",
        description_template="An interactive quest game about {topic}",
        component_models={"node": QuestNode},
        schema_description=build_schema_instruction(QuestGame),
        sample_output={},
    )
)

CONTENT_REGISTRY.register(
    ContentTypeConfig(
        content_type="web_simulation",
        model_class=WebSimulation,
        agent_config=SIMULATION_WRITER,
        category="designer",
        default_params={"complexity": "medium", "simulation_type": "interactive"},
        title_template="{topic} Simulation",
        description_template="An interactive simulation about {topic}",
        component_models={"variable": SimulationVariable, "control": SimulationControl},
        schema_description=build_schema_instruction(WebSimulation),
        sample_output={},
    )
)

CONTENT_REGISTRY.register(
    ContentTypeConfig(
        content_type="simulation",
        model_class=WebSimulation,
        agent_config=SIMULATION_WRITER,
        category="designer",
        default_params={"complexity": "medium", "simulation_type": "interactive"},
        title_template="{topic} Simulation",
        description_template="An interactive simulation about {topic}",
        component_models={"variable": SimulationVariable, "control": SimulationControl},
        schema_description=build_schema_instruction(WebSimulation),
        sample_output={},
    )
)


__all__ = [
    "ContentTypeConfig",
    "ContentRegistry",
    "CONTENT_REGISTRY",
    # Schema definitions
    "QUIZ_SCHEMA_DESCRIPTION",
    "STORY_SCHEMA_DESCRIPTION",
    "SAMPLE_QUIZ_OUTPUT",
    "SAMPLE_STORY_OUTPUT",
]
