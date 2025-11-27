"""Editor agent for editorial workflow orchestration.

This agent:
- Uses AdaptiveEditorialWorkflow and IterativeEditorialWorkflow
- Implements ANALYZE_CONTENT_TYPE, EVALUATE_CONTENT_QUALITY
- Implements REVIEW_VARIANTS_QUALITY, select_editing_strategy
- Provides edit_with_workflow for adaptive and iterative editing
"""

import logging
from typing import Any, Dict, List, Optional

from ...agents.stateful_agent import StatefulAgent
from ...models.agent_models import AgentTask
from ...teams.content_team import CONTENT_WRITER
from ...workflows.editorial_workflows import (
    AdaptiveEditorialWorkflow,
    IterativeEditorialWorkflow,
)

logger = logging.getLogger(__name__)


class EditorAgent(StatefulAgent):
    """Editor agent for editorial workflow orchestration.

    Implements:
    - AgentProtocol: process_task, update_status
    - ANALYZE_CONTENT_TYPE: Determine content type and appropriate editing strategy
    - EVALUATE_CONTENT_QUALITY: Assess content quality against standards
    - REVIEW_VARIANTS_QUALITY: Review multiple content variants
    - SELECT_EDITING_STRATEGY: Choose appropriate editing strategy
    - Uses ReviewerAgent for actual review/validation/refinement
    """

    def __init__(self, agent_id: str = "editor", reviewer=None):
        """Initialize editor agent.

        Args:
            agent_id: Agent identifier
            reviewer: Optional ReviewerAgent instance for delegation
        """
        super().__init__(
            agent_id=agent_id,
            config=CONTENT_WRITER,
        )
        self.reviewer = reviewer
        logger.info(f"Initialized EditorAgent {agent_id}")

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute task based on task_id."""
        context = self.prepare_task_context(task)

        # Delegate EditorialProtocol methods to reviewer if available
        if task.task_id in ["review_content", "validate_content", "refine_content"]:
            if self.reviewer:
                return await self.reviewer._execute_task(task, resolved_prompt)
            else:
                logger.warning(
                    f"No reviewer available for {task.task_id}, returning default"
                )
                return {"status": "no_reviewer_available"}

        # Handle Editor-specific tasks
        if task.task_id == "analyze_content_type":
            content_draft = context.get("content_draft", {})
            return await self.analyze_content_type(content_draft)
        elif task.task_id == "evaluate_content_quality":
            content_draft = context.get("content_draft", {})
            return await self.evaluate_content_quality(content_draft)
        elif task.task_id == "review_variant_quality":
            content_variants = context.get("content_variants", [])
            criteria = context.get("criteria", {})
            return await self.review_variants_quality(content_variants, criteria)
        elif task.task_id == "select_editing_strategy":
            content_type_analysis = context.get("content_type_analysis", {})
            available_strategies = context.get("available_strategies", [])
            return await self.select_editing_strategy(
                content_type_analysis, available_strategies
            )
        else:
            # Default: delegate to reviewer
            if self.reviewer:
                return await self.reviewer._execute_task(task, resolved_prompt)
            return {"status": "unknown_task"}

    # ========================================================================
    # Workflow-based Editing
    # ========================================================================

    async def edit_with_workflow(
        self, workflow_type: str, content: Dict[str, Any], **parameters
    ) -> Dict[str, Any]:
        """Edit content using specified workflow pattern.

        Args:
            workflow_type: "adaptive" or "iterative"
            content: Content to edit
            **parameters: Additional parameters for workflow

        Returns:
            Workflow execution result
        """
        logger.info(f"Editing with {workflow_type} workflow")

        if not self.reviewer:
            raise ValueError("Reviewer not set. Cannot execute editorial workflow.")

        # Create workflow based on type
        if workflow_type == "adaptive":
            workflow = AdaptiveEditorialWorkflow(
                name="adaptive_editing",
                type_analyzer=CONTENT_WRITER,
                generator=CONTENT_WRITER,
                strategies=parameters.get("strategies", {}),
                default_strategy=parameters.get("default_strategy", "standard"),
            )
        elif workflow_type == "iterative":
            max_iterations = parameters.get("max_iterations", 3)
            workflow = IterativeEditorialWorkflow(
                name="iterative_editing",
                generator=CONTENT_WRITER,
                evaluator=CONTENT_WRITER,
                refiner=CONTENT_WRITER,
                max_iterations=max_iterations,
            )
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

        # Prepare input data for workflow
        input_data = {
            "parameters": {
                "content_draft": content,
                **parameters,
            }
        }

        # Execute workflow
        result = await workflow.execute(input_data)

        return {
            "workflow_type": workflow_type,
            "result": result,
            "status": "completed",
        }

    async def edit_adaptive(
        self,
        content: Dict[str, Any],
        strategies: Optional[Dict[str, Any]] = None,
        **parameters,
    ) -> Dict[str, Any]:
        """Edit content using adaptive editorial workflow.

        Args:
            content: Content to edit
            strategies: Editing strategies for different content types
            **parameters: Additional parameters

        Returns:
            Adaptive editing result
        """
        return await self.edit_with_workflow(
            "adaptive", content, strategies=strategies or {}, **parameters
        )

    async def edit_iterative(
        self, content: Dict[str, Any], max_iterations: int = 3, **parameters
    ) -> Dict[str, Any]:
        """Edit content using iterative editorial workflow.

        Args:
            content: Content to edit
            max_iterations: Maximum number of refinement iterations
            **parameters: Additional parameters

        Returns:
            Iterative editing result
        """
        return await self.edit_with_workflow(
            "iterative", content, max_iterations=max_iterations, **parameters
        )

    # ========================================================================
    # Task-Specific Methods
    # ========================================================================

    async def analyze_content_type(
        self, content_draft: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content type and determine appropriate editing strategy.

        Implements ANALYZE_CONTENT_TYPE task.

        Args:
            content_draft: Draft content to analyze

        Returns:
            Content type analysis dictionary
        """
        logger.info("Analyzing content type")

        content_type = self._detect_content_type(content_draft)

        # Determine editing strategy
        strategy_map = {
            "quiz": "educational",
            "story": "narrative",
            "game": "interactive",
            "simulation": "technical",
            "general": "standard",
        }

        suggested_strategy = strategy_map.get(content_type, "standard")

        analysis = {
            "content_type": content_type,
            "suggested_strategy": suggested_strategy,
            "characteristics": self._identify_characteristics(
                content_draft, content_type
            ),
            "editing_focus": self._determine_editing_focus(content_type),
        }

        logger.info(f"Content type: {content_type}, strategy: {suggested_strategy}")
        return analysis

    async def evaluate_content_quality(
        self, content_draft: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate content quality against standards.

        Implements EVALUATE_CONTENT_QUALITY task.

        Args:
            content_draft: Draft content to evaluate

        Returns:
            Evaluation result dictionary
        """
        logger.info("Evaluating content quality")

        content_type = self._detect_content_type(content_draft)

        # Assess different quality dimensions
        completeness = self._assess_completeness(content_draft, content_type)
        clarity = self._assess_clarity(content_draft, content_type)
        consistency = self._assess_consistency(content_draft, content_type)
        engagement = self._assess_engagement(content_draft, content_type)

        overall_quality = (completeness + clarity + consistency + engagement) / 4

        # Determine if content meets quality threshold
        meets_standards = overall_quality >= 0.7

        evaluation = {
            "overall_quality": round(overall_quality, 2),
            "meets_standards": meets_standards,
            "scores": {
                "completeness": round(completeness, 2),
                "clarity": round(clarity, 2),
                "consistency": round(consistency, 2),
                "engagement": round(engagement, 2),
            },
            "content_type": content_type,
            "recommendations": self._generate_recommendations(
                completeness, clarity, consistency, engagement
            ),
        }

        logger.info(
            f"Quality evaluation: {overall_quality:.2f}, meets standards: {meets_standards}"
        )
        return evaluation

    async def review_variants_quality(
        self, content_variants: List[Dict[str, Any]], criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Review multiple content variants and provide quality scores.

        Implements REVIEW_VARIANTS_QUALITY task.

        Args:
            content_variants: List of content variants to review
            criteria: Review criteria

        Returns:
            Quality scores for each variant
        """
        logger.info(f"Reviewing {len(content_variants)} content variants")

        quality_scores = []

        for i, variant in enumerate(content_variants):
            # Evaluate each variant
            evaluation = await self.evaluate_content_quality(variant)

            quality_scores.append(
                {
                    "variant_index": i,
                    "overall_quality": evaluation["overall_quality"],
                    "scores": evaluation["scores"],
                    "meets_standards": evaluation["meets_standards"],
                }
            )

        # Identify best variant
        best_index = max(
            range(len(quality_scores)),
            key=lambda i: quality_scores[i]["overall_quality"],
        )

        return {
            "quality_scores": quality_scores,
            "best_variant_index": best_index,
            "best_variant_score": quality_scores[best_index]["overall_quality"],
            "num_variants_reviewed": len(content_variants),
        }

    async def select_editing_strategy(
        self,
        content_type_analysis: Dict[str, Any],
        available_strategies: List[str],
    ) -> Dict[str, Any]:
        """Select appropriate editing strategy based on content analysis.

        Implements SELECT_EDITING_STRATEGY task.

        Args:
            content_type_analysis: Analysis of content type
            available_strategies: List of available editing strategies

        Returns:
            Selected strategy dictionary
        """
        logger.info("Selecting editing strategy")

        content_type = content_type_analysis.get("content_type", "general")
        suggested_strategy = content_type_analysis.get("suggested_strategy", "standard")

        # Select strategy from available options
        if suggested_strategy in available_strategies:
            selected = suggested_strategy
        elif available_strategies:
            selected = available_strategies[0]
        else:
            selected = "standard"

        return {
            "editing_strategy": selected,
            "rationale": f"Selected {selected} based on {content_type} content type",
            "content_type": content_type,
        }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _detect_content_type(self, content: Dict[str, Any]) -> str:
        """Detect content type from structure."""
        if "questions" in content:
            return "quiz"
        elif "nodes" in content and "start_node" in content:
            if "victory_conditions" in content:
                return "game"
            else:
                return "story"
        elif "variables" in content and "controls" in content:
            return "simulation"
        return "general"

    def _assess_completeness(self, content: Dict[str, Any], content_type: str) -> float:
        """Assess content completeness."""
        if not content:
            return 0.0

        if content_type == "quiz":
            questions = content.get("questions", [])
            return min(len(questions) / 5.0, 1.0)  # Expect at least 5 questions
        elif content_type in ["story", "game"]:
            nodes = content.get("nodes", {})
            return min(len(nodes) / 5.0, 1.0)  # Expect at least 5 nodes
        elif content_type == "simulation":
            variables = content.get("variables", [])
            return min(len(variables) / 3.0, 1.0)  # Expect at least 3 variables

        return 0.8  # Default

    def _assess_clarity(self, content: Dict[str, Any], content_type: str) -> float:
        """Assess content clarity."""
        if not content:
            return 0.0

        # Check for required fields
        required_fields = {
            "quiz": ["title", "questions"],
            "story": ["title", "nodes", "start_node"],
            "game": ["title", "nodes", "start_node", "victory_conditions"],
            "simulation": ["title", "variables", "controls"],
        }

        fields = required_fields.get(content_type, ["title"])
        present = sum(1 for field in fields if field in content)

        return present / len(fields) if fields else 0.8

    def _assess_consistency(self, content: Dict[str, Any], content_type: str) -> float:
        """Assess content consistency."""
        # Simple heuristic: check if content structure is well-formed
        if not content:
            return 0.0

        return 0.85  # Default good score

    def _assess_engagement(self, content: Dict[str, Any], content_type: str) -> float:
        """Assess content engagement potential."""
        if not content:
            return 0.0

        if content_type == "quiz":
            questions = content.get("questions", [])
            has_explanations = all(q.get("explanation") for q in questions)
            return 0.9 if has_explanations else 0.7
        elif content_type in ["story", "game"]:
            nodes = content.get("nodes", {})
            has_branches = any(
                len(node.get("branches", [])) > 1 or len(node.get("choices", [])) > 1
                for node in nodes.values()
            )
            return 0.9 if has_branches else 0.7

        return 0.8  # Default

    def _identify_characteristics(
        self, content: Dict[str, Any], content_type: str
    ) -> List[str]:
        """Identify content characteristics."""
        characteristics = [content_type]

        if content_type == "quiz":
            if content.get("time_limit"):
                characteristics.append("timed")
        elif content_type in ["story", "game"]:
            nodes = content.get("nodes", {})
            if len(nodes) > 10:
                characteristics.append("complex")
            else:
                characteristics.append("simple")

        return characteristics

    def _determine_editing_focus(self, content_type: str) -> List[str]:
        """Determine appropriate editing focus for content type."""
        focus_map = {
            "quiz": ["accuracy", "clarity", "pedagogical_value"],
            "story": ["narrative_flow", "character_consistency", "engagement"],
            "game": ["balance", "progression", "reward_structure"],
            "simulation": ["accuracy", "usability", "educational_value"],
            "general": ["clarity", "completeness", "consistency"],
        }

        return focus_map.get(content_type, ["clarity", "completeness"])

    def _generate_recommendations(
        self, completeness: float, clarity: float, consistency: float, engagement: float
    ) -> List[str]:
        """Generate recommendations based on quality scores."""
        recommendations = []

        if completeness < 0.7:
            recommendations.append(
                "Expand content to provide more comprehensive coverage"
            )
        if clarity < 0.7:
            recommendations.append("Improve clarity and readability")
        if consistency < 0.7:
            recommendations.append("Ensure consistency in terminology and style")
        if engagement < 0.7:
            recommendations.append("Add more interactive or engaging elements")

        if not recommendations:
            recommendations.append("Content meets quality standards")

        return recommendations


__all__ = ["EditorAgent"]
