"""Data models for editorial operations (content editing and refinement).

This module defines models for editorial workflows, feedback, revisions,
and content quality metrics.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EditorialAction(str, Enum):
    """Types of editorial actions that can be performed."""

    VALIDATE = "validate"
    REFINE = "refine"
    REVIEW = "review"
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


class FeedbackType(str, Enum):
    """Types of feedback that can be provided."""

    GRAMMAR = "grammar"
    CLARITY = "clarity"
    ACCURACY = "accuracy"
    STRUCTURE = "structure"
    TONE = "tone"
    ENGAGEMENT = "engagement"
    GENERAL = "general"


class Feedback(BaseModel):
    """Feedback on content for refinement."""

    feedback_id: str = Field(..., description="Unique feedback identifier")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    content: str = Field(..., description="Feedback content/message")
    severity: str = Field("medium", description="Severity: low, medium, high, critical")
    location: Optional[str] = Field(
        None, description="Location in content (e.g., 'question 3')"
    )
    suggested_fix: Optional[str] = Field(None, description="Suggested correction")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str = Field(..., description="Agent or user who created the feedback")


class ContentRevision(BaseModel):
    """A revision of content with tracking information."""

    revision_id: str = Field(..., description="Unique revision identifier")
    version: int = Field(..., description="Version number")
    content: Dict[str, Any] = Field(..., description="Content at this revision")
    changes_made: List[str] = Field(
        default_factory=list, description="List of changes made"
    )
    feedback_addressed: List[str] = Field(
        default_factory=list, description="Feedback IDs addressed in this revision"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str = Field(..., description="Agent that created this revision")
    notes: Optional[str] = Field(
        None, description="Additional notes about this revision"
    )


class QualityMetrics(BaseModel):
    """Quality metrics for content evaluation."""

    overall_score: float = Field(
        ..., ge=0, le=100, description="Overall quality score (0-100)"
    )
    grammar_score: Optional[float] = Field(
        None, ge=0, le=100, description="Grammar quality"
    )
    clarity_score: Optional[float] = Field(
        None, ge=0, le=100, description="Clarity score"
    )
    accuracy_score: Optional[float] = Field(
        None, ge=0, le=100, description="Accuracy score"
    )
    engagement_score: Optional[float] = Field(
        None, ge=0, le=100, description="Engagement score"
    )
    completeness_score: Optional[float] = Field(
        None, ge=0, le=100, description="Completeness score"
    )
    issues_found: List[str] = Field(
        default_factory=list, description="List of issues found"
    )
    strengths: List[str] = Field(default_factory=list, description="Content strengths")
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    evaluated_by: str = Field(..., description="Agent that performed evaluation")


class EditorialRequest(BaseModel):
    """Request for editorial action on content."""

    request_id: str = Field(..., description="Unique request identifier")
    action: EditorialAction = Field(..., description="Editorial action to perform")
    content: Dict[str, Any] = Field(..., description="Content to work on")
    feedback: Optional[List[Feedback]] = Field(None, description="Feedback to address")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Additional parameters for the action"
    )
    requested_by: str = Field(..., description="Agent or user making the request")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EditorialResponse(BaseModel):
    """Response from an editorial action."""

    request_id: str = Field(..., description="Original request identifier")
    action: EditorialAction = Field(..., description="Action that was performed")
    status: str = Field(..., description="Status: completed, failed, partial")
    original_content: Dict[str, Any] = Field(..., description="Original content")
    refined_content: Optional[Dict[str, Any]] = Field(
        None, description="Refined content (if applicable)"
    )
    feedback: List[Feedback] = Field(
        default_factory=list, description="Feedback generated"
    )
    quality_metrics: Optional[QualityMetrics] = Field(
        None, description="Quality metrics"
    )
    changes_made: List[str] = Field(
        default_factory=list, description="List of changes made"
    )
    approved: Optional[bool] = Field(None, description="Whether content was approved")
    completed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_by: str = Field(..., description="Agent that completed the action")
    notes: Optional[str] = Field(None, description="Additional notes")


class ValidationResult(BaseModel):
    """Result of content validation."""

    is_valid: bool = Field(..., description="Whether content passed validation")
    validation_score: float = Field(
        ..., ge=0, le=100, description="Validation score (0-100)"
    )
    errors: List[str] = Field(
        default_factory=list, description="Validation errors found"
    )
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    suggestions: List[str] = Field(
        default_factory=list, description="Suggestions for improvement"
    )
    validated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    validated_by: str = Field(..., description="Agent that performed validation")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional validation details"
    )


class EditorialWorkflow(BaseModel):
    """Editorial workflow tracking for content generation and refinement."""

    workflow_id: str = Field(..., description="Unique workflow identifier")
    content_id: str = Field(..., description="ID of content being worked on")
    status: str = Field("in_progress", description="Workflow status")
    current_version: int = Field(1, description="Current version number")
    revisions: List[ContentRevision] = Field(
        default_factory=list, description="List of content revisions"
    )
    feedback_history: List[Feedback] = Field(
        default_factory=list, description="All feedback received"
    )
    quality_history: List[QualityMetrics] = Field(
        default_factory=list, description="Quality metrics over time"
    )
    agents_involved: List[str] = Field(
        default_factory=list, description="Agents that worked on this content"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = Field(
        None, description="When workflow completed"
    )


class RefinementContext(BaseModel):
    """Context for content refinement operations."""

    target_audience: Optional[str] = Field(
        None, description="Target audience for the content"
    )
    tone: Optional[str] = Field(
        None, description="Desired tone (e.g., formal, casual, educational)"
    )
    style_guide: Optional[str] = Field(None, description="Style guide to follow")
    constraints: List[str] = Field(
        default_factory=list, description="Constraints to respect"
    )
    goals: List[str] = Field(default_factory=list, description="Refinement goals")
    preserve_elements: List[str] = Field(
        default_factory=list, description="Elements that must be preserved"
    )
    focus_areas: List[FeedbackType] = Field(
        default_factory=list, description="Areas to focus refinement on"
    )
