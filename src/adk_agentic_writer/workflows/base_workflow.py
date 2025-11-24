"""Base workflow class - metadata-driven orchestration."""

import logging
from typing import Any, Callable, Dict, List, Optional

from ..models.agent_models import WorkflowMetadata, WorkflowPattern, WorkflowScope

logger = logging.getLogger(__name__)


class Workflow(WorkflowMetadata):
    """
    Base workflow class with pattern-driven execution and runtime logic.
    """

    # Allow extra fields for runtime-only attributes
    model_config = {"extra": "allow"}

    def __init__(
        self,
        name: str,
        pattern: WorkflowPattern,
        scope: WorkflowScope,
        description: str,
        agents: Optional[List[Any]] = None,
        condition: Optional[Callable] = None,
        max_iterations: Optional[int] = None,
        merge_strategy: Optional[str] = None,
        tasks: Optional[List[Any]] = None,
    ):
        """
        Initialize workflow with metadata.

        Args:
            name: Workflow name
            pattern: Orchestration pattern (SEQUENTIAL, PARALLEL, LOOP, CONDITIONAL)
            scope: Application scope (AGENT, CONTENT, EDITORIAL)
            description: What this workflow does
            agents: List or dict of agents/generators to execute (internal, not in metadata)
            condition: Condition function for loop/conditional workflows (internal, not in metadata)
            max_iterations: Maximum iterations for loop workflows
            merge_strategy: Strategy for parallel workflows
            tasks: List of AgentTask instances that agents can take on
        """
        # Initialize parent WorkflowMetadata
        super().__init__(
            name=name,
            pattern=pattern,
            scope=scope,
            description=description,
            max_iterations=max_iterations,
            merge_strategy=merge_strategy,
        )

        # Store runtime-only attributes (not part of metadata)
        self.agents = agents or []
        self.condition = condition
        self.tasks = tasks or []

        logger.info(
            f"Initialized {pattern.value} workflow '{name}' for {scope.value} scope with {len(self.tasks)} tasks"
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow based on its pattern.

        Args:
            input_data: Input data for the workflow

        Returns:
            Output data from the workflow execution
        """
        if self.pattern == WorkflowPattern.SEQUENTIAL:
            return await self.execute_sequential(input_data)
        elif self.pattern == WorkflowPattern.PARALLEL:
            return await self.execute_parallel(input_data)
        elif self.pattern == WorkflowPattern.LOOP:
            return await self.execute_loop(input_data)
        elif self.pattern == WorkflowPattern.CONDITIONAL:
            return await self.execute_conditional(input_data)
        else:
            raise ValueError(f"Unknown workflow pattern: {self.pattern}")

    async def execute_sequential(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agents sequentially."""
        result = input_data
        for i, agent in enumerate(self.agents):
            task_desc = result.get("task_description", "Process task")
            params = result.get("parameters", {})

            # After first agent, pass the result as content to next agent
            if i > 0:
                params = {**params, "content": result}

            result = await agent.process_task(task_desc, params)
        return result

    async def execute_parallel(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
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

    async def execute_loop(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent in a loop until condition is met."""
        result = input_data
        iteration = 0
        agent = self.agents[0] if self.agents else None

        if not agent:
            raise ValueError("Loop workflow requires at least one agent")

        max_iter = self.max_iterations or 10

        while iteration < max_iter:
            task_desc = result.get("task_description", "Process task")
            params = result.get("parameters", {})
            result = await agent.process_task(task_desc, params)

            if self.condition and not self.condition(result, iteration):
                break
            iteration += 1

        return result

    async def execute_conditional(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute appropriate agent based on condition."""
        if not self.condition:
            raise ValueError("Conditional workflow requires a condition function")

        # For conditional workflows, agents should be a dict
        agents_dict = (
            self.agents
            if isinstance(self.agents, dict)
            else {i: a for i, a in enumerate(self.agents)}
        )

        key = self.condition(input_data)
        agent = agents_dict.get(key)

        if not agent:
            raise ValueError(f"No agent found for condition key: {key}")

        task_desc = input_data.get("task_description", "Process task")
        params = input_data.get("parameters", {})
        return await agent.process_task(task_desc, params)
