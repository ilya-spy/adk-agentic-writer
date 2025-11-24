"""Editorial team configuration with reviewer and refiner roles."""

from enum import Enum

from ..models.agent_models import (
    AgentConfig,
    TeamMetadata,
    WorkflowScope,
)


class EditorialRole(str, Enum):
    """Editorial team specific roles (compatible with AgentRole)."""

    EDITORIAL_REVIEWER = "editorial_reviewer"
    EDITORIAL_REFINER = "editorial_refiner"


# Editorial Reviewer Configuration
EDITORIAL_REVIEWER = AgentConfig(
    role=EditorialRole.EDITORIAL_REVIEWER,
    system_instruction="""You are an expert content reviewer specializing in quality assurance.
Your role is to review content for quality, accuracy, and effectiveness.

Guidelines:
- Assess content quality, accuracy, and completeness
- Identify areas for improvement
- Provide specific, actionable feedback
- Check for pedagogical soundness
- Verify consistency and coherence
- Evaluate engagement and clarity
- Ensure content meets requirements and standards
- Provide constructive criticism with clear examples
- Focus on educational value and user experience""",
    temperature=0.5,
    max_tokens=1536,
)

# Editorial Refiner Configuration
EDITORIAL_REFINER = AgentConfig(
    role=EditorialRole.EDITORIAL_REFINER,
    system_instruction="""You are an expert content refiner specializing in improving content quality.
Your role is to enhance content based on feedback while maintaining original intent.

Guidelines:
- Improve clarity, coherence, and flow
- Enhance engagement and readability
- Ensure consistency in style and tone
- Fix grammatical and structural issues
- Maintain the original intent while improving expression
- Adapt improvements to the content type and audience
- Preserve educational value while enhancing presentation
- Address all feedback points systematically
- Ensure changes improve overall quality""",
    temperature=0.6,
    max_tokens=2048,
)

# Agent Pools

EDITORIAL_REVIEWERS_POOL = TeamMetadata(
    name="editorial_reviewers_pool",
    scope=WorkflowScope.EDITORIAL,
    description="Editorial review team specializing in content quality assurance and validation",
    roles=[
        EditorialRole.EDITORIAL_REVIEWER.value,
        EditorialRole.EDITORIAL_REVIEWER.value,
    ],  # Pool of 2
)

EDITORIAL_REFINERS_POOL = TeamMetadata(
    name="editorial_refiners_pool",
    scope=WorkflowScope.EDITORIAL,
    description="Editorial refinement team specializing in content improvement based on feedback",
    roles=[
        EditorialRole.EDITORIAL_REFINER.value,
        EditorialRole.EDITORIAL_REFINER.value,
    ],  # Pool of 2
)

EDITORIAL_GROUP_POOL = TeamMetadata(
    name="editorial_group_pool",
    scope=WorkflowScope.EDITORIAL,
    description="Editorial group team specializing in content review and refinement",
    roles=[
        EditorialRole.EDITORIAL_REVIEWER.value,
        EditorialRole.EDITORIAL_REFINER.value,
    ],  # Pool of 2
)
