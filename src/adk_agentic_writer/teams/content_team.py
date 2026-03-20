"""Content team configuration with specialized writer roles.

Each role includes:
- System instruction
- Generation prompt template
- Prompt templates for individual blocks
- Prompt modifiers for customization
- Schema description and sample output for structured generation
"""

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
from ..utils.schema import build_schema_instruction


class ContentRole(str, Enum):
    """Content team specific roles (compatible with AgentRole)."""

    CONTENT_WRITER = "content_writer"
    STORY_WRITER = "story_writer"
    QUIZ_WRITER = "quiz_writer"
    GAME_WRITER = "game_writer"
    SIMULATION_WRITER = "simulation_writer"


# =============================================================================
# Common Prompt Components
# =============================================================================

_COMMON_INSTRUCTION = """You are an expert content prodcustion seniot staff specializing in interactive and engaging content for modern editorials.
Your responses must be valid JSON matching the exact schema provided.
Be creative, engaging, and educational. Ensure all content is appropriate for general audiences."""

_JSON_OUTPUT_INSTRUCTION = """
CRITICAL: You MUST respond with valid JSON only. No markdown, no explanations, no code blocks.
The JSON must exactly match the schema structure provided."""


# =============================================================================
# Quiz Writer Configuration
# =============================================================================

QUIZ_WRITER = AgentConfig(
    role=ContentRole.QUIZ_WRITER,
    instruction=f"""{_COMMON_INSTRUCTION}

You create engaging educational quizzes with:
- Clear, thought-provoking questions
- Helpful explanations for the correct answer
- Varying difficulty levels

{_JSON_OUTPUT_INSTRUCTION}""",
    temperature=0.7,
    max_tokens=1536,
    generation_prompt="""Generate an educational quiz about "{topic}".

The overall TOPIC difficulty is "{difficulty}" — this controls how hard the question
CONTENT is (e.g. easy = beginner-friendly facts, hard = advanced/tricky knowledge).

IMPORTANT -- follow ALL of these rules precisely:

1. Create exactly {num_questions} questions.
2. Each question MUST have exactly {num_options} answer options (not more, not fewer).
3. Include a brief explanation for each answer.
4. SCORING TIERS (in addition as a modifier to overall topic difficulty):
   Every quiz MUST contain a MIX of three scoring tiers:
     - "low"  tier = 1 point  (straightforward recall)
     - "mid"  tier = 2 points (requires understanding)
     - "high" tier = 3 points (requires analysis / synthesis)
   You MUST include at least one question at EACH tier. Distribute evenly.
   Set each question's "tier" field to exactly "low", "mid", or "high".
   Set each question's "score" field to the matching value (1, 2, or 3).
5. Create questions wisely, according to global quiz difficulty and tiered adjustment witin the difficulty.
6. Try creative question sequences, not simply round-robin from low to high tiers.""",
    prompt_templates={
        # Complete question generation (preferred - LLM decides correct answer)
        "quiz_question_complete": """Generate one quiz question about {topic} at {difficulty} difficulty.

Return valid JSON:
{{"question": "...", "options": ["A","B","C","D"], "correct_answer": 0,
  "explanation": "...", "tier": "low|mid|high", "score": 1}}

- Exactly {num_options} options, correct_answer = 0-based index
- Plausible distractors, educational explanation
- Return ONLY the JSON object""",
        # Legacy individual prompts (fallback)
    },
    prompt_modifiers={
        "difficulty_easy": "Keep questions simple and straightforward, suitable for beginners.",
        "difficulty_medium": "Include some nuanced questions that require deeper understanding.",
        "difficulty_hard": "Make questions challenging, testing advanced knowledge and critical thinking.",
        "formal_tone": "Use formal, academic language appropriate for educational settings.",
        "casual_tone": "Use friendly, conversational language to make learning fun.",
    },
)


# =============================================================================
# Story Writer Configuration
# =============================================================================

