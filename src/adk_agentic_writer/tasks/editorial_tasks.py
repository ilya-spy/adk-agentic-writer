"""Editorial tasks: review, validate, refine."""

from ..models.agent_models import AgentRole, AgentTask

REVIEW_CONTENT = AgentTask(
    task_id="review_content",
    agent_role=AgentRole.REVIEWER,
    prompt="Review the following content and provide detailed feedback.\n\nContent: {content_draft}",
    output_key="feedback",
)

VALIDATE_CONTENT = AgentTask(
    task_id="validate_content",
    agent_role=AgentRole.REVIEWER,
    prompt="Validate that the following content meets quality standards.\n\nContent: {content_draft}",
    output_key="validation_result",
)

REFINE_CONTENT = AgentTask(
    task_id="refine_content",
    agent_role=AgentRole.REFINER,
    prompt="Refine the following content based on feedback.\n\nContent: {content_draft}\n\nFeedback: {feedback}",
    output_key="refined_content",
)
