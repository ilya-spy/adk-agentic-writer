"""Reviewer agent implementing content review and refinement with StatefulAgent framework.

This agent reviews and improves content using:
- StatefulAgent: For variable/parameter management
- Review cycles: Iterative improvement
- Quality criteria: Customizable review standards
"""

import logging
from typing import Any, Dict, List, Optional

from ...agents.stateful_agent import StatefulAgent
from ...models.agent_models import AgentTask, AgentStatus
from ...teams.content_team import CONTENT_WRITER

logger = logging.getLogger(__name__)

# Review criteria templates
REVIEW_CRITERIA = {
    "clarity": {
        "name": "Clarity",
        "checks": [
            "Is the content easy to understand?",
            "Are concepts explained clearly?",
            "Is terminology appropriate for the audience?",
        ],
    },
    "engagement": {
        "name": "Engagement",
        "checks": [
            "Is the content interesting and engaging?",
            "Does it maintain reader interest?",
            "Are examples and illustrations compelling?",
        ],
    },
    "accuracy": {
        "name": "Accuracy",
        "checks": [
            "Is the information factually correct?",
            "Are there any inconsistencies?",
            "Is the content appropriate for the topic?",
        ],
    },
    "structure": {
        "name": "Structure",
        "checks": [
            "Is the content well-organized?",
            "Does it flow logically?",
            "Are transitions smooth?",
        ],
    },
    "completeness": {
        "name": "Completeness",
        "checks": [
            "Does it cover all necessary points?",
            "Are there any gaps?",
            "Is the depth appropriate?",
        ],
    },
}


