"""Task definitions for EditorialProtocol methods."""

from ..models.agent_models import AgentRole, AgentTask

# Task: review_content
# Produces: feedback (used by refine_content)
REVIEW_CONTENT = AgentTask(
    task_id="review_content",
    agent_role=AgentRole.REVIEWER,
    prompt="Review the {content_draft} and provide detailed feedback on quality, accuracy, and improvements needed",
    suggested_workflow="content_review",
    suggested_team="editorial_team",
    output_key="feedback",
)

# Task: validate_content
# Produces: validation_result
VALIDATE_CONTENT = AgentTask(
    task_id="validate_content",
    agent_role=AgentRole.REVIEWER,
    prompt="Validate that the {content_draft} meets all requirements and quality standards",
    suggested_workflow="content_validation",
    suggested_team="editorial_team",
    output_key="validation_result",
)

# Task: refine_content
# Consumes: content_draft, feedback
# Produces: refined_content
REFINE_CONTENT = AgentTask(
    task_id="refine_content",
    agent_role=AgentRole.REFINER,
    prompt="Refine this content based on the feedback provided.\n\nContent: {content_draft}\n\nFeedback: {feedback}",
    suggested_workflow="content_refinement",
    suggested_team="editorial_team",
    output_key="refined_content",
)
