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
        stage_labels: Optional[List[str]] = None,
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
            stage_labels: Human-readable labels per stage (e.g. ["Generating content", "Validating content"])
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
        self.stage_labels = stage_labels or []

        logger.info(
            f"Initialized {pattern.value} workflow '{name}' for {scope.value} scope with {len(self.tasks)} tasks"
        )

    def _stage_label(self, index: int, task: Any = None) -> str:
        """Get a human-readable label for a stage.

        Priority: explicit stage_labels[i] > task.task_id > "Stage {i}".
        Subclasses can override for richer labels.
        """
        if index < len(self.stage_labels):
            return self.stage_labels[index]
        if task and hasattr(task, "task_id"):
            return task.task_id.replace("_", " ").title()
        return f"Stage {index}"

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
        """Execute agents sequentially, forwarding state between stages.

        Task resolution per stage (priority order):
        1. ``input_data["tasks"][i]`` -- caller override for stage *i*
        2. ``self.tasks[i]``          -- workflow default for stage *i*

        Either list may be shorter than the number of agents; missing
        slots are treated as ``None``.  At least one source must provide
        a non-None task for each stage.

        State forwarding: each agent's ``state.variables`` are merged
        into ``params`` before calling the next stage so downstream
        agents can read upstream output_keys via ``prepare_task_context``.

        Stage labels are logged and collected in ``result["_workflow_log"]``.
        """
        input_tasks = input_data.get("tasks") or []
        params = input_data.get("parameters", {})
        result = None
        prev_agent = None
        workflow_log: List[str] = []

        total = len(self.agents)
        for i, agent in enumerate(self.agents):
            # Forward previous agent's state variables as params
            if prev_agent and hasattr(prev_agent, "state"):
                params = {**params, **prev_agent.state.variables}

            # Merge: caller override → workflow default
            input_task = input_tasks[i] if i < len(input_tasks) else None
            wf_task = self.tasks[i] if i < len(self.tasks) else None
            task = input_task or wf_task

            if task is None:
                raise ValueError(
                    f"No task for stage {i} ({agent.agent_id}): "
                    f"provide it in input_data['tasks'] or workflow.tasks"
                )

            label = self._stage_label(i, task)
            logger.info(
                "[%s] Stage %d/%d: %s (agent=%s)",
                self.name, i + 1, total, label, agent.agent_id,
            )
            workflow_log.append(label)

            result = await agent.process_task(task, params)
            prev_agent = agent

        # Attach stage log to result for UI consumption
        if isinstance(result, dict):
            result["_workflow_log"] = workflow_log

        return result

    async def execute_parallel(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agents in parallel."""
        import asyncio

        task = input_data.get("task")
        params = input_data.get("parameters", {})

        tasks = [agent.process_task(task, params) for agent in self.agents]
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
            task = result.get("task")
            params = result.get("parameters", {})
            result = await agent.process_task(task, params)

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

        task = input_data.get("task")
        params = input_data.get("parameters", {})
        return await agent.process_task(task, params)
