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
    """

    content_type: str
    model_class: Type[BaseModel]
    agent_config: AgentConfig
    category: str  # "writer" or "designer"
    default_params: Dict[str, Any] = field(default_factory=dict)
    title_template: str = "{topic} Content"
    description_template: str = "Content about {topic}"
    component_models: Dict[str, Type[BaseModel]] = field(default_factory=dict)


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
            "passing_score": 70,
        },
        title_template="{topic} Quiz",
        description_template="Test your knowledge about {topic}",
        component_models={"question": QuizQuestion},
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
    )
)

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
    )
)


__all__ = ["ContentTypeConfig", "ContentRegistry", "CONTENT_REGISTRY"]
