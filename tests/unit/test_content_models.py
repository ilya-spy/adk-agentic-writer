"""Tests for content models."""

from adk_agentic_writer.models.content_models import (
    ContentType,
    Quiz,
    QuizQuestion,
    QuestGame,
    QuestNode,
    BranchedNarrative,
    StoryNode,
    WebSimulation,
    SimulationVariable,
)


def test_quiz_question_creation() -> None:
    """Test creating a quiz question."""
    question = QuizQuestion(
        question="What is Python?",
        options=["A snake", "A programming language", "A movie", "A game"],
        correct_answer=1,
        explanation="Python is a high-level programming language",
        difficulty="easy",
    )
    
    assert question.question == "What is Python?"
    assert len(question.options) == 4
    assert question.correct_answer == 1
    assert question.difficulty == "easy"


def test_quiz_creation() -> None:
    """Test creating a quiz."""
    questions = [
        QuizQuestion(
            question="What is 2+2?",
            options=["3", "4", "5", "6"],
            correct_answer=1,
        )
    ]
    
    quiz = Quiz(
        title="Math Quiz",
        description="Test your math skills",
        questions=questions,
        passing_score=70,
    )
    
    assert quiz.title == "Math Quiz"
    assert len(quiz.questions) == 1
    assert quiz.passing_score == 70


def test_quest_node_creation() -> None:
    """Test creating a quest node."""
    node = QuestNode(
        node_id="start",
        title="The Beginning",
        description="You are at the start of your journey",
        choices=[
            {"text": "Go left", "next_node_id": "left"},
            {"text": "Go right", "next_node_id": "right"},
        ],
        rewards=["Map"],
    )
    
    assert node.node_id == "start"
    assert node.title == "The Beginning"
    assert len(node.choices) == 2
    assert "Map" in node.rewards


def test_story_node_creation() -> None:
    """Test creating a story node."""
    node = StoryNode(
        node_id="chapter1",
        content="Once upon a time...",
        branches=[
            {"text": "Continue", "next_node_id": "chapter2"},
        ],
        tags=["beginning", "fantasy"],
        is_ending=False,
    )
    
    assert node.node_id == "chapter1"
    assert "fantasy" in node.tags
    assert not node.is_ending


def test_simulation_variable_creation() -> None:
    """Test creating a simulation variable."""
    var = SimulationVariable(
        name="temperature",
        initial_value=20.0,
        min_value=-10.0,
        max_value=50.0,
        unit="°C",
    )
    
    assert var.name == "temperature"
    assert var.initial_value == 20.0
    assert var.unit == "°C"
