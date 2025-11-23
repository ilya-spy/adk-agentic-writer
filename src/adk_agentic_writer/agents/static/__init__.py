"""Static agents with template-based content generation."""

from .coordinator import CoordinatorAgent
from .game_designer import GameDesignerAgent
from .quiz_writer import StaticQuizWriterAgent
from .reviewer import ReviewerAgent
from .simulation_designer import SimulationDesignerAgent
from .story_writer import StoryWriterAgent

__all__ = [
    "StaticQuizWriterAgent",
    "StoryWriterAgent",
    "GameDesignerAgent",
    "SimulationDesignerAgent",
    "ReviewerAgent",
    "CoordinatorAgent",
]
