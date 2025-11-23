"""Agent workflow patterns and predefined instances.

All workflows inherit from the base Workflow class and use metadata
to specify their orchestration pattern.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from ..models.agent_models import WorkflowPattern, WorkflowScope
from .base_workflow import Workflow

logger = logging.getLogger(__name__)


class SequentialAgentWorkflow(Workflow):
    """
    Sequential agent workflow - executes agents in order.

    Pattern: Agent A → Agent B → Agent C
    Each agent's output becomes the input for the next agent.
    """

    def __init__(self, name: str, agents: List[Any]):
        """
        Initialize sequential agent workflow.

        Args:
            name: Workflow name
            agents: List of agents to execute sequentially
        """
        super().__init__(
            name=name,
            pattern=WorkflowPattern.SEQUENTIAL,
            scope=WorkflowScope.AGENT,
            description="Execute agents in sequence, output of each feeds into next",
            agents=agents,
            parameters={"execution_order": "strict"},
        )
        logger.info(
            f"Sequential agent workflow '{name}' configured with {len(agents)} agents"
        )


class ParallelAgentWorkflow(Workflow):
    """
    Parallel agent workflow - executes agents concurrently.

    Pattern: [Agent A, Agent B, Agent C] → Merge
    All agents receive the same input and execute simultaneously.
    """

    def __init__(self, name: str, agents: List[Any], merge_strategy: str = "combine"):
        """
        Initialize parallel agent workflow.

        Args:
            name: Workflow name
            agents: List of agents to execute in parallel
            merge_strategy: How to merge results - 'combine', 'first', 'vote'
        """
        super().__init__(
            name=name,
            pattern=WorkflowPattern.PARALLEL,
            scope=WorkflowScope.AGENT,
            description="Execute agents concurrently and merge results",
            agents=agents,
            merge_strategy=merge_strategy,
            parameters={"wait_for_all": True},
        )
        logger.info(
            f"Parallel agent workflow '{name}' configured with {len(agents)} agents"
        )


class LoopAgentWorkflow(Workflow):
    """
    Loop agent workflow - executes an agent repeatedly until condition is met.

    Pattern: Agent → Check → Agent → Check → ... → Done
    Useful for iterative refinement or multi-turn agent interactions.
    """

    def __init__(
        self,
        name: str,
        agent: Any,
        condition: Optional[Callable[[Dict[str, Any], int], bool]] = None,
        max_iterations: int = 10,
    ):
        """
        Initialize loop agent workflow.

        Args:
            name: Workflow name
            agent: Agent to execute in loop
            condition: Function that returns True to continue looping
            max_iterations: Maximum number of iterations
        """
        super().__init__(
            name=name,
            pattern=WorkflowPattern.LOOP,
            scope=WorkflowScope.AGENT,
            description="Execute agent repeatedly until condition met",
            agents=[agent],
            condition=condition,
            max_iterations=max_iterations,
            parameters={"condition": "quality_threshold_met"},
        )
        logger.info(
            f"Loop agent workflow '{name}' configured with max {max_iterations} iterations"
        )


class ConditionalAgentWorkflow(Workflow):
    """
    Conditional agent workflow - routes to different agents based on conditions.

    Pattern: Condition → [Agent A | Agent B | Agent C]
    Useful for decision trees and branching agent logic.
    """

    def __init__(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], str],
        agents: Dict[str, Any],
    ):
        """
        Initialize conditional agent workflow.

        Args:
            name: Workflow name
            condition: Function that returns agent key to execute
            agents: Dict mapping keys to agents
        """
        super().__init__(
            name=name,
            pattern=WorkflowPattern.CONDITIONAL,
            scope=WorkflowScope.AGENT,
            description="Route to different agents based on conditions",
            agents=agents,
            condition=condition,
            parameters={"routing_logic": "condition_based"},
        )
        logger.info(
            f"Conditional agent workflow '{name}' configured with {len(agents)} branches"
        )
