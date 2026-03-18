"""Primary content generation tasks.

Each task includes content_types (aliases) for discovery.
Agents import tasks and publish via get_supported_tasks().
"""

from ..models.agent_models import AgentRole, AgentTask

GENERATE_QUIZ = AgentTask(
    task_id="generate_quiz",
    agent_role=AgentRole.WRITER,
    prompt="Generate a quiz about {topic} with {num_questions} questions.",
    parameters={"topic": "", "num_questions": 5, "difficulty": "medium"},
    content_types=["quiz", "trivia", "test"],
    output_key="content",
)

GENERATE_STORY = AgentTask(
    task_id="generate_story",
    agent_role=AgentRole.WRITER,
    prompt="Generate a branched narrative about {topic} with {num_nodes} nodes.",
    parameters={"topic": "", "num_nodes": 7, "genre": "fantasy"},
    content_types=["story", "narrative", "branched_narrative", "adventure"],
    output_key="content",
)

GENERATE_GAME = AgentTask(
    task_id="generate_game",
    agent_role=AgentRole.DESIGNER,
    prompt="Generate a quest game about {topic} with {num_nodes} nodes.",
    parameters={"topic": "", "num_nodes": 5, "complexity": "medium"},
    content_types=["game", "quest_game", "quest", "rpg"],
    output_key="content",
)

GENERATE_SIMULATION = AgentTask(
    task_id="generate_simulation",
    agent_role=AgentRole.DESIGNER,
    prompt="Generate an interactive simulation about {topic}.",
    parameters={"topic": "", "complexity": "medium"},
    content_types=["simulation", "web_simulation", "interactive", "simulator"],
    output_key="content",
)

PRIMARY_TASKS = [GENERATE_QUIZ, GENERATE_STORY, GENERATE_GAME, GENERATE_SIMULATION]
