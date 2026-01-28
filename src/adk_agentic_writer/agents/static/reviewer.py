"""Static reviewer agent for content review and refinement.

Reviews and improves content using template-based evaluation.
Inherits from StatefulAgent for unified structure.
"""

import logging
from typing import Any, Dict, List

from ...models.agent_models import AgentTask
from ...teams.editorial_team import EDITORIAL_REVIEWER
from ..stateful_agent import StatefulAgent

logger = logging.getLogger(__name__)

# Review criteria with scoring guidelines
REVIEW_CRITERIA = {
    "clarity": {
        "name": "Clarity",
        "description": "Content is easy to understand",
        "weight": 1.0,
    },
    "engagement": {
        "name": "Engagement",
        "description": "Content is interesting and compelling",
        "weight": 1.0,
    },
    "accuracy": {
        "name": "Accuracy",
        "description": "Information is factually correct",
        "weight": 1.2,
    },
    "structure": {
        "name": "Structure",
        "description": "Content is well-organized",
        "weight": 0.8,
    },
    "completeness": {
        "name": "Completeness",
        "description": "Content covers all necessary points",
        "weight": 1.0,
    },
}


class ReviewerAgent(StatefulAgent):
    """Static reviewer using template-based evaluation.

    Provides:
    - Multi-criteria content review
    - Quality scoring and metrics
    - Actionable feedback generation
    """

    def __init__(self, agent_id: str = "reviewer"):
        """Initialize static reviewer.

        Args:
            agent_id: Unique agent identifier
        """
        super().__init__(agent_id=agent_id, config=EDITORIAL_REVIEWER)
        logger.info(f"Initialized ReviewerAgent {agent_id}")

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute review task.

        Args:
            task: Task to execute
            resolved_prompt: Resolved prompt string

        Returns:
            Review result dictionary
        """
        context = self.prepare_task_context(task)
        content = context.get("content", {})
        content_type = context.get("content_type", "general")
        criteria = context.get("criteria", list(REVIEW_CRITERIA.keys()))

        return await self._review_content(content, content_type, criteria)

    async def _review_content(
        self, content: Dict[str, Any], content_type: str, criteria: List[str]
    ) -> Dict[str, Any]:
        """Review content against criteria.

        Args:
            content: Content to review
            content_type: Type of content
            criteria: List of criteria to evaluate

        Returns:
            Review result with scores and feedback
        """
        logger.info(f"Reviewing {content_type} content")

        scores = {}
        feedback = []
        issues = []

        for criterion in criteria:
            if criterion not in REVIEW_CRITERIA:
                continue

            score = self._evaluate_criterion(content, content_type, criterion)
            scores[criterion] = score

            if score < 70:
                issues.append(
                    {
                        "criterion": criterion,
                        "score": score,
                        "suggestion": self._get_suggestion(criterion, content_type),
                    }
                )

            feedback.append(
                {
                    "criterion": REVIEW_CRITERIA[criterion]["name"],
                    "score": score,
                    "status": "pass" if score >= 70 else "needs_improvement",
                }
            )

        # Calculate weighted overall score
        total_weight = sum(
            REVIEW_CRITERIA[c]["weight"] for c in criteria if c in REVIEW_CRITERIA
        )
        overall_score = (
            sum(
                scores.get(c, 0) * REVIEW_CRITERIA[c]["weight"]
                for c in criteria
                if c in REVIEW_CRITERIA
            )
            / total_weight
            if total_weight > 0
            else 0
        )

        return {
            "content_type": content_type,
            "overall_score": round(overall_score, 1),
            "status": "approved" if overall_score >= 75 else "needs_revision",
            "scores": scores,
            "feedback": feedback,
            "issues": issues,
            "quality_metrics": {
                "overall_score": round(overall_score, 1),
                "clarity_score": scores.get("clarity", 0),
                "engagement_score": scores.get("engagement", 0),
                "accuracy_score": scores.get("accuracy", 0),
            },
        }

    def _evaluate_criterion(
        self, content: Dict[str, Any], content_type: str, criterion: str
    ) -> float:
        """Evaluate content against a single criterion.

        Args:
            content: Content to evaluate
            content_type: Type of content
            criterion: Criterion to evaluate

        Returns:
            Score from 0-100
        """
        # Base score
        base_score = 75.0

        # Adjust based on content presence
        if not content:
            return 50.0

        # Check for key content fields
        has_title = bool(content.get("title"))
        has_description = bool(content.get("description"))
        has_content = len(content) > 2

        if has_title:
            base_score += 5
        if has_description:
            base_score += 5
        if has_content:
            base_score += 5

        # Content-type specific checks
        if content_type == "quiz":
            questions = content.get("questions", [])
            if len(questions) >= 5:
                base_score += 5
            if all(q.get("explanation") for q in questions):
                base_score += 5

        elif content_type == "story":
            nodes = content.get("nodes", {})
            if len(nodes) >= 5:
                base_score += 5
            if any(n.get("is_ending") for n in nodes.values()):
                base_score += 5

        elif content_type == "game":
            quests = content.get("quests", [])
            if len(quests) >= 2:
                base_score += 5
            if content.get("victory_condition"):
                base_score += 5

        elif content_type == "simulation":
            variables = content.get("variables", [])
            controls = content.get("controls", [])
            if len(variables) >= 2:
                base_score += 5
            if len(controls) >= 2:
                base_score += 5

        return min(base_score, 100.0)

    def _get_suggestion(self, criterion: str, content_type: str) -> str:
        """Get improvement suggestion for a criterion.

        Args:
            criterion: The criterion that needs improvement
            content_type: Type of content

        Returns:
            Suggestion string
        """
        suggestions = {
            "clarity": f"Consider simplifying the language in your {content_type}",
            "engagement": f"Add more interactive elements to your {content_type}",
            "accuracy": f"Verify all facts and information in your {content_type}",
            "structure": f"Improve the organization of your {content_type}",
            "completeness": f"Add more content to cover all aspects of the topic",
        }
        return suggestions.get(
            criterion, f"Review and improve the {criterion} of your content"
        )


__all__ = ["ReviewerAgent"]