STORY_WRITER = AgentConfig(
    role=ContentRole.STORY_WRITER,
    instruction=f"""{_COMMON_INSTRUCTION}

You create immersive branched narratives with:
- Compelling opening hooks
- Multiple story paths and endings
- Rich descriptive content
- Meaningful choices that affect the story

{_JSON_OUTPUT_INSTRUCTION}""",
    temperature=0.85,
    max_tokens=2048,
    generation_prompt="""Create a branched interactive narrative about "{topic}".

Requirements:
- Genre: {genre}
- Create approximately {num_nodes} story nodes
- Include a "start" node as the entry point
- Include at least 2 different endings (ending_0, ending_1, etc.)
- Each non-ending node should have 1-3 branches (choices)
- Branches format: {{"text": "choice text", "next_node_id": "node_id"}}

Make the story engaging with vivid descriptions and meaningful choices.""",
    prompt_templates={
        # Complete story node generation (preferred - LLM decides branches)
        "story_node_complete": """Generate a story node for an interactive {genre} narrative about {topic}.

Node context:
- Node ID: {node_id}
- Node type: {node_type}
- Available next nodes: {available_nodes}

Return valid JSON with this exact structure:
{{
  "node_id": "{node_id}",
  "content": "2-4 sentences of narrative text",
  "branches": [
    {{"text": "Choice description (5-10 words)", "next_node_id": "valid_node_id"}}
  ],
  "tags": ["relevant", "tags"],
  "is_ending": false
}}

Requirements:
- Content should be vivid and engaging
- Each branch text should be a meaningful player choice
- Branch next_node_id MUST be from available_nodes list
- If this is an ending node, set is_ending: true and branches: []
- Return ONLY the JSON object""",
        # Complete story structure (for generating interconnected nodes)
        "story_structure": """Create a complete branched story structure about {topic} in the {genre} genre.

Requirements:
- Create exactly {num_nodes} nodes total
- Include a "start" node as entry point
- Include {num_endings} ending nodes (ending_0, ending_1, etc.)
- Middle nodes should be named node_0, node_1, etc.
- Each non-ending node needs 1-3 branches with meaningful choices
- All branches must connect to valid existing nodes
- Create multiple paths through the story

Return valid JSON with this structure:
{{
  "nodes": {{
    "start": {{"node_id": "start", "content": "...", "branches": [...], "tags": [...], "is_ending": false}},
    "node_0": {{...}},
    "ending_0": {{"node_id": "ending_0", "content": "...", "branches": [], "tags": ["ending"], "is_ending": true}}
  }}
}}""",
        # Legacy individual prompts (fallback)
        "story_opening": "Write an engaging opening paragraph (3-4 sentences) for an interactive {genre} story about {topic}.",
        "story_path": "Write a short paragraph (2-3 sentences) describing the next scene in a {genre} story about {topic}.",
        "story_ending": "Write a satisfying {ending_type} conclusion paragraph (2-3 sentences) for a {genre} story about {topic}.",
        "story_branch": "Write a brief choice option (5-10 words) for a story branch leading to {destination}.",
    },
    prompt_modifiers={
        "genre_fantasy": "Use magical elements, mythical creatures, and epic quests.",
        "genre_scifi": "Include futuristic technology, space exploration, and scientific concepts.",
        "genre_mystery": "Create suspense, clues, and unexpected revelations.",
        "genre_adventure": "Focus on exploration, challenges, and exciting discoveries.",
        "tone_dark": "Use a darker, more serious tone with higher stakes.",
        "tone_lighthearted": "Keep the tone fun, optimistic, and accessible.",
    },
)


# =============================================================================
# Game Writer Configuration
# =============================================================================

GAME_WRITER = AgentConfig(
    role=ContentRole.GAME_WRITER,
    instruction=f"""{_COMMON_INSTRUCTION}

You are a game design specialist creating quest-based interactive experiences.
Your role is to create engaging quest games with clear objectives and rewarding progression.

Guidelines:
- Design clear objectives and victory conditions
- Create meaningful choices and consequences
- Balance challenge and reward
- Ensure logical quest progression
- Design interesting items and rewards
- Make the game engaging and fun
- Provide clear feedback to players

{build_schema_instruction(QuestGame)}

{_JSON_OUTPUT_INSTRUCTION}""",
    temperature=0.75,
    max_tokens=2048,
    generation_prompt="""Create an interactive quest game about "{topic}".

Requirements:
- Create approximately {num_nodes} quest nodes
- Include a start node and victory condition
- Each node should have title, description, choices, and rewards
- Design clear progression path with optional side quests""",
    prompt_templates={
        "quest_title": "Create a creative quest title (5-8 words) for a game about {topic}.",
        "quest_objective": "Create a specific objective (one sentence) for a quest about {topic}.",
        "quest_node": "Write a quest node description (2-3 sentences) for {node_type} in a game about {topic}.",
        "quest_choice": "Write a brief choice option (5-10 words) leading to {destination}.",
    },
    prompt_modifiers={
        "complexity_simple": "Keep mechanics simple with linear progression.",
        "complexity_medium": "Add branching paths and optional objectives.",
        "complexity_complex": "Include inventory management, stat checks, and multiple endings.",
    },
)


# =============================================================================
# Simulation Writer Configuration
# =============================================================================

