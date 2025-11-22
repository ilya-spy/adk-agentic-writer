"""Data models for interactive content types."""

from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Types of interactive content that can be generated."""

    QUIZ = "quiz"
    QUEST_GAME = "quest_game"
    BRANCHED_NARRATIVE = "branched_narrative"
    WEB_SIMULATION = "web_simulation"


class QuizQuestion(BaseModel):
    """A single quiz question with answers."""

    question: str = Field(..., description="The question text")
    options: List[str] = Field(..., description="List of answer options")
    correct_answer: int = Field(..., description="Index of the correct answer")
    explanation: Optional[str] = Field(None, description="Explanation of the answer")
    difficulty: str = Field("medium", description="Question difficulty: easy, medium, hard")


class Quiz(BaseModel):
    """Complete quiz structure."""

    title: str = Field(..., description="Quiz title")
    description: str = Field(..., description="Quiz description")
    questions: List[QuizQuestion] = Field(..., description="List of questions")
    time_limit: Optional[int] = Field(None, description="Time limit in minutes")
    passing_score: int = Field(70, description="Minimum percentage to pass")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QuestNode(BaseModel):
    """A node in a quest game."""

    node_id: str = Field(..., description="Unique identifier for this node")
    title: str = Field(..., description="Node title")
    description: str = Field(..., description="Node description/narrative")
    choices: List[Dict[str, str]] = Field(
        default_factory=list, description="Available choices: {text, next_node_id}"
    )
    rewards: List[str] = Field(default_factory=list, description="Items or achievements gained")
    requirements: List[str] = Field(
        default_factory=list, description="Required items or conditions"
    )


class QuestGame(BaseModel):
    """Complete quest game structure."""

    title: str = Field(..., description="Game title")
    description: str = Field(..., description="Game overview")
    start_node: str = Field(..., description="ID of the starting node")
    nodes: Dict[str, QuestNode] = Field(..., description="Map of node_id to QuestNode")
    victory_conditions: List[str] = Field(
        default_factory=list, description="Conditions to win the game"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StoryNode(BaseModel):
    """A node in a branched narrative."""

    node_id: str = Field(..., description="Unique identifier for this node")
    content: str = Field(..., description="Story content at this node")
    branches: List[Dict[str, str]] = Field(
        default_factory=list, description="Available branches: {text, next_node_id, condition?}"
    )
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    is_ending: bool = Field(False, description="Whether this is an ending node")


class BranchedNarrative(BaseModel):
    """Complete branched narrative structure."""

    title: str = Field(..., description="Story title")
    synopsis: str = Field(..., description="Story synopsis")
    genre: str = Field(..., description="Story genre")
    start_node: str = Field(..., description="ID of the starting node")
    nodes: Dict[str, StoryNode] = Field(..., description="Map of node_id to StoryNode")
    characters: List[str] = Field(default_factory=list, description="Main characters")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SimulationVariable(BaseModel):
    """A variable in a web simulation."""

    name: str = Field(..., description="Variable name")
    initial_value: float = Field(..., description="Initial value")
    min_value: Optional[float] = Field(None, description="Minimum allowed value")
    max_value: Optional[float] = Field(None, description="Maximum allowed value")
    unit: Optional[str] = Field(None, description="Unit of measurement")


class SimulationControl(BaseModel):
    """A user control in the simulation."""

    control_id: str = Field(..., description="Unique control identifier")
    label: str = Field(..., description="Control label")
    type: str = Field(..., description="Control type: slider, button, toggle")
    affects: List[str] = Field(..., description="Variables affected by this control")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Control-specific params")


class WebSimulation(BaseModel):
    """Complete web simulation structure."""

    title: str = Field(..., description="Simulation title")
    description: str = Field(..., description="Simulation description")
    variables: List[SimulationVariable] = Field(..., description="Simulation variables")
    controls: List[SimulationControl] = Field(..., description="User controls")
    rules: List[str] = Field(..., description="Simulation rules/equations")
    visualization_type: str = Field(
        "chart", description="Type of visualization: chart, animation, 3d"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContentRequest(BaseModel):
    """Request to generate interactive content."""

    content_type: ContentType = Field(..., description="Type of content to generate")
    topic: str = Field(..., description="Topic or theme")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Additional generation parameters"
    )
    user_id: Optional[str] = Field(None, description="User making the request")


class ContentResponse(BaseModel):
    """Response containing generated content."""

    request_id: str = Field(..., description="Unique request identifier")
    content_type: ContentType = Field(..., description="Type of content generated")
    content: Dict[str, Any] = Field(..., description="Generated content data")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: str = Field("completed", description="Generation status")
    agents_involved: List[str] = Field(default_factory=list, description="Agents that worked on this")
