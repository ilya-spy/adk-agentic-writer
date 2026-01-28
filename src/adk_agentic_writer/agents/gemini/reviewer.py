"""Gemini-powered reviewer agent for content review and refinement.

Reviews and improves content using LLM-powered evaluation.
Inherits from StatefulAgent for unified structure.
ADK integration to be added later.
"""

import logging
from typing import Any, Dict, List

from ...models.agent_models import AgentTask
from ...teams.editorial_team import EDITORIAL_REVIEWER
from ..stateful_agent import StatefulAgent

logger = logging.getLogger(__name__)

# Review criteria (same as static for consistency)
REVIEW_CRITERIA = {
    "clarity": {"name": "Clarity", "weight": 1.0},
    "engagement": {"name": "Engagement", "weight": 1.0},
    "accuracy": {"name": "Accuracy", "weight": 1.2},
    "structure": {"name": "Structure", "weight": 0.8},
    "completeness": {"name": "Completeness", "weight": 1.0},
}


class GeminiReviewerAgent(StatefulAgent):
    """Gemini reviewer using LLM-powered evaluation.

    Same structure as ReviewerAgent but uses LLM for
    more nuanced content evaluation. ADK integration TBD.
    """

    def __init__(self, agent_id: str = "gemini_reviewer"):
        """Initialize Gemini reviewer.

        Args:
            agent_id: Unique agent identifier
        """
        super().__init__(agent_id=agent_id, config=EDITORIAL_REVIEWER)
        self._adk_agent = None  # To be initialized with ADK
        logger.info(f"Initialized GeminiReviewerAgent {agent_id}")

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute review task using LLM.

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
        """Review content using LLM evaluation.

        Currently uses fallback template-based evaluation.
        ADK integration to be added.

        Args:
            content: Content to review
            content_type: Type of content
            criteria: List of criteria to evaluate

        Returns:
            Review result with scores and feedback
        """
        logger.info(f"Reviewing {content_type} content with Gemini")

        # TODO: Implement ADK LLM-based review
        # For now, use fallback evaluation
        if self._adk_agent is None:
            return await self._fallback_review(content, content_type, criteria)

        # Future ADK implementation:
        # prompt = self._build_review_prompt(content, content_type, criteria)
        # result = await self._adk_agent.run(prompt)
        # return self._parse_review_result(result)

        return await self._fallback_review(content, content_type, criteria)

    async def _fallback_review(
        self, content: Dict[str, Any], content_type: str, criteria: List[str]
    ) -> Dict[str, Any]:
        """Fallback template-based review.

        Args:
            content: Content to review
            content_type: Type of content
            criteria: List of criteria

        Returns:
            Review result dictionary
        """
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
        """Evaluate content against a criterion.

        Args:
            content: Content to evaluate
            content_type: Type of content
            criterion: Criterion name

        Returns:
            Score from 0-100
        """
        base_score = 75.0

        if not content:
            return 50.0

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
            if len(content.get("variables", [])) >= 2:
                base_score += 5
            if len(content.get("controls", [])) >= 2:
                base_score += 5

        return min(base_score, 100.0)

    def _get_suggestion(self, criterion: str, content_type: str) -> str:
        """Get improvement suggestion.

        Args:
            criterion: Criterion needing improvement
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
        return suggestions.get(criterion, f"Review and improve {criterion}")

    def _build_review_prompt(
        self, content: Dict[str, Any], content_type: str, criteria: List[str]
    ) -> str:
        """Build LLM prompt for review (for future ADK integration).

        Args:
            content: Content to review
            content_type: Type of content
            criteria: Criteria to evaluate

        Returns:
            Prompt string
        """
        criteria_str = ", ".join(criteria)
        return f"""Review the following {content_type} content for: {criteria_str}

Content: {content}

Provide:
1. Score (0-100) for each criterion
2. Overall assessment
3. Specific suggestions for improvement

Return as JSON with keys: scores, overall_score, status, feedback, issues"""


__all__ = ["GeminiReviewerAgent"]