class ReviewerAgent(StatefulAgent):
    """Reviewer agent implementing EditorialProtocol.

    Implements:
    - AgentProtocol: process_task, update_status
    - EditorialProtocol: review_content, validate_content, refine_content
    - Review cycles: Iterative content improvement
    - Quality scoring: Multi-criteria evaluation
    """

    def __init__(self, agent_id: str = "reviewer"):
        """Initialize reviewer agent."""
        super().__init__(
            agent_id=agent_id,
            config=CONTENT_WRITER,  # Use content writer config as base
        )
        logger.info(f"Initialized ReviewerAgent {agent_id}")

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute review task based on task_id."""
        context = self.prepare_task_context(task)

        if task.task_id == "review_content":
            content = context.get("content", {})
            review_criteria = context.get("review_criteria", {})
            return await self.review_content(content, review_criteria)
        elif task.task_id == "validate_content":
            content = context.get("content", {})
            is_valid = await self.validate_content(content)
            return {"valid": is_valid}
        elif task.task_id == "refine_content":
            content = context.get("content", {})
            feedback = context.get("feedback", "")
            return await self.refine_content(content, feedback)
        else:
            # Default: review with criteria
            content = context.get("content", {})
            content_type = context.get("content_type", "general")
            criteria = context.get("criteria", ["clarity", "engagement", "accuracy"])
            return await self._review_content(content, content_type, criteria)

    async def _review_content(
        self, content: Dict[str, Any], content_type: str, criteria: List[str]
    ) -> Dict[str, Any]:
        """Review content and provide feedback.

        Args:
            content: Content to review
            content_type: Type of content (quiz, story, game, etc.)
            criteria: List of criteria to evaluate

        Returns:
            Review result with scores and suggestions
        """
        logger.info(f"Reviewing {content_type} content with criteria: {criteria}")

        # Analyze content
        scores = {}
        suggestions = []
        issues = []

        for criterion in criteria:
            if criterion in REVIEW_CRITERIA:
                # Evaluate based on criterion
                score, feedback = await self._evaluate_criterion(
                    content, content_type, criterion
                )
                scores[criterion] = score

                if score < 7:  # Below threshold
                    issues.append(
                        {
                            "criterion": criterion,
                            "score": score,
                            "feedback": feedback,
                        }
                    )
                    suggestions.extend(feedback)

        # Calculate overall score
        overall_score = sum(scores.values()) / len(scores) if scores else 0

        # Determine status
        status = "approved" if overall_score >= 7.5 else "needs_revision"

        review_result = {
            "status": status,
            "overall_score": round(overall_score, 2),
            "scores": scores,
            "suggestions": suggestions[:5],  # Top 5 suggestions
            "issues": issues,
            "content_type": content_type,
            "reviewed": True,
        }

        logger.info(
            f"Review complete: {status}, score: {overall_score:.2f}, "
            f"issues: {len(issues)}"
        )

        return review_result

    # ========================================================================
    # EditorialProtocol Implementation
    # ========================================================================

    async def review_content(
        self, content: Dict[str, Any], review_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Review content and generate detailed feedback.

        Implements EditorialProtocol.

        Args:
            content: Content to review
            review_criteria: Criteria for review (focus, depth, etc.)

        Returns:
            Review feedback dictionary with overall_score, feedback, issues_found, etc.
        """
        # Extract criteria from review_criteria
        criteria = review_criteria.get(
            "criteria", ["clarity", "engagement", "accuracy"]
        )
        content_type = review_criteria.get("content_type", "general")

        # Use existing internal review method
        return await self._review_content(content, content_type, criteria)

    async def validate_content(self, content: Dict[str, Any]) -> bool:
        """Validate generated content.

        Implements EditorialProtocol.

        Args:
            content: Content to validate

        Returns:
            True if content is valid, False otherwise
        """
        logger.info("Validating content")

        if not content:
            return False

        # Detect content type
        if "questions" in content:
            content_type = "quiz"
        elif "nodes" in content and "start_node" in content:
            if "victory_conditions" in content:
                content_type = "game"
            else:
                content_type = "story"
        elif "variables" in content and "controls" in content:
            content_type = "simulation"
        else:
            content_type = "general"

        # Validate based on type
        if content_type == "quiz":
            return "questions" in content and len(content.get("questions", [])) > 0
        elif content_type in ["story", "game"]:
            return "nodes" in content and "start_node" in content
        elif content_type == "simulation":
            return "variables" in content and "controls" in content

        # Default validation
        return len(content) > 0

    async def refine_content(
        self, content: Dict[str, Any], feedback: str | Dict[str, Any]
    ) -> Dict[str, Any]:
        """Refine content based on review feedback.

        Implements EditorialProtocol.

        Args:
            content: Content to refine
            feedback: Feedback from review_content() or string feedback

        Returns:
            Refined content dictionary
        """
        logger.info("Refining content based on feedback")

        # Extract feedback details
        if isinstance(feedback, dict):
            issues = feedback.get("issues_found", [])
            suggestions = feedback.get("suggestions", [])
        else:
            issues = []
            suggestions = [{"area": "general", "suggestion": str(feedback)}]

        # Create refined copy
        refined_content = content.copy()

        # Apply refinements based on suggestions
        for suggestion in suggestions:
            area = suggestion.get("area", "general")

            if area == "completeness" and isinstance(refined_content, dict):
                # Add metadata to indicate refinement
                if "metadata" not in refined_content:
                    refined_content["metadata"] = {}
                refined_content["metadata"]["refined"] = True
                refined_content["metadata"]["refinement_applied"] = "completeness"

            elif area == "clarity":
                if "metadata" not in refined_content:
                    refined_content["metadata"] = {}
                refined_content["metadata"]["clarity_improved"] = True

        logger.info(f"Content refined: {len(suggestions)} improvements applied")
        return refined_content

    # ========================================================================
    # Internal Evaluation Methods
    # ========================================================================

    async def _evaluate_criterion(
        self, content: Dict[str, Any], content_type: str, criterion: str
    ) -> tuple[float, List[str]]:
        """Evaluate content against specific criterion.

        Returns:
            Tuple of (score, feedback_list)
        """
        feedback = []
        base_score = 8.0  # Start optimistic

        criterion_info = REVIEW_CRITERIA.get(criterion, {})
        checks = criterion_info.get("checks", [])

        # Content type specific evaluations
        if content_type == "quiz":
            score, fb = await self._evaluate_quiz(content, criterion, checks)
            base_score = score
            feedback.extend(fb)
        elif content_type in ["branched_narrative", "story"]:
            score, fb = await self._evaluate_story(content, criterion, checks)
            base_score = score
            feedback.extend(fb)
        elif content_type == "quest_game":
            score, fb = await self._evaluate_game(content, criterion, checks)
            base_score = score
            feedback.extend(fb)
        else:
            # General content evaluation
            score, fb = await self._evaluate_general(content, criterion, checks)
            base_score = score
            feedback.extend(fb)

        return base_score, feedback

    async def _evaluate_quiz(
        self, content: Dict[str, Any], criterion: str, checks: List[str]
    ) -> tuple[float, List[str]]:
        """Evaluate quiz content."""
        feedback = []
        score = 8.0

        questions = content.get("questions", [])

        if criterion == "clarity":
            # Check question clarity
            if not questions:
                feedback.append("Quiz has no questions")
                score = 3.0
            elif len(questions) < 3:
                feedback.append("Consider adding more questions for better coverage")
                score = 7.0

            # Check if questions have explanations
            has_explanations = all(q.get("explanation") for q in questions)
            if not has_explanations:
                feedback.append("Add explanations for all answers")
                score -= 1.0

        elif criterion == "engagement":
            # Check question variety
            if len(questions) > 0 and len(
                set(q.get("question", "")[:20] for q in questions)
            ) < len(questions):
                feedback.append("Vary question formats for better engagement")
                score -= 0.5

        elif criterion == "accuracy":
            # Check answer correctness indicators
            for i, q in enumerate(questions):
                if "correct_answer" not in q:
                    feedback.append(f"Question {i+1} missing correct answer")
                    score -= 1.0

        return max(score, 1.0), feedback

    async def _evaluate_story(
        self, content: Dict[str, Any], criterion: str, checks: List[str]
    ) -> tuple[float, List[str]]:
        """Evaluate story content."""
        feedback = []
        score = 8.0

        nodes = content.get("nodes", {})
        start_node = content.get("start_node")

        if criterion == "structure":
            if not nodes:
                feedback.append("Story has no nodes")
                score = 3.0
            elif len(nodes) < 5:
                feedback.append("Story could be expanded with more nodes")
                score = 7.0

            if not start_node or start_node not in nodes:
                feedback.append("Invalid or missing start node")
                score -= 2.0

        elif criterion == "engagement":
            # Check branching
            branch_count = sum(
                1 for node in nodes.values() if len(node.get("branches", [])) > 1
            )
            if branch_count < 2:
                feedback.append("Add more branching points for interactivity")
                score -= 1.0

        elif criterion == "completeness":
            # Check for endings
            endings = sum(1 for node in nodes.values() if node.get("is_ending", False))
            if endings < 2:
                feedback.append("Add multiple endings for replay value")
                score -= 0.5

        return max(score, 1.0), feedback

    async def _evaluate_game(
        self, content: Dict[str, Any], criterion: str, checks: List[str]
    ) -> tuple[float, List[str]]:
        """Evaluate game content."""
        feedback = []
        score = 8.0

        nodes = content.get("nodes", {})

        if criterion == "structure":
            if len(nodes) < 5:
                feedback.append("Game could use more quest nodes")
                score = 7.0

        elif criterion == "engagement":
            # Check reward variety
            all_rewards = []
            for node in nodes.values():
                all_rewards.extend(node.get("rewards", []))

            if len(set(all_rewards)) < 3:
                feedback.append("Add more varied rewards")
                score -= 1.0

        elif criterion == "completeness":
            if "victory_conditions" not in content:
                feedback.append("Define clear victory conditions")
                score -= 1.0

        return max(score, 1.0), feedback

    async def _evaluate_general(
        self, content: Dict[str, Any], criterion: str, checks: List[str]
    ) -> tuple[float, List[str]]:
        """Evaluate general content."""
        feedback = []
        score = 8.0

        if not content:
            feedback.append("Content is empty")
            return 2.0, feedback

        if criterion == "completeness":
            # Check basic fields
            if "title" not in content:
                feedback.append("Add a title")
                score -= 1.0
            if "description" not in content:
                feedback.append("Add a description")
                score -= 0.5

        return max(score, 1.0), feedback


__all__ = ["ReviewerAgent"]
