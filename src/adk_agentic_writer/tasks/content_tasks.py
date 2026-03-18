"""Unified content tasks.

Two core tasks: IDEATE for brainstorming, WRITE for content generation.
Both accept format/flavor/topic parameters and use output_key for state passing.
"""

from ..models.agent_models import AgentRole, AgentTask

IDEATE = AgentTask(
    task_id="ideate",
    agent_role=AgentRole.STRATEGIST,
    prompt="Analyze prompt and select optimal format and parameters",
    output_key="ideation_result",
    parameters={"prompt": "", "formats": []},
)

WRITE = AgentTask(
    task_id="write",
    agent_role=AgentRole.WRITER,
    prompt="Write {flavor} about {topic}",
    output_key="draft_content",
    parameters={"format": "", "flavor": "", "topic": ""},
)
