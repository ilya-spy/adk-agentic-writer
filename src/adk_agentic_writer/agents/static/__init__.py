"""Static agents with template-based content generation."""

from .coordinator import CoordinatorAgent
from .editor import EditorAgent
from .game_designer import GameDesignerAgent
from .producer import ProducerAgent
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
    "EditorAgent",
    "ProducerAgent",
]
