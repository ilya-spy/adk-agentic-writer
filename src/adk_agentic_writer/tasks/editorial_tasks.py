"""Editorial tasks: review, refine, publish."""

from ..models.agent_models import AgentRole, AgentTask

REVIEW = AgentTask(
    task_id="review",
    agent_role=AgentRole.REVIEWER,
    prompt="Review the following content and provide detailed feedback",
    output_key="review_result",
    parameters={"format": "", "draft_content": ""},
)

REFINE = AgentTask(
    task_id="refine",
    agent_role=AgentRole.REFINER,
    prompt="Refine content based on review feedback",
    output_key="draft_content",
    parameters={"format": "", "draft_content": "", "review_result": ""},
)

PUBLISH = AgentTask(
    task_id="publish",
    agent_role=AgentRole.COORDINATOR,
    prompt="Full publish pipeline: ideate, write, review, refine",
    output_key="published_content",
    parameters={"formats": [], "prompt": ""},
)
