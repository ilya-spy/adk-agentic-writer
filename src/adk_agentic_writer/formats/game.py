"""Quest game format specification."""

from ..models.content_models import QuestGame
from ..utils.schema import build_schema_instruction
from .base import FormatSpec, ParamSpec

GAME_FORMAT = FormatSpec(
    name="game",
    label="Quest Game",
    model_class=QuestGame,
    default_params={"complexity": "medium", "theme": "fantasy", "num_nodes": 5},
    parameter_specs=[
        ParamSpec("topic", "str", "", "Content topic"),
        ParamSpec("flavor", "str", "game", "Content flavor"),
        ParamSpec(
            "complexity", "str", "medium", "Game complexity: simple, medium, hard"
        ),
        ParamSpec("theme", "str", "fantasy", "Game theme/setting"),
        ParamSpec("num_nodes", "int", 5, "Number of quest nodes"),
    ],
    schema_description=build_schema_instruction(QuestGame),
    writer_instruction="""\
You are an expert content creator specializing in interactive and engaging content.
You are a game design specialist creating quest-based interactive experiences
with clear objectives, meaningful choices, balanced challenge and reward,
and logical quest progression.

CRITICAL: Respond with valid JSON only. No markdown, no explanations, no code blocks.
The JSON must exactly match the schema structure provided.""",
    writer_prompt="""\
Create an interactive gamified {flavor} about "{topic}".

STYLE — adapt to the "{flavor}" format:
- "game": Standard quest game with objectives and rewards.
- "quest_game" / "quest": Focus on a clear quest line with milestones.
- "rpg": Emphasize character stats, inventory, and role-playing choices.

COMPLEXITY — the complexity is "{complexity}":
- "simple": Keep mechanics simple with linear progression.
- "medium": Add branching paths and optional objectives.
- "hard": Include inventory management, stat checks, and multiple endings.

RULES:
- Create approximately {num_nodes} structural content nodes.
- Include a start node and victory condition.
- Each node should have title, description, choices, and rewards.
- Design clear progression path with optional side quests.""",
    reviewer_prompt="""\
Review this quest game. Check:
- A start node exists and is referenced by start_node
- All choice next_node_id values reference existing nodes
- Victory conditions are defined
- Rewards are balanced and meaningful
- Quest progression is logical""",
    refiner_prompt="""\
Refine this quest game. Fix any issues from the review. Ensure:
- All node references are valid
- Quest progression is logical and engaging
- Rewards and requirements are balanced
- Victory conditions are achievable""",
    flavors=["quest_game", "quest", "rpg"],
    temperature=0.75,
    max_tokens=2048,
)
