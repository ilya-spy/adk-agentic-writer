"""Abstract agent workflow patterns - framework-agnostic agent orchestration.

These patterns inherit from corresponding base_workflow classes.
Implementations should be in agents/base/ or agents/gemini/ subdirectories.
"""

import logging
from typing import Any, Dict, List

from .base_workflow import (
    ConditionalWorkflow,
    LoopWorkflow,
    ParallelWorkflow,
    SequentialWorkflow,
)

logger = logging.getLogger(__name__)


class SequentialAgentWorkflow(SequentialWorkflow):
    """
    Sequential agent workflow - executes agents in order.
    
    Pattern: Agent A → Agent B → Agent C
    Each agent's output becomes the input for the next agent.
    
    Inherits from SequentialWorkflow base class.
    Implementations should override execute() method.
    """

    def __init__(self, name: str, agents: List[Any]):
        """
        Initialize sequential agent workflow.

        Args:
            name: Workflow name
            agents: List of agents to execute sequentially
        """
        super().__init__(name, agents)
        logger.info(f"Sequential agent workflow '{name}' configured with {len(agents)} agents")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agents sequentially."""
        result = input_data
        for agent in self.agents:
            task_desc = result.get("task_description", "Process task")
            params = result.get("parameters", {})
            result = await agent.process_task(task_desc, params)
        return result


class ParallelAgentWorkflow(ParallelWorkflow):
    """
    Parallel agent workflow - executes agents concurrently.
    
    Pattern: [Agent A, Agent B, Agent C] → Merge
    All agents receive the same input and execute simultaneously.
    
    Inherits from ParallelWorkflow base class.
    Implementations should override execute() method.
    """

    def __init__(self, name: str, agents: List[Any], merge_strategy: str = "combine"):
        """
        Initialize parallel agent workflow.

        Args:
            name: Workflow name
            agents: List of agents to execute in parallel
            merge_strategy: How to merge results - 'combine', 'first', 'vote'
        """
        super().__init__(name, agents, merge_strategy)
        logger.info(f"Parallel agent workflow '{name}' configured with {len(agents)} agents")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agents in parallel."""
        import asyncio
        task_desc = input_data.get("task_description", "Process task")
        params = input_data.get("parameters", {})
        
        tasks = [agent.process_task(task_desc, params) for agent in self.agents]
        results = await asyncio.gather(*tasks)
        
        if self.merge_strategy == "first":
            return results[0]
        elif self.merge_strategy == "combine":
            return {"results": results, "merged": True}
        else:
            return {"results": results}


class LoopAgentWorkflow(LoopWorkflow):
    """
    Loop agent workflow - executes an agent repeatedly until condition is met.
    
    Pattern: Agent → Check → Agent → Check → ... → Done
    Useful for iterative refinement or multi-turn agent interactions.
    
    Inherits from LoopWorkflow base class.
    Implementations should override execute() method.
    """

    def __init__(
        self,
        name: str,
        agent: Any,
        condition: Any,
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
        super().__init__(name)
        self.agent = agent
        self.condition = condition
        self.max_iterations = max_iterations
        logger.info(f"Loop agent workflow '{name}' configured with max {max_iterations} iterations")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent in a loop until condition is met."""
        result = input_data
        iteration = 0
        
        while iteration < self.max_iterations:
            task_desc = result.get("task_description", "Process task")
            params = result.get("parameters", {})
            result = await self.agent.process_task(task_desc, params)
            
            if not self.condition(result):
                break
            iteration += 1
        
        return result


class ConditionalAgentWorkflow(ConditionalWorkflow):
    """
    Conditional agent workflow - routes to different agents based on conditions.
    
    Pattern: Condition → [Agent A | Agent B | Agent C]
    Useful for decision trees and branching agent logic.
    
    Inherits from ConditionalWorkflow base class.
    Implementations should override execute() method.
    """

    def __init__(
        self,
        name: str,
        condition: Any,
        agents: Dict[str, Any],
        default_agent: Any = None,
    ):
        """
        Initialize conditional agent workflow.

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
        logger.info(f"Conditional agent workflow '{name}' configured with {len(agents)} branches")