SIMULATION_WRITER = AgentConfig(
    role=ContentRole.SIMULATION_WRITER,
    instruction=f"""{_COMMON_INSTRUCTION}

You are a simulation design specialist creating interactive web simulations.
Your role is to create educational and engaging simulations with realistic models.

Guidelines:
- Design accurate simulation models
- Create intuitive user controls
- Ensure realistic variable interactions
- Make simulations educational and engaging
- Provide clear visualization options
- Balance complexity with usability
- Include helpful explanations

{build_schema_instruction(WebSimulation)}

{_JSON_OUTPUT_INSTRUCTION}""",
    temperature=0.65,
    max_tokens=2048,
    generation_prompt="""Create an interactive simulation about "{topic}".

Requirements:
- Define key variables with realistic ranges
- Create intuitive controls (sliders, buttons, toggles)
- Define rules/equations for variable interactions
- Specify visualization type (chart, animation, 3d)""",
    prompt_templates={
        "simulation_description": "Write a brief description (2-3 sentences) for an interactive simulation about {topic}.",
        "variable_description": "Describe the variable {variable_name} and its role in simulating {topic}.",
        "control_description": "Describe the control {control_name} and how it affects the simulation.",
    },
    prompt_modifiers={
        "complexity_basic": "Keep the model simple with 2-3 variables.",
        "complexity_advanced": "Include multiple interacting variables and feedback loops.",
    },
)


# =============================================================================
# Generic Content Writer Configuration
# =============================================================================

CONTENT_WRITER = AgentConfig(
    role=ContentRole.CONTENT_WRITER,
    instruction=f"""{_COMMON_INSTRUCTION}

Your role is to generate clear, engaging, and well-structured content for various purposes.

Guidelines:
- Create clear and concise content
- Adapt style and tone to the content type
- Ensure accuracy and completeness
- Treat the content as a set of cards or blocks that can be navigated
- Use buttons for user interaction and navigation
- Follow best practices for the content format
- Maintain consistency and coherence
- Focus on intuitive user experience""",
    temperature=0.7,
    max_tokens=2048,
    generation_prompt="Generate content about {topic}.",
    prompt_templates={
        "chapter_content": "Write a chapter paragraph (3-4 sentences) about {topic}.",
        "section_content": "Write a section (2-3 paragraphs) about {topic}.",
    },
    prompt_modifiers={
        "formal_tone": "Use formal, professional language.",
        "casual_tone": "Use friendly, conversational language.",
    },
)


# =============================================================================
# Role Registry - Get config by role enum or string
# =============================================================================

CONTENT_ROLE_CONFIGS = {
    ContentRole.QUIZ_WRITER: QUIZ_WRITER,
    ContentRole.STORY_WRITER: STORY_WRITER,
    ContentRole.GAME_WRITER: GAME_WRITER,
    ContentRole.SIMULATION_WRITER: SIMULATION_WRITER,
    ContentRole.CONTENT_WRITER: CONTENT_WRITER,
    # String aliases
    "quiz_writer": QUIZ_WRITER,
    "story_writer": STORY_WRITER,
    "game_writer": GAME_WRITER,
    "simulation_writer": SIMULATION_WRITER,
    "content_writer": CONTENT_WRITER,
    # Content type aliases
    "quiz": QUIZ_WRITER,
    "story": STORY_WRITER,
    "game": GAME_WRITER,
    "simulation": SIMULATION_WRITER,
}


def get_config_for_role(role: str) -> AgentConfig:
    """Get AgentConfig for a role or content type.

    Args:
        role: Role enum, role string, or content type

    Returns:
        AgentConfig for the role

    Raises:
        ValueError: If role not found
    """
    config = CONTENT_ROLE_CONFIGS.get(role)
    if config is None:
        raise ValueError(
            f"Unknown role: {role}. Available: {list(CONTENT_ROLE_CONFIGS.keys())}"
        )
    return config


# =============================================================================
# Agent Pools (Teams)
# =============================================================================

STORY_WRITERS_POOL = TeamMetadata(
    name="story_writers_pool",
    scope=WorkflowScope.CONTENT,
    description="Story writing team specializing in interactive narratives",
    roles=[ContentRole.STORY_WRITER.value] * 3,
)

QUIZ_WRITERS_POOL = TeamMetadata(
    name="quiz_writers_pool",
    scope=WorkflowScope.CONTENT,
    description="Quiz writing team specializing in educational quizzes",
    roles=[ContentRole.QUIZ_WRITER.value] * 2,
)

GAME_WRITERS_POOL = TeamMetadata(
    name="game_writers_pool",
    scope=WorkflowScope.CONTENT,
    description="Game writing team specializing in quest games",
    roles=[ContentRole.GAME_WRITER.value] * 2,
)

SIMULATION_WRITERS_POOL = TeamMetadata(
    name="simulation_writers_pool",
    scope=WorkflowScope.CONTENT,
    description="Simulation team specializing in interactive simulations",
    roles=[ContentRole.SIMULATION_WRITER.value],
)

__all__ = [
    # Roles
    "ContentRole",
    # Configs
    "CONTENT_WRITER",
    "QUIZ_WRITER",
    "STORY_WRITER",
    "GAME_WRITER",
    "SIMULATION_WRITER",
    # Registry
    "CONTENT_ROLE_CONFIGS",
    "get_config_for_role",
    # Pools / Teams
    "STORY_WRITERS_POOL",
    "QUIZ_WRITERS_POOL",
    "GAME_WRITERS_POOL",
    "SIMULATION_WRITERS_POOL",
]
