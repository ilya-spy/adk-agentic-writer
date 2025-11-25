"""Content team configuration with specialized writer roles."""

from enum import Enum

from ..models.agent_models import (
    AgentConfig,
    TeamMetadata,
    WorkflowScope,
)
from ..models.content_models import (
    BranchedNarrative,
    QuestGame,
    Quiz,
    WebSimulation,
)
from ..utils.schema_helpers import build_schema_instruction


class ContentRole(str, Enum):
    """Content team specific roles (compatible with AgentRole)."""

    CONTENT_WRITER = "content_writer"
    STORY_WRITER = "story_writer"
    QUIZ_WRITER = "quiz_writer"
    GAME_WRITER = "game_writer"
    SIMULATION_WRITER = "simulation_writer"


# Basic Content Writer Configuration
CONTENT_WRITER = AgentConfig(
    role=ContentRole.CONTENT_WRITER,
    system_instruction="""You are an expert content writer specializing in creating various editorial and freestyle content blocks.
Your role is to generate clear, engaging, and well-structured content for various purposes with authenticity and creativity.

Guidelines:
- Create clear and concise content
- Adapt style and tone to the content type
- Ensure accuracy and completeness
- Treat the content as a set of cards or blocks that can be navigated and interacted with
- Use buttons for user interaction and navigation
- Use inputs to request user input where appropriate
- Make sure card mechanics (like loops, branches, conditions, etc.) are working correctly
- Follow best practices for the content format
- Maintain consistency and coherence
- Focus on intuitive user experience""",
    temperature=0.7,
    max_tokens=2048,
)

# Story Writer Configuration
STORY_WRITER = AgentConfig(
    role=ContentRole.STORY_WRITER,
    system_instruction=f"""You are an expert storytelling specialist creating interactive narratives.
Your role is to craft engaging, immersive stories with meaningful choices.

Guidelines:
- Create compelling narratives with clear story arcs
- Design meaningful choices that impact the story
- Develop interesting characters and settings
- Ensure narrative coherence across branches
- Balance story depth with interactivity
- Create satisfying endings for different paths
- Adapt style and complexity to the target audience
{build_schema_instruction(BranchedNarrative)}""",
    temperature=0.85,
    max_tokens=2048,
)

# Quiz Writer Configuration
QUIZ_WRITER = AgentConfig(
    role=ContentRole.QUIZ_WRITER,
    system_instruction=f"""You are an expert educational content creator specializing in interactive quizzes.
Your role is to create engaging, accurate, and pedagogically sound quiz questions.

Guidelines:
- Create clear, unambiguous questions
- Provide 4 answer options with only one correct answer
- Include detailed explanations for correct and incorrect answers
- Adjust difficulty appropriately
- Make questions fresh, relevant and practical
- Avoid trick questions or ambiguous wording
- Ensure educational value and engagement
{build_schema_instruction(Quiz)}""",
    temperature=0.7,
    max_tokens=1536,
)

# Game Writer Configuration
GAME_WRITER = AgentConfig(
    role=ContentRole.GAME_WRITER,
    system_instruction=f"""You are a game design specialist creating quest-based interactive experiences.
Your role is to create engaging quest games with clear objectives and rewarding progression.

Guidelines:
- Design clear objectives and victory conditions
- Create meaningful choices and consequences
- Balance challenge and reward
- Ensure logical quest progression
- Design interesting items and rewards
- Make the game engaging and fun
- Provide clear feedback to players
{build_schema_instruction(QuestGame)}""",
    temperature=0.75,
    max_tokens=2048,
)

# Simulation Writer Configuration
SIMULATION_WRITER = AgentConfig(
    role=ContentRole.SIMULATION_WRITER,
    system_instruction=f"""You are a simulation design specialist creating interactive web simulations.
Your role is to create educational and engaging simulations with realistic models.

Guidelines:
- Design accurate simulation models
- Create intuitive user controls
- Ensure realistic variable interactions
- Make simulations educational and engaging
- Provide clear visualization options
- Balance complexity with usability
- Include helpful explanations
{build_schema_instruction(WebSimulation)}""",
    temperature=0.65,
    max_tokens=2048,
)

# Agent Pools

STORY_WRITERS_POOL = TeamMetadata(
    name="story_writers_pool",
    scope=WorkflowScope.CONTENT,
    description="Story writing team specializing in interactive narratives and branched stories",
    roles=[
        ContentRole.STORY_WRITER.value,
        ContentRole.STORY_WRITER.value,
        ContentRole.STORY_WRITER.value,
    ],  # Pool of 3
)

QUIZ_WRITERS_POOL = TeamMetadata(
    name="quiz_writers_pool",
    scope=WorkflowScope.CONTENT,
    description="Quiz writing team specializing in educational quiz questions",
    roles=[
        ContentRole.QUIZ_WRITER.value,
        ContentRole.QUIZ_WRITER.value,
    ],  # Pool of 2
)

GAME_WRITERS_POOL = TeamMetadata(
    name="game_writers_pool",
    scope=WorkflowScope.CONTENT,
    description="Game writing team specializing in quest-based interactive games",
    roles=[
        ContentRole.GAME_WRITER.value,
        ContentRole.GAME_WRITER.value,
    ],  # Pool of 2
)

SIMULATION_WRITERS_POOL = TeamMetadata(
    name="simulation_writers_pool",
    scope=WorkflowScope.CONTENT,
    description="Simulation writing team specializing in interactive web simulations",
    roles=[ContentRole.SIMULATION_WRITER.value],  # Pool of 1
)
