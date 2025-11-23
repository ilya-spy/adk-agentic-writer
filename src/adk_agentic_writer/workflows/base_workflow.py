"""Abstract base workflow patterns - framework-agnostic orchestration."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class WorkflowPattern(ABC):
    """
    Abstract base class for workflow orchestration patterns.
    
    This defines the interface that any workflow implementation must follow,
    keeping the orchestration logic separate from the underlying framework (ADK, LangChain, etc.)
    """

    def __init__(self, name: str):
        """
        Initialize workflow pattern.

        Args:
            name: Name identifier for this workflow
        """
        self.name = name
        logger.info(f"Initialized workflow pattern: {name}")

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow pattern.

        Args:
            input_data: Input data for the workflow

        Returns:
            Output data from the workflow execution
        """
        pass


class SequentialWorkflow(WorkflowPattern):
    """
    Abstract sequential workflow - executes agents in order.
    
    Pattern: A → B → C
    Each agent's output becomes the input for the next agent.
    """

    def __init__(self, name: str, agents: List[Any]):
        """
        Initialize sequential workflow.

        Args:
            name: Workflow name
            agents: List of agents to execute sequentially
        """
        super().__init__(name)
        self.agents = agents
        logger.info(f"Sequential workflow '{name}' configured with {len(agents)} agents")

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agents sequentially."""
        pass


class ParallelWorkflow(WorkflowPattern):
    """
    Abstract parallel workflow - executes agents concurrently.
    
    Pattern: [A, B, C] → Merge
    All agents receive the same input and execute simultaneously.
    """

    def __init__(self, name: str, agents: List[Any], merge_strategy: str = "combine"):
        """
        Initialize parallel workflow.

        Args:
            name: Workflow name
            agents: List of agents to execute in parallel
            merge_strategy: How to merge results - 'combine', 'first', 'vote'
        """
        super().__init__(name)
        self.agents = agents
        self.merge_strategy = merge_strategy
        logger.info(f"Parallel workflow '{name}' configured with {len(agents)} agents")

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agents in parallel."""
        pass


class LoopWorkflow(WorkflowPattern):
    """
    Abstract loop workflow - executes an agent repeatedly until condition is met.
    
    Pattern: A → Check → A → Check → ... → Done
    Useful for iterative refinement or multi-turn interactions.
    """

    def __init__(
        self,
        name: str,
        agent: Any,
        condition: Callable[[Dict[str, Any], int], bool],
        max_iterations: int = 10,
    ):
        """
        Initialize loop workflow.

        Args:
            name: Workflow name
            agent: Agent to execute in loop
            condition: Function that returns True to continue looping
            max_iterations: Maximum number of iterations
        """
        super().__init__(name)
        self.agent = agent
        self.condition = condition
        self.max_iterations = max_iterations
        logger.info(f"Loop workflow '{name}' configured with max {max_iterations} iterations")

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent in a loop until condition is met."""
        pass


class ConditionalWorkflow(WorkflowPattern):
    """
    Abstract conditional workflow - routes to different agents based on conditions.
    
    Pattern: Condition → [A | B | C]
    Useful for decision trees and branching logic.
    """

    def __init__(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], str],
        agents: Dict[str, Any],
        default_agent: Optional[Any] = None,
    ):
        """
        Initialize conditional workflow.

        Args:
            name: Workflow name
            condition: Function that returns agent key to execute
            agents: Dict mapping keys to agents
            default_agent: Agent to use if condition returns unknown key
        """
        super().__init__(name)
        self.condition = condition
        self.agents = agents
        self.default_agent = default_agent
        logger.info(f"Conditional workflow '{name}' configured with {len(agents)} branches")

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute appropriate agent based on condition."""
        pass

