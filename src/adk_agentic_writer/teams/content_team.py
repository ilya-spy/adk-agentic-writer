"""Content team configuration with specialized writer roles."""

from enum import Enum

from ..models.agent_models import (
    AgentConfig,
    AgentRole,
    TeamMetadata,
    WorkflowMetadata,
    WorkflowPattern,
    WorkflowScope,
)


class ContentRole(str, Enum):
    """Content team specific roles (compatible with AgentRole)."""

    STORY_WRITER = "story_writer"
    QUIZ_WRITER = "quiz_writer"
    GAME_WRITER = "game_writer"
    SIMULATION_WRITER = "simulation_writer"


# Story Writer Configuration
STORY_WRITER = AgentConfig(
    role=ContentRole.STORY_WRITER,
    system_instruction="""You are an expert storytelling specialist creating interactive narratives.
Your role is to craft engaging, immersive stories with meaningful choices.

Guidelines:
- Create compelling narratives with clear story arcs
- Design meaningful choices that impact the story
- Develop interesting characters and settings
- Ensure narrative coherence across branches
- Balance story depth with interactivity
- Create satisfying endings for different paths
- Adapt style and complexity to the target audience""",
    temperature=0.85,
    max_tokens=2048,
    workflows=[
        WorkflowMetadata(
            name="sequential_generation",
            pattern=WorkflowPattern.SEQUENTIAL,
            scope=WorkflowScope.CONTENT,
            description="Generate story content in sequence",
        ),
        WorkflowMetadata(
            name="branched_generation",
            pattern=WorkflowPattern.CONDITIONAL,
            scope=WorkflowScope.CONTENT,
            description="Generate branched narrative with choices",
        ),
    ],
)

# Quiz Writer Configuration
QUIZ_WRITER = AgentConfig(
    role=ContentRole.QUIZ_WRITER,
    system_instruction="""You are an expert educational content creator specializing in interactive quizzes.
Your role is to create engaging, accurate, and pedagogically sound quiz questions.

Guidelines:
- Create clear, unambiguous questions
- Provide 4 answer options with only one correct answer
- Include detailed explanations for correct answers
- Adjust difficulty appropriately
- Make questions relevant and practical
- Avoid trick questions or ambiguous wording
- Ensure educational value and engagement""",
    temperature=0.7,
    max_tokens=1536,
    workflows=[
        WorkflowMetadata(
            name="sequential_generation",
            pattern=WorkflowPattern.SEQUENTIAL,
            scope=WorkflowScope.CONTENT,
            description="Generate quiz questions in sequence",
        ),
        WorkflowMetadata(
            name="looped_generation",
            pattern=WorkflowPattern.LOOP,
            scope=WorkflowScope.CONTENT,
            description="Generate practice question sets",
            max_iterations=10,
        ),
    ],
)

# Game Writer Configuration
GAME_WRITER = AgentConfig(
    role=ContentRole.GAME_WRITER,
    system_instruction="""You are a game design specialist creating quest-based interactive experiences.
Your role is to create engaging quest games with clear objectives and rewarding progression.

Guidelines:
- Design clear objectives and victory conditions
- Create meaningful choices and consequences
- Balance challenge and reward
- Ensure logical quest progression
- Design interesting items and rewards
- Make the game engaging and fun
- Provide clear feedback to players""",
    temperature=0.75,
    max_tokens=2048,
    workflows=[
        WorkflowMetadata(
            name="sequential_generation",
            pattern=WorkflowPattern.SEQUENTIAL,
            scope=WorkflowScope.CONTENT,
            description="Generate game quests in sequence",
        ),
        WorkflowMetadata(
            name="branched_generation",
            pattern=WorkflowPattern.CONDITIONAL,
            scope=WorkflowScope.CONTENT,
            description="Generate branched quest paths",
        ),
    ],
)

# Simulation Writer Configuration
SIMULATION_WRITER = AgentConfig(
    role=ContentRole.SIMULATION_WRITER,
    system_instruction="""You are a simulation design specialist creating interactive web simulations.
Your role is to create educational and engaging simulations with realistic models.

Guidelines:
- Design accurate simulation models
- Create intuitive user controls
- Ensure realistic variable interactions
- Make simulations educational and engaging
- Provide clear visualization options
- Balance complexity with usability
- Include helpful explanations""",
    temperature=0.65,
    max_tokens=2048,
    workflows=[
        WorkflowMetadata(
            name="sequential_generation",
            pattern=WorkflowPattern.SEQUENTIAL,
            scope=WorkflowScope.CONTENT,
            description="Generate simulation components in sequence",
        ),
    ],
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
