"""Editorial workflow patterns and predefined instances.

These workflows implement patterns for editing, validating, and refining content.
They correspond to the EditorialProtocol.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from ..models.agent_models import WorkflowPattern, WorkflowScope
from .base_workflow import Workflow

logger = logging.getLogger(__name__)


class SequentialEditorialWorkflow(Workflow):
    """
    Sequential editorial workflow - edits content in stages.

    Pattern: Draft → Refine → Review → Finalize
    Each stage builds upon the previous stage's output.

    Corresponds to EditorialProtocol operations.
    """

    def __init__(self, name: str, stages: List[Any]):
        """
        Initialize sequential editorial workflow.

        Args:
            name: Workflow name
            stages: List of editorial stages (generate, validate, refine)
        """
        super().__init__(
            name=name,
            pattern=WorkflowPattern.SEQUENTIAL,
            scope=WorkflowScope.EDITORIAL,
            description="Review → Refine → Validate in sequence",
            agents=stages,
            parameters={"steps": ["review", "refine", "validate"]},
        )
        logger.info(
            f"Sequential editorial workflow '{name}' configured with {len(stages)} stages"
        )


class ParallelEditorialWorkflow(Workflow):
    """
    Parallel editorial workflow - generates multiple content variants concurrently.

    Pattern: [Variant 1, Variant 2, Variant 3] → Select Best
    All variants are generated simultaneously and the best is selected.

    Corresponds to EditorialProtocol operations.
    """

    def __init__(
        self, name: str, generators: List[Any], selection_strategy: str = "first"
    ):
        """
        Initialize parallel editorial workflow.

        Args:
            name: Workflow name
            generators: List of content generators to execute in parallel
            selection_strategy: How to select best - 'first', 'vote', 'quality_score'
        """
        super().__init__(
            name=name,
            pattern=WorkflowPattern.PARALLEL,
            scope=WorkflowScope.EDITORIAL,
            description="Multiple reviewers provide feedback concurrently",
            agents=generators,
            merge_strategy=selection_strategy,
            parameters={"consensus_strategy": "majority_vote"},
        )
        self.selection_strategy = selection_strategy
        logger.info(
            f"Parallel editorial workflow '{name}' configured with {len(generators)} generators"
        )


class IterativeEditorialWorkflow(Workflow):
    """
    Iterative editorial workflow - refines content through multiple iterations.

    Pattern: Generate → Validate → Refine → Validate → ... → Done
    Useful for achieving high-quality content through iterative improvement.

    Corresponds to EditorialProtocol operations (generate, validate, refine).
    """

    def __init__(
        self,
        name: str,
        generator: Any,
        evaluator: Any,
        max_iterations: int = 5,
    ):
        """
        Initialize iterative editorial workflow.

        Args:
            name: Workflow name
            generator: Content generator (implements generate_content)
            evaluator: Content evaluator (implements validate_content)
            max_iterations: Maximum number of iterations
        """
        condition_fn = lambda data, iteration: iteration < max_iterations

        super().__init__(
            name=name,
            pattern=WorkflowPattern.LOOP,
            scope=WorkflowScope.EDITORIAL,
            description="Review and refine content iteratively until quality met",
            agents=[generator],
            condition=condition_fn,
            max_iterations=max_iterations,
            parameters={"quality_threshold": 80.0, "exit_on_quality": True},
        )
        self.evaluator = evaluator
        logger.info(
            f"Iterative editorial workflow '{name}' configured with max {max_iterations} iterations"
        )


class AdaptiveEditorialWorkflow(Workflow):
    """
    Adaptive editorial workflow - adapts editing strategy based on content type.

    Pattern: Analyze Type → [Strategy A | Strategy B | Strategy C] → Edit
    Useful for handling different content types with specialized editing approaches.
    """

    def __init__(
        self,
        name: str,
        type_analyzer: Any,
        strategies: Dict[str, Any],
        default_strategy: Any = None,
    ):
        """
        Initialize adaptive editorial workflow.

        Args:
            name: Workflow name
            type_analyzer: Function that determines content type/strategy
            strategies: Dict mapping content types to editing strategies
            default_strategy: Default strategy if type is unknown
        """
        super().__init__(
            name=name,
            pattern=WorkflowPattern.CONDITIONAL,
            scope=WorkflowScope.EDITORIAL,
            description="Route to different review strategies based on content type",
            agents=[type_analyzer],
            parameters={
                "routing_criteria": "content_complexity",
                "fallback": "basic_reviewer",
            },
        )
        self.type_analyzer = type_analyzer
        self.strategies = strategies
        self.default_strategy = default_strategy
        logger.info(
            f"Adaptive editorial workflow '{name}' configured with {len(strategies)} strategies"
        )
