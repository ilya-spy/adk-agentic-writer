"""Task definitions for EditorialProtocol methods."""

from ..models.agent_models import AgentRole, AgentTask

# Task: review_content
# Produces: feedback (used by refine_content)
REVIEW_CONTENT = AgentTask(
    task_id="review_content",
    agent_role=AgentRole.REVIEWER,
    prompt="""Review the following content and provide detailed feedback on quality, accuracy, and improvements needed.

Content: {content_draft}""",
    output_key="feedback",
)

# Task: validate_content
# Produces: validation_result
VALIDATE_CONTENT = AgentTask(
    task_id="validate_content",
    agent_role=AgentRole.REVIEWER,
    prompt="""Validate that the following content meets all requirements and quality standards.

Content: {content_draft}""",
    output_key="validation_result",
)

# Task: refine_content
# Consumes: content_draft, feedback
# Produces: refined_content
REFINE_CONTENT = AgentTask(
    task_id="refine_content",
    agent_role=AgentRole.REFINER,
    prompt="""Refine the following content based on the provided feedback.

Content: {content_draft}

Feedback: {feedback}""",
    output_key="refined_content",
)

# ============================================================================
# Tasks for SequentialEditorialWorkflow
# Pattern: Draft → Refine → Review → Finalize
# ============================================================================

# Task: review_draft
# Produces: review_feedback
REVIEW_DRAFT = AgentTask(
    task_id="review_draft",
    agent_role=AgentRole.REVIEWER,
    prompt="""Review the following draft content for clarity, accuracy, and quality.

Draft: {content_draft}""",
    output_key="review_feedback",
)

# Task: refine_based_on_review
# Consumes: content_draft, review_feedback
# Produces: refined_draft
REFINE_BASED_ON_REVIEW = AgentTask(
    task_id="refine_based_on_review",
    agent_role=AgentRole.REFINER,
    prompt="""Refine the following content based on the review feedback provided.

Content: {content_draft}

Review feedback: {review_feedback}""",
    output_key="refined_draft",
    dependencies=["review_draft"],
)

# Task: finalize_content
# Consumes: refined_draft
# Produces: final_content
FINALIZE_CONTENT = AgentTask(
    task_id="finalize_content",
    agent_role=AgentRole.EDITOR,
    prompt="""Finalize the following refined draft for publication, ensuring all standards are met.

Refined draft: {refined_draft}""",
    output_key="final_content",
    dependencies=["refine_based_on_review"],
)

# ============================================================================
# Tasks for ParallelEditorialWorkflow
# Pattern: [Variant 1, Variant 2, Variant 3] → Select Best
# ============================================================================

# Task: review_variant_quality
# Consumes: content_variants
# Produces: quality_scores
REVIEW_VARIANTS_QUALITY = AgentTask(
    task_id="review_variant_quality",
    agent_role=AgentRole.REVIEWER,
    prompt="""Review the following content variants and provide quality scores based on the specified criteria.

Content variants: {content_variants}
Criteria: {criteria}""",
    output_key="quality_scores",
)

# Task: select_best_variant
# Consumes: all quality_scores
# Produces: selected_content
SELECT_BEST_VARIANT = AgentTask(
    task_id="select_best_variant",
    agent_role=AgentRole.EDITOR,
    prompt="""Select the best content variant using the specified selection strategy.

Variants: {content_variants}
Quality scores: {quality_scores}
Selection strategy: {selection_strategy}""",
    output_key="selected_content",
    dependencies=["review_variant_quality"],
)

# ============================================================================
# Tasks for IterativeEditorialWorkflow
# Pattern: Generate → Validate → Refine → Validate → ... → Done
# ============================================================================

# Task: evaluate_content_quality
# Consumes: content_draft
# Produces: evaluation_result
EVALUATE_CONTENT_QUALITY = AgentTask(
    task_id="evaluate_content_quality",
    agent_role=AgentRole.REVIEWER,
    prompt="""Evaluate the following content against quality standards and provide detailed feedback.

Content: {content_draft}""",
    output_key="evaluation_result",
)

# Task: refine_iteratively
# Consumes: content_draft, evaluation_result
# Produces: refined_content
REFINE_ITERATIVELY = AgentTask(
    task_id="refine_iteratively",
    agent_role=AgentRole.REFINER,
    prompt="""Refine the following content to improve quality based on the evaluation results.

Content: {content_draft}

Evaluation: {evaluation_result}""",
    output_key="refined_content",
    dependencies=["evaluate_content_quality"],
)

# ============================================================================
# Tasks for AdaptiveEditorialWorkflow
# Pattern: Analyze Type → [Strategy A | Strategy B | Strategy C] → Edit
# ============================================================================

# Task: analyze_content_type
# Produces: content_type_analysis
ANALYZE_CONTENT_TYPE = AgentTask(
    task_id="analyze_content_type",
    agent_role=AgentRole.REVIEWER,
    prompt="""Analyze the following draft to determine its type, style, and appropriate editing strategy.

Draft: {content_draft}""",
    output_key="content_type_analysis",
)

# Task: select_editing_strategy
# Consumes: content_type_analysis
# Produces: editing_strategy
SELECT_EDITING_STRATEGY = AgentTask(
    task_id="select_editing_strategy",
    agent_role=AgentRole.EDITOR,
    prompt="""Select the most appropriate editing strategy from the available options based on the content analysis.

Available strategies: {available_strategies}

Content analysis: {content_type_analysis}""",
    output_key="editing_strategy",
    dependencies=["analyze_content_type"],
)

# Task: apply_adaptive_editing
# Consumes: content_draft, editing_strategy
# Produces: edited_content
APPLY_ADAPTIVE_EDITING = AgentTask(
    task_id="apply_adaptive_editing",
    agent_role=AgentRole.EDITOR,
    prompt="""Apply the specified editing strategy to edit the following draft according to content-specific best practices.

Editing strategy: {editing_strategy}

Draft: {content_draft}""",
    output_key="edited_content",
    dependencies=["select_editing_strategy"],
)
