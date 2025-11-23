"""Editorial workflow patterns for content editing and refinement.

These workflows implement patterns for editing, validating, and refining content.
They inherit from base workflow classes and correspond to the EditorialProtocol.
"""

import logging
from typing import Any, Dict, List

from .base_workflow import LoopWorkflow, ParallelWorkflow, SequentialWorkflow

logger = logging.getLogger(__name__)


class SequentialEditorialWorkflow(SequentialWorkflow):
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
        super().__init__(name, stages)
        logger.info(f"Sequential editorial workflow '{name}' configured with {len(stages)} stages")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute editorial stages sequentially."""
        task_desc = input_data.get("task_description", "Process task")
        params = input_data.get("parameters", {})
        
        # Execute first stage (generator)
        result = await self.agents[0].process_task(task_desc, params)
        
        # If there's a second stage (reviewer), pass the generated content
        if len(self.agents) > 1:
            params_with_content = {**params, "content": result}
            result = await self.agents[1].process_task(task_desc, params_with_content)
            
        return result


class ParallelEditorialWorkflow(ParallelWorkflow):
    """
    Parallel editorial workflow - generates multiple content variants concurrently.
    
    Pattern: [Variant 1, Variant 2, Variant 3] → Select Best
    All variants are generated simultaneously and the best is selected.
    
    Corresponds to EditorialProtocol operations.
    """

    def __init__(self, name: str, generators: List[Any], selection_strategy: str = "first"):
        """
        Initialize parallel editorial workflow.

        Args:
            name: Workflow name
            generators: List of content generators to execute in parallel
            selection_strategy: How to select best - 'first', 'vote', 'quality_score'
        """
        super().__init__(name, generators, selection_strategy)
        self.selection_strategy = selection_strategy
        logger.info(f"Parallel editorial workflow '{name}' configured with {len(generators)} generators")


class IterativeEditorialWorkflow(LoopWorkflow):
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
        super().__init__(name, generator, lambda data, iteration: iteration < max_iterations, max_iterations)
        self.evaluator = evaluator
        logger.info(f"Iterative editorial workflow '{name}' configured with max {max_iterations} iterations")


class AdaptiveEditorialWorkflow(SequentialWorkflow):
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
        super().__init__(name, [type_analyzer])
        self.type_analyzer = type_analyzer
        self.strategies = strategies
        self.default_strategy = default_strategy
        logger.info(f"Adaptive editorial workflow '{name}' configured with {len(strategies)} strategies")

