"""Gemini coordinator agent for intelligent task orchestration.

Coordinates specialized agents and manages multi-agent workflows.
Inherits from StatefulAgent for unified structure.
ADK integration for intelligent routing to be added later.
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from ...models.agent_models import AgentConfig, AgentRole, AgentStatus, AgentTask
from ...teams.content_team import ContentRole
from ...teams.editorial_team import EditorialRole
from ..stateful_agent import StatefulAgent
from ..text_provider import GeminiTextProvider

logger = logging.getLogger(__name__)


class SupportedTask(str, Enum):
    """Tasks supported by the Gemini team coordinator."""

    GENERATE_QUIZ = "generate_quiz"
    GENERATE_STORY = "generate_story"
    GENERATE_GAME = "generate_game"
    GENERATE_SIMULATION = "generate_simulation"
    REVIEW_CONTENT = "review_content"
    REFINE_CONTENT = "refine_content"
    VALIDATE_CONTENT = "validate_content"
    COMPLETE_WORKFLOW = "complete_workflow"


# Coordinator configuration
COORDINATOR_CONFIG = AgentConfig(
    role=ContentRole.CONTENT_WRITER,
    system_instruction="""You are an intelligent coordinator agent managing a team of specialized content generation agents.
Your role is to:
- Analyze incoming tasks and determine the best agent(s) to handle them
- Coordinate multi-agent workflows for complex tasks
- Ensure quality through review and refinement cycles
- Provide clear, structured coordination plans""",
    temperature=0.5,
    max_tokens=1024,
)


class GeminiCoordinatorAgent(StatefulAgent):
    """Coordinator agent for Gemini team.

    Provides:
    - Task routing to specialized agents
    - Multi-agent workflow coordination
    - Quality control through review cycles

    ADK integration for intelligent routing TBD.
    """

    def __init__(
        self,
        agent_id: str = "gemini_coordinator",
        config: Optional[AgentConfig] = None,
    ):
        """Initialize Gemini coordinator.

        Args:
            agent_id: Unique agent identifier
            config: Optional custom configuration
        """
        super().__init__(agent_id=agent_id, config=config or COORDINATOR_CONFIG)
        self.agent_registry: Dict[str, List["StatefulAgent"]] = {}
        self._adk_agent = None  # To be initialized with ADK
        logger.info(f"Initialized GeminiCoordinatorAgent {agent_id}")

    async def process_task(
        self, task_or_description: Any, parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process task with backwards-compatible interface.

        Supports both:
        - Old interface: process_task(task_description: str, parameters: Dict)
        - New interface: process_task(task: AgentTask, parameters: Optional[Dict])

        Args:
            task_or_description: AgentTask or string description
            parameters: Task parameters

        Returns:
            Task result dictionary
        """
        await self.update_status(AgentStatus.WORKING)

        # Handle old string-based interface
        if isinstance(task_or_description, str):
            # Old interface: convert to new format
            params = parameters or {}
            task = AgentTask(
                task_id=params.get("task", "generate"),
                agent_role=AgentRole.WRITER,  # Use base role for compatibility
                prompt=task_or_description,
                parameters=params,
                output_key="content",
            )
            result = await self._execute_task(task, task_or_description)
        else:
            # New AgentTask interface - use parent implementation
            result = await super().process_task(task_or_description, parameters)

        await self.update_status(AgentStatus.COMPLETED)
        return result

    def register_agent(self, agent: "StatefulAgent") -> None:
        """Register an agent with the coordinator.

        Args:
            agent: Agent to register
        """
        role = str(
            agent.agent_config.role.value
            if hasattr(agent.agent_config.role, "value")
            else agent.agent_config.role
        )
        if role not in self.agent_registry:
            self.agent_registry[role] = []
        self.agent_registry[role].append(agent)
        logger.info(f"Registered agent {agent.agent_id} with role {role}")

    def get_registered_agents(self) -> Dict[str, List[str]]:
        """Get summary of registered agents.

        Returns:
            Dict of role -> list of agent IDs
        """
        return {
            role: [agent.agent_id for agent in agents]
            for role, agents in self.agent_registry.items()
        }

    def get_supported_tasks(self) -> List[Dict[str, Any]]:
        """Get list of supported tasks.

        Returns:
            List of task definitions
        """
        return [
            {"task": t.value, "description": t.name.replace("_", " ").title()}
            for t in SupportedTask
        ]

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute coordinator task.

        Routes to appropriate handler based on task type.

        Args:
            task: Task to execute
            resolved_prompt: Resolved prompt string

        Returns:
            Task result dictionary
        """
        context = self.prepare_task_context(task)
        task_type = context.get("task", task.task_id)

        logger.info(f"Coordinator processing task: {task_type}")

        handlers = {
            SupportedTask.GENERATE_QUIZ: self._handle_generate,
            SupportedTask.GENERATE_STORY: self._handle_generate,
            SupportedTask.GENERATE_GAME: self._handle_generate,
            SupportedTask.GENERATE_SIMULATION: self._handle_generate,
            SupportedTask.REVIEW_CONTENT: self._handle_review,
            SupportedTask.COMPLETE_WORKFLOW: self._handle_complete_workflow,
        }

        # Find handler
        handler = None
        for supported_task, h in handlers.items():
            if task_type == supported_task or task_type == supported_task.value:
                handler = h
                break

        if handler:
            return await handler(context)

        # Default: try to route based on content type
        return await self._handle_generate(context)

    async def _handle_generate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle content generation task.

        Args:
            context: Task context with parameters

        Returns:
            Generation result
        """
        task_type = context.get("task", "")
        content_type = self._infer_content_type(task_type, context)

        agent = self._get_agent_for_content_type(content_type)
        if not agent:
            return {"error": f"No agent available for {content_type}"}

        # Create task for the agent
        gen_task = AgentTask(
            task_id="generate",
            agent_role=AgentRole.WRITER,
            prompt=f"Generate {content_type} about {{topic}}",
            parameters=context,
            output_key="content",
        )

        result = await agent.process_task(gen_task, context)

        return {
            "task": f"generate_{content_type}",
            "content": result,
            "agent_used": agent.agent_id,
            "status": "completed",
        }

    async def _handle_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle content review task.

        Args:
            context: Task context with content to review

        Returns:
            Review result
        """
        reviewer = self._get_agent_by_role("editorial_reviewer")
        if not reviewer:
            return {"error": "No reviewer agent available"}

        review_task = AgentTask(
            task_id="review_content",
            agent_role=AgentRole.REVIEWER,
            prompt="Review content",
            parameters=context,
            output_key="review",
        )

        result = await reviewer.process_task(review_task, context)

        return {
            "task": "review_content",
            "review": result,
            "agent_used": reviewer.agent_id,
            "status": "completed",
        }

    async def _handle_complete_workflow(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle complete workflow: Generate -> Review -> Refine.

        Args:
            context: Task context

        Returns:
            Workflow result
        """
        content_type = context.get("content_type", "quiz")

        # Step 1: Generate
        logger.info(f"Workflow Step 1: Generating {content_type}")
        gen_result = await self._handle_generate(context)

        if "error" in gen_result:
            return gen_result

        generated_content = gen_result.get("content", {})
        agents_used = [gen_result.get("agent_used")]

        # Step 2: Review (if reviewer available)
        reviewer = self._get_agent_by_role("editorial_reviewer")
        review_result = None

        if reviewer:
            logger.info(f"Workflow Step 2: Reviewing {content_type}")
            review_context = {
                "content": generated_content,
                "content_type": content_type,
            }
            review_result = await self._handle_review(review_context)
            agents_used.append(reviewer.agent_id)

            # Step 3: Refine if needed
            if review_result.get("review", {}).get("status") == "needs_revision":
                logger.info(f"Workflow Step 3: Refining {content_type}")
                # Re-generate with feedback
                refine_context = {
                    **context,
                    "feedback": review_result.get("review", {}).get("issues", []),
                }
                gen_result = await self._handle_generate(refine_context)
                generated_content = gen_result.get("content", {})

        return {
            "task": "complete_workflow",
            "content_type": content_type,
            "final_content": generated_content,
            "review": review_result,
            "agents_involved": agents_used,
            "workflow_steps": (
                ["generate", "review", "refine"] if review_result else ["generate"]
            ),
            "status": "completed",
        }

    def _infer_content_type(self, task_type: str, context: Dict[str, Any]) -> str:
        """Infer content type from task or context.

        Args:
            task_type: Task type string
            context: Task context

        Returns:
            Content type string
        """
        # Check explicit content_type
        if context.get("content_type"):
            return context["content_type"]

        # Infer from task type
        task_str = str(task_type).lower()
        if "quiz" in task_str:
            return "quiz"
        elif "story" in task_str:
            return "story"
        elif "game" in task_str:
            return "game"
        elif "simulation" in task_str:
            return "simulation"

        return "quiz"  # Default

    def _get_agent_for_content_type(
        self, content_type: str
    ) -> Optional["StatefulAgent"]:
        """Get agent for a content type.

        Args:
            content_type: Content type string

        Returns:
            Agent or None
        """
        role_mapping = {
            "quiz": ContentRole.QUIZ_WRITER.value,
            "story": ContentRole.STORY_WRITER.value,
            "game": ContentRole.GAME_WRITER.value,
            "simulation": ContentRole.SIMULATION_WRITER.value,
        }

        role = role_mapping.get(content_type)
        if role:
            return self._get_agent_by_role(role)
        return None

    def _get_agent_by_role(self, role: str) -> Optional["StatefulAgent"]:
        """Get an agent by role.

        Args:
            role: Role string

        Returns:
            Agent or None
        """
        agents = self.agent_registry.get(role, [])
        return agents[0] if agents else None


__all__ = ["GeminiCoordinatorAgent", "SupportedTask"]
