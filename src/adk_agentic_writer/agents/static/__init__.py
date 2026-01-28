"""Static agents with template-based content generation.

Core agents:
- WriterAgent: Text-based content (Quiz, Story)
- DesignerAgent: Structural content (Game, Simulation)
- CoordinatorAgent: Orchestrates content generation

Uses content registry for extensibility.
"""

from .coordinator import CoordinatorAgent

# Unified agents
from .writer import (
    WriterAgent,
    StaticQuizWriterAgent,
    StoryWriterAgent,
    create_quiz_writer,
    create_story_writer,
)
from .designer import (
    DesignerAgent,
    GameDesignerAgent,
    SimulationDesignerAgent,
    create_game_designer,
    create_simulation_designer,
)

__all__ = [
    # Coordinator
    "CoordinatorAgent",
    # Unified agents
    "WriterAgent",
    "DesignerAgent",
    # Backward-compatible aliases
    "StaticQuizWriterAgent",
    "StoryWriterAgent",
    "GameDesignerAgent",
    "SimulationDesignerAgent",
    # Factory functions
    "create_quiz_writer",
    "create_story_writer",
    "create_game_designer",
    "create_simulation_designer",
]
