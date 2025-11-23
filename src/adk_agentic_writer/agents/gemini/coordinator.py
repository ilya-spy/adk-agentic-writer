"""Gemini coordinator agent using Google ADK for intelligent task orchestration.

This coordinator uses Google ADK to intelligently route tasks to the appropriate
specialized agents and manage complex multi-agent workflows.
"""

import json
import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

from ...models.agent_models import AGENT_TEAM_CONFIGS, AgentRole, AgentStatus
from ...models.content_models import ContentType
from ...models.editorial_models import (
    EditorialRequest,
    EditorialAction,
    EditorialWorkflow,
    ContentRevision,
    QualityMetrics,
)
from ...workflows import (
    SequentialEditorialWorkflow,
    LoopAgentWorkflow,
    ConditionalAgentWorkflow,
)
from ...utils import substitute_variables
from ..base_agent import BaseAgent

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
    COMPLETE_WORKFLOW = "complete_workflow"  # Generate + Review + Refine
    GENERATE_MULTIMODAL = "generate_multimodal"  # Complex multi-content orchestration


class GeminiCoordinatorAgent(BaseAgent):
    """Coordinator agent using Google ADK for intelligent task orchestration.

    This coordinator:
    - Routes tasks to appropriate specialized agents
    - Manages multi-agent workflows
    - Uses Google ADK for intelligent decision-making
    - Coordinates generation, review, and refinement cycles

    Implements:
    - AgentProtocol: process_task, update_status, get_state, receive_message
    """

    def __init__(
        self,
        agent_id: str = "gemini_coordinator",
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the Gemini coordinator agent with Google ADK."""
        super().__init__(agent_id, AgentRole.COORDINATOR, config)

        # Get system instruction from AGENT_TEAM_CONFIGS
        agent_config = AGENT_TEAM_CONFIGS.get(AgentRole.COORDINATOR)

        # Create Google ADK Agent instance for coordination logic
        self.adk_agent = Agent(
            name="CoordinatorAgent",
            model=Gemini(model="gemini-2.0-flash-exp"),
            instruction=(
                agent_config.system_instruction
                if agent_config
                else self._get_default_instruction()
            ),
            output_key="coordination_plan",
        )
        # InMemoryRunner requires agent parameter
        self.runner = InMemoryRunner(agent=self.adk_agent)

        # Agent registry
        self.agent_registry: Dict[AgentRole, List[BaseAgent]] = {}

        logger.info(f"Initialized Gemini coordinator {agent_id}")

    def _get_default_instruction(self) -> str:
        """Default instruction if not in config."""
        return """You are an intelligent coordinator agent managing a team of specialized content generation agents.
Your role is to:
- Analyze incoming tasks and determine the best agent(s) to handle them
- Coordinate multi-agent workflows for complex tasks
- Ensure quality through review and refinement cycles
- Provide clear, structured coordination plans"""

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the coordinator.

        Args:
            agent: Agent to register
        """
        if agent.role not in self.agent_registry:
            self.agent_registry[agent.role] = []
        self.agent_registry[agent.role].append(agent)
        logger.info(f"Registered agent {agent.agent_id} with role {agent.role}")

    def get_supported_tasks(self) -> List[Dict[str, Any]]:
        """Get list of supported tasks with descriptions.

        Returns:
            List of task definitions
        """
        return [
            {
                "task": SupportedTask.GENERATE_QUIZ,
                "description": "Generate an interactive quiz on any topic",
                "parameters": {
                    "topic": "str (required)",
                    "num_questions": "int (default: 5)",
                    "difficulty": "str (easy|medium|hard, default: medium)",
                },
                "example": {
                    "task": "generate_quiz",
                    "topic": "Python programming",
                    "num_questions": 10,
                    "difficulty": "medium",
                },
            },
            {
                "task": SupportedTask.GENERATE_STORY,
                "description": "Generate a branched narrative story",
                "parameters": {
                    "topic": "str (required)",
                    "genre": "str (default: fantasy)",
                    "num_branches": "int (default: 3)",
                },
                "example": {
                    "task": "generate_story",
                    "topic": "space exploration",
                    "genre": "sci-fi",
                    "num_branches": 5,
                },
            },
            {
                "task": SupportedTask.GENERATE_GAME,
                "description": "Generate a quest-based game",
                "parameters": {
                    "topic": "str (required)",
                    "complexity": "str (simple|medium|complex, default: medium)",
                    "theme": "str (default: fantasy)",
                },
                "example": {
                    "task": "generate_game",
                    "topic": "medieval adventure",
                    "complexity": "medium",
                    "theme": "fantasy",
                },
            },
            {
                "task": SupportedTask.GENERATE_SIMULATION,
                "description": "Generate an interactive web simulation",
                "parameters": {
                    "topic": "str (required)",
                    "simulation_type": "str (default: interactive)",
                    "complexity": "str (default: medium)",
                },
                "example": {
                    "task": "generate_simulation",
                    "topic": "pendulum physics",
                    "simulation_type": "interactive",
                    "complexity": "medium",
                },
            },
            {
                "task": SupportedTask.REVIEW_CONTENT,
                "description": "Review and provide feedback on content",
                "parameters": {
                    "content": "dict (required)",
                    "content_type": "str (required)",
                    "review_criteria": "list[str] (optional)",
                },
                "example": {
                    "task": "review_content",
                    "content": {"title": "My Quiz", "questions": [...]},
                    "content_type": "quiz",
                },
            },
            {
                "task": SupportedTask.REFINE_CONTENT,
                "description": "Refine content based on feedback",
                "parameters": {
                    "content": "dict (required)",
                    "feedback": "str or list[Feedback] (required)",
                },
                "example": {
                    "task": "refine_content",
                    "content": {...},
                    "feedback": "Improve clarity in questions 2 and 5",
                },
            },
            {
                "task": SupportedTask.VALIDATE_CONTENT,
                "description": "Validate content quality and correctness",
                "parameters": {
                    "content": "dict (required)",
                    "content_type": "str (required)",
                },
                "example": {
                    "task": "validate_content",
                    "content": {...},
                    "content_type": "quiz",
                },
            },
            {
                "task": SupportedTask.COMPLETE_WORKFLOW,
                "description": "Complete workflow: Generate → Review → Refine",
                "parameters": {
                    "content_type": "str (quiz|story|game|simulation, required)",
                    "topic": "str (required)",
                    "...": "Additional parameters for the content type",
                },
                "example": {
                    "task": "complete_workflow",
                    "content_type": "quiz",
                    "topic": "Python programming",
                    "num_questions": 10,
                },
            },
            {
                "task": SupportedTask.GENERATE_MULTIMODAL,
                "description": "Generate complex multimodal content with strategic orchestration",
                "parameters": {
                    "topic": "str (required)",
                    "content_strategy": "str (sequential|loop|conditional|adaptive, required)",
                    "components": "list[dict] (content types and parameters, required)",
                    "editorial_strategy": "str (iterative|adaptive|quality_driven, default: iterative)",
                    "quality_threshold": "float (0-100, default: 80.0)",
                    "max_iterations": "int (default: 3)",
                },
                "example": {
                    "task": "generate_multimodal",
                    "topic": "Introduction to Python",
                    "content_strategy": "sequential",
                    "components": [
                        {"type": "story", "purpose": "introduction", "num_branches": 2},
                        {"type": "quiz", "purpose": "assessment", "num_questions": 5},
                        {"type": "simulation", "purpose": "practice"},
                    ],
                    "editorial_strategy": "quality_driven",
                    "quality_threshold": 85.0,
                },
            },
        ]

    async def process_task(
        self, task_description: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a task by coordinating specialized agents.

        Args:
            task_description: Description of the task
            parameters: Task parameters including 'task' type

        Returns:
            Dict containing results
        """
        await self.update_status(AgentStatus.WORKING)

        task_type = parameters.get("task", task_description)
        logger.info(f"Coordinator processing task: {task_type}")

        try:
            # Route to appropriate handler
            if task_type == SupportedTask.GENERATE_QUIZ:
                result = await self._handle_generate_quiz(parameters)
            elif task_type == SupportedTask.GENERATE_STORY:
                result = await self._handle_generate_story(parameters)
            elif task_type == SupportedTask.GENERATE_GAME:
                result = await self._handle_generate_game(parameters)
            elif task_type == SupportedTask.GENERATE_SIMULATION:
                result = await self._handle_generate_simulation(parameters)
            elif task_type == SupportedTask.REVIEW_CONTENT:
                result = await self._handle_review_content(parameters)
            elif task_type == SupportedTask.REFINE_CONTENT:
                result = await self._handle_refine_content(parameters)
            elif task_type == SupportedTask.VALIDATE_CONTENT:
                result = await self._handle_validate_content(parameters)
            elif task_type == SupportedTask.COMPLETE_WORKFLOW:
                result = await self._handle_complete_workflow(parameters)
            elif task_type == SupportedTask.GENERATE_MULTIMODAL:
                result = await self._handle_generate_multimodal(parameters)
            else:
                result = await self._handle_custom_task(task_description, parameters)

            await self.update_status(AgentStatus.COMPLETED)
            return result

        except Exception as e:
            logger.error(f"Error in coordinator: {e}")
            await self.update_status(AgentStatus.ERROR)
            return {"error": str(e), "task": task_type, "status": "failed"}

    async def _handle_generate_quiz(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle quiz generation task."""
        writer = self._get_agent_by_role(AgentRole.QUIZ_WRITER)
        if not writer:
            return {"error": "No quiz writer agent available"}

        result = await writer.process_task("Generate quiz", parameters)
        return {
            "task": "generate_quiz",
            "content": result,
            "agent_used": writer.agent_id,
            "status": "completed",
        }

    async def _handle_generate_story(
        self, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle story generation task."""
        writer = self._get_agent_by_role(AgentRole.STORY_WRITER)
        if not writer:
            return {"error": "No story writer agent available"}

        result = await writer.process_task("Generate story", parameters)
        return {
            "task": "generate_story",
            "content": result,
            "agent_used": writer.agent_id,
            "status": "completed",
        }

    async def _handle_generate_game(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle game generation task."""
        designer = self._get_agent_by_role(AgentRole.GAME_DESIGNER)
        if not designer:
            return {"error": "No game designer agent available"}

        result = await designer.process_task("Generate game", parameters)
        return {
            "task": "generate_game",
            "content": result,
            "agent_used": designer.agent_id,
            "status": "completed",
        }

    async def _handle_generate_simulation(
        self, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle simulation generation task."""
        designer = self._get_agent_by_role(AgentRole.SIMULATION_DESIGNER)
        if not designer:
            return {"error": "No simulation designer agent available"}

        result = await designer.process_task("Generate simulation", parameters)
        return {
            "task": "generate_simulation",
            "content": result,
            "agent_used": designer.agent_id,
            "status": "completed",
        }

    async def _handle_review_content(
        self, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle content review task."""
        reviewer = self._get_agent_by_role(AgentRole.REVIEWER)
        if not reviewer:
            return {"error": "No reviewer agent available"}

        result = await reviewer.process_task("Review content", parameters)
        return {
            "task": "review_content",
            "review": result,
            "agent_used": reviewer.agent_id,
            "status": "completed",
        }

    async def _handle_refine_content(
        self, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle content refinement task."""
        # Use appropriate agent based on content type
        content_type = parameters.get("content_type", "general")
        agent = self._get_agent_for_content_type(content_type)

        if not agent:
            return {"error": f"No agent available for content type {content_type}"}

        result = await agent.process_task("Refine content", parameters)
        return {
            "task": "refine_content",
            "refined_content": result,
            "agent_used": agent.agent_id,
            "status": "completed",
        }

    async def _handle_validate_content(
        self, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle content validation task."""
        reviewer = self._get_agent_by_role(AgentRole.REVIEWER)
        if not reviewer:
            return {"error": "No reviewer agent available"}

        # Validation is part of review
        result = await reviewer.process_task("Validate content", parameters)
        return {
            "task": "validate_content",
            "validation": result,
            "agent_used": reviewer.agent_id,
            "status": "completed",
        }

    async def _handle_complete_workflow(
        self, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle complete workflow: Generate → Review → Refine."""
        content_type = parameters.get("content_type")
        if not content_type:
            return {"error": "content_type is required for complete_workflow"}

        # Step 1: Generate
        writer = self._get_agent_for_content_type(content_type)
        if not writer:
            return {"error": f"No agent available for content type {content_type}"}

        logger.info(f"Workflow Step 1: Generating {content_type}")
        generated = await writer.process_task(f"Generate {content_type}", parameters)

        # Step 2: Review
        reviewer = self._get_agent_by_role(AgentRole.REVIEWER)
        if reviewer:
            logger.info(f"Workflow Step 2: Reviewing {content_type}")
            review_result = await reviewer.process_task(
                "Review content", {"content": generated, "content_type": content_type}
            )

            # Step 3: Refine if needed
            if review_result.get("issues_found") or review_result.get("suggestions"):
                logger.info(f"Workflow Step 3: Refining {content_type}")
                feedback = review_result.get("review", "Improve based on review")
                refined = await writer.process_task(
                    "Refine content", {"content": generated, "feedback": feedback}
                )

                return {
                    "task": "complete_workflow",
                    "content_type": content_type,
                    "original_content": generated,
                    "review": review_result,
                    "final_content": refined,
                    "agents_involved": [writer.agent_id, reviewer.agent_id],
                    "workflow_steps": ["generate", "review", "refine"],
                    "status": "completed",
                }

        return {
            "task": "complete_workflow",
            "content_type": content_type,
            "final_content": generated,
            "agents_involved": [writer.agent_id],
            "workflow_steps": ["generate"],
            "status": "completed",
        }

    async def _handle_generate_multimodal(
        self, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle multimodal content generation with strategic orchestration.

        This method:
        1. Analyzes the multimodal strategy using Google ADK
        2. Creates an editorial workflow to track progress
        3. Orchestrates multiple content generation tasks
        4. Applies editorial models for quality control
        5. Uses loops/conditionals for iterative refinement
        6. Coordinates with specialized agents as "supportive coordinators"

        Args:
            parameters: Multimodal generation parameters

        Returns:
            Dict containing all generated content and workflow metadata
        """
        topic = parameters.get("topic")
        if not topic:
            return {"error": "topic is required for multimodal generation"}

        content_strategy = parameters.get("content_strategy", "sequential")
        components = parameters.get("components", [])
        editorial_strategy = parameters.get("editorial_strategy", "iterative")
        quality_threshold = parameters.get("quality_threshold", 80.0)
        max_iterations = parameters.get("max_iterations", 3)

        if not components:
            return {"error": "components list is required"}

        logger.info(
            f"Starting multimodal generation: {topic} with {len(components)} components"
        )

        # Create editorial workflow to track the entire process
        workflow_id = f"multimodal_{topic.replace(' ', '_')}"
        editorial_workflow = EditorialWorkflow(
            workflow_id=workflow_id,
            content_id=workflow_id,
            current_version=1,
            status="in_progress",
            agents_involved=[self.agent_id],
        )

        # Step 1: Use Google ADK to create strategic plan
        strategy_plan = await self._create_multimodal_strategy(
            topic, content_strategy, components, editorial_strategy
        )

        logger.info(f"Strategy plan created: {strategy_plan.get('strategy_type')}")

        # Step 2: Execute strategy based on type
        if content_strategy == "sequential":
            result = await self._execute_sequential_multimodal(
                topic, components, editorial_workflow, quality_threshold
            )
        elif content_strategy == "loop":
            result = await self._execute_loop_multimodal(
                topic, components, editorial_workflow, quality_threshold, max_iterations
            )
        elif content_strategy == "conditional":
            result = await self._execute_conditional_multimodal(
                topic, components, editorial_workflow, quality_threshold
            )
        elif content_strategy == "adaptive":
            result = await self._execute_adaptive_multimodal(
                topic,
                components,
                editorial_workflow,
                quality_threshold,
                max_iterations,
                strategy_plan,
            )
        else:
            return {"error": f"Unknown content strategy: {content_strategy}"}

        # Mark workflow as completed
        editorial_workflow.status = "completed"

        return {
            "task": "generate_multimodal",
            "topic": topic,
            "content_strategy": content_strategy,
            "editorial_strategy": editorial_strategy,
            "components_generated": len(result.get("components", [])),
            "workflow": editorial_workflow.model_dump(),
            "strategy_plan": strategy_plan,
            "result": result,
            "status": "completed",
        }

    async def _create_multimodal_strategy(
        self,
        topic: str,
        content_strategy: str,
        components: List[Dict[str, Any]],
        editorial_strategy: str,
    ) -> Dict[str, Any]:
        """Use Google ADK to create intelligent multimodal strategy."""
        prompt = f"""Create a strategic plan for generating multimodal educational content.

Topic: {topic}
Content Strategy: {content_strategy}
Editorial Strategy: {editorial_strategy}
Components: {json.dumps(components, indent=2)}

Analyze and provide:
1. Optimal order/flow for components
2. Dependencies between components
3. Quality checkpoints
4. Refinement strategies
5. Integration approach

Return JSON:
{{
    "strategy_type": "sequential|loop|conditional|adaptive",
    "component_order": ["story", "quiz", "simulation"],
    "dependencies": {{"quiz": ["story"], "simulation": ["quiz"]}},
    "quality_checkpoints": ["after_story", "after_quiz", "final"],
    "refinement_approach": "iterative|quality_driven|adaptive",
    "integration_notes": "How components work together"
}}"""

        try:
            result = await self.runner.run(
                input_data={"prompt": prompt, "topic": topic}
            )

            plan = json.loads(result.get("coordination_plan", "{}"))
            return plan
        except Exception as e:
            logger.warning(f"Error creating strategy plan: {e}, using default")
            return {
                "strategy_type": content_strategy,
                "component_order": [c.get("type") for c in components],
                "dependencies": {},
                "quality_checkpoints": ["final"],
                "refinement_approach": editorial_strategy,
            }

    async def _execute_sequential_multimodal(
        self,
        topic: str,
        components: List[Dict[str, Any]],
        editorial_workflow: EditorialWorkflow,
        quality_threshold: float,
    ) -> Dict[str, Any]:
        """Execute sequential multimodal generation."""
        logger.info("Executing sequential multimodal strategy")

        generated_components = []
        all_agents_used = []

        for idx, component in enumerate(components):
            component_type = component.get("type")
            component_purpose = component.get("purpose", "content")

            logger.info(
                f"Generating component {idx + 1}/{len(components)}: {component_type} ({component_purpose})"
            )

            # Generate component using supportive coordinator pattern
            component_result = await self._generate_component_with_support(
                topic=topic,
                component_type=component_type,
                component_params=component,
                editorial_workflow=editorial_workflow,
                quality_threshold=quality_threshold,
            )

            generated_components.append(
                {
                    "type": component_type,
                    "purpose": component_purpose,
                    "content": component_result.get("content"),
                    "quality_metrics": component_result.get("quality_metrics"),
                    "agent_used": component_result.get("agent_used"),
                    "iterations": component_result.get("iterations", 1),
                }
            )

            all_agents_used.extend(component_result.get("agents_involved", []))

        return {
            "strategy": "sequential",
            "components": generated_components,
            "agents_involved": list(set(all_agents_used)),
            "total_components": len(generated_components),
        }

    async def _execute_loop_multimodal(
        self,
        topic: str,
        components: List[Dict[str, Any]],
        editorial_workflow: EditorialWorkflow,
        quality_threshold: float,
        max_iterations: int,
    ) -> Dict[str, Any]:
        """Execute loop-based multimodal generation with iterative refinement."""
        logger.info(
            f"Executing loop multimodal strategy (max {max_iterations} iterations)"
        )

        generated_components = []
        all_agents_used = []
        iteration = 0
        overall_quality = 0.0

        # Loop until quality threshold met or max iterations reached
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Loop iteration {iteration}/{max_iterations}")

            iteration_components = []
            iteration_quality_scores = []

            for component in components:
                component_type = component.get("type")

                # Generate or refine component
                if iteration == 1:
                    # First iteration: generate
                    component_result = await self._generate_component_with_support(
                        topic=topic,
                        component_type=component_type,
                        component_params=component,
                        editorial_workflow=editorial_workflow,
                        quality_threshold=quality_threshold,
                    )
                else:
                    # Subsequent iterations: refine based on previous
                    previous_component = next(
                        (
                            c
                            for c in generated_components
                            if c["type"] == component_type
                        ),
                        None,
                    )
                    if previous_component:
                        component_result = await self._refine_component_with_support(
                            component=previous_component,
                            editorial_workflow=editorial_workflow,
                            quality_threshold=quality_threshold,
                        )
                    else:
                        continue

                iteration_components.append(component_result)

                # Track quality
                quality = component_result.get("quality_metrics", {}).get(
                    "overall_score", 0.0
                )
                iteration_quality_scores.append(quality)
                all_agents_used.extend(component_result.get("agents_involved", []))

            # Calculate overall quality
            if iteration_quality_scores:
                overall_quality = sum(iteration_quality_scores) / len(
                    iteration_quality_scores
                )

            # Update generated components
            generated_components = iteration_components

            logger.info(
                f"Iteration {iteration} complete. Overall quality: {overall_quality:.1f}"
            )

            # Check if quality threshold met
            if overall_quality >= quality_threshold:
                logger.info(
                    f"Quality threshold {quality_threshold} met at iteration {iteration}"
                )
                break

        return {
            "strategy": "loop",
            "components": generated_components,
            "agents_involved": list(set(all_agents_used)),
            "total_iterations": iteration,
            "final_quality": overall_quality,
            "quality_threshold_met": overall_quality >= quality_threshold,
        }

    async def _execute_conditional_multimodal(
        self,
        topic: str,
        components: List[Dict[str, Any]],
        editorial_workflow: EditorialWorkflow,
        quality_threshold: float,
    ) -> Dict[str, Any]:
        """Execute conditional multimodal generation with branching logic."""
        logger.info("Executing conditional multimodal strategy")

        generated_components = []
        all_agents_used = []
        branches_taken = []

        for idx, component in enumerate(components):
            component_type = component.get("type")
            condition = component.get("condition", "always")

            # Evaluate condition
            should_generate = await self._evaluate_condition(
                condition, generated_components, editorial_workflow
            )

            if should_generate:
                logger.info(f"Condition '{condition}' met, generating {component_type}")
                branches_taken.append(f"{idx}_{component_type}")

                component_result = await self._generate_component_with_support(
                    topic=topic,
                    component_type=component_type,
                    component_params=component,
                    editorial_workflow=editorial_workflow,
                    quality_threshold=quality_threshold,
                )

                generated_components.append(component_result)
                all_agents_used.extend(component_result.get("agents_involved", []))
            else:
                logger.info(
                    f"Condition '{condition}' not met, skipping {component_type}"
                )

        return {
            "strategy": "conditional",
            "components": generated_components,
            "agents_involved": list(set(all_agents_used)),
            "branches_taken": branches_taken,
            "total_components": len(generated_components),
        }

    async def _execute_adaptive_multimodal(
        self,
        topic: str,
        components: List[Dict[str, Any]],
        editorial_workflow: EditorialWorkflow,
        quality_threshold: float,
        max_iterations: int,
        strategy_plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute adaptive multimodal generation with AI-driven decisions."""
        logger.info("Executing adaptive multimodal strategy with AI guidance")

        generated_components = []
        all_agents_used = []
        decisions_made = []

        for iteration in range(max_iterations):
            logger.info(f"Adaptive iteration {iteration + 1}/{max_iterations}")

            # Use Google ADK to decide next action
            decision = await self._make_adaptive_decision(
                topic,
                components,
                generated_components,
                editorial_workflow,
                strategy_plan,
            )

            decisions_made.append(decision)
            action = decision.get("action", "continue")

            if action == "stop":
                logger.info("AI decided to stop generation")
                break
            elif action == "generate":
                component_type = decision.get("component_type")
                component_params = decision.get("parameters", {})

                component_result = await self._generate_component_with_support(
                    topic=topic,
                    component_type=component_type,
                    component_params=component_params,
                    editorial_workflow=editorial_workflow,
                    quality_threshold=quality_threshold,
                )

                generated_components.append(component_result)
                all_agents_used.extend(component_result.get("agents_involved", []))
            elif action == "refine":
                component_idx = decision.get("component_index", 0)
                if component_idx < len(generated_components):
                    component_result = await self._refine_component_with_support(
                        component=generated_components[component_idx],
                        editorial_workflow=editorial_workflow,
                        quality_threshold=quality_threshold,
                    )
                    generated_components[component_idx] = component_result

        return {
            "strategy": "adaptive",
            "components": generated_components,
            "agents_involved": list(set(all_agents_used)),
            "decisions_made": decisions_made,
            "total_iterations": len(decisions_made),
        }

    async def _generate_component_with_support(
        self,
        topic: str,
        component_type: str,
        component_params: Dict[str, Any],
        editorial_workflow: EditorialWorkflow,
        quality_threshold: float,
    ) -> Dict[str, Any]:
        """Generate a component using supportive coordinator pattern.

        This acts as a "supportive coordinator" that handles mini-tasks.
        """
        # Get appropriate agent for component type
        agent = self._get_agent_for_content_type(component_type)
        if not agent:
            return {"error": f"No agent for component type {component_type}"}

        # Merge topic with component params
        params = {**component_params, "topic": topic}

        # Generate content
        content = await agent.process_task(f"Generate {component_type}", params)

        # Review content
        reviewer = self._get_agent_by_role(AgentRole.REVIEWER)
        review_result = None
        quality_metrics = None

        if reviewer:
            review_result = await reviewer.process_task(
                "Review content", {"content": content, "content_type": component_type}
            )
            quality_metrics = review_result.get("quality_metrics")

            # Refine if quality below threshold
            if quality_metrics:
                quality_score = quality_metrics.get("overall_score", 0.0)
                if quality_score < quality_threshold:
                    logger.info(
                        f"Quality {quality_score} below threshold {quality_threshold}, refining"
                    )
                    feedback = review_result.get("feedback", [])
                    content = await agent.process_task(
                        "Refine content", {"content": content, "feedback": feedback}
                    )

        # Create content revision for editorial workflow
        revision = ContentRevision(
            revision_id=f"rev_{len(editorial_workflow.revisions) + 1}",
            version=len(editorial_workflow.revisions) + 1,
            content=content,
            changes_made=[f"Generated {component_type} component"],
            feedback_addressed=[],
            created_by=agent.agent_id,
        )
        editorial_workflow.revisions.append(revision)

        if quality_metrics:
            editorial_workflow.quality_history.append(QualityMetrics(**quality_metrics))

        return {
            "type": component_type,
            "content": content,
            "quality_metrics": quality_metrics,
            "review": review_result,
            "agent_used": agent.agent_id,
            "agents_involved": [agent.agent_id]
            + ([reviewer.agent_id] if reviewer else []),
            "iterations": 1,
        }

    async def _refine_component_with_support(
        self,
        component: Dict[str, Any],
        editorial_workflow: EditorialWorkflow,
        quality_threshold: float,
    ) -> Dict[str, Any]:
        """Refine a component using supportive coordinator pattern."""
        component_type = component.get("type")
        content = component.get("content")

        agent = self._get_agent_for_content_type(component_type)
        if not agent:
            return component

        # Get feedback from previous review
        previous_review = component.get("review", {})
        feedback = previous_review.get("feedback", "Improve quality and clarity")

        # Refine content
        refined_content = await agent.process_task(
            "Refine content", {"content": content, "feedback": feedback}
        )

        # Review refined content
        reviewer = self._get_agent_by_role(AgentRole.REVIEWER)
        review_result = None
        quality_metrics = None

        if reviewer:
            review_result = await reviewer.process_task(
                "Review content",
                {"content": refined_content, "content_type": component_type},
            )
            quality_metrics = review_result.get("quality_metrics")

        # Update editorial workflow
        revision = ContentRevision(
            revision_id=f"rev_{len(editorial_workflow.revisions) + 1}",
            version=len(editorial_workflow.revisions) + 1,
            content=refined_content,
            changes_made=[f"Refined {component_type} component"],
            feedback_addressed=[],
            created_by=agent.agent_id,
        )
        editorial_workflow.revisions.append(revision)

        if quality_metrics:
            editorial_workflow.quality_history.append(QualityMetrics(**quality_metrics))

        return {
            "type": component_type,
            "content": refined_content,
            "quality_metrics": quality_metrics,
            "review": review_result,
            "agent_used": agent.agent_id,
            "agents_involved": [agent.agent_id]
            + ([reviewer.agent_id] if reviewer else []),
            "iterations": component.get("iterations", 1) + 1,
        }

    async def _evaluate_condition(
        self,
        condition: str,
        generated_components: List[Dict[str, Any]],
        editorial_workflow: EditorialWorkflow,
    ) -> bool:
        """Evaluate a condition for conditional branching."""
        if condition == "always":
            return True
        elif condition == "if_quality_high":
            if editorial_workflow.quality_history:
                last_quality = editorial_workflow.quality_history[-1].overall_score
                return last_quality >= 80.0
            return True
        elif condition == "if_previous_success":
            return len(generated_components) > 0
        else:
            # Use Google ADK to evaluate complex conditions
            return True

    async def _make_adaptive_decision(
        self,
        topic: str,
        components: List[Dict[str, Any]],
        generated_components: List[Dict[str, Any]],
        editorial_workflow: EditorialWorkflow,
        strategy_plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Use Google ADK to make adaptive decisions."""
        prompt = f"""Analyze the current multimodal generation state and decide next action.

Topic: {topic}
Planned components: {len(components)}
Generated components: {len(generated_components)}
Quality history: {[q.overall_score for q in editorial_workflow.quality_history[-3:]]}

Decide:
{{
    "action": "generate|refine|stop",
    "component_type": "quiz|story|game|simulation",
    "component_index": 0,
    "parameters": {{}},
    "reasoning": "why this decision"
}}"""

        try:
            result = await self.runner.run(
                input_data={"prompt": prompt, "topic": topic}
            )

            decision = json.loads(result.get("coordination_plan", "{}"))
            return decision
        except Exception as e:
            logger.warning(f"Error making adaptive decision: {e}, using default")
            # Default: generate next component if available
            if len(generated_components) < len(components):
                return {
                    "action": "generate",
                    "component_type": components[len(generated_components)].get("type"),
                    "reasoning": "Continue with planned components",
                }
            return {"action": "stop", "reasoning": "All components generated"}

    async def _handle_custom_task(
        self, task_description: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle custom task using Google ADK for intelligent routing."""
        logger.info(f"Handling custom task: {task_description}")

        # Use Google ADK to determine how to handle the task
        prompt = f"""Analyze this task and determine the best approach:

Task: {task_description}
Parameters: {json.dumps(parameters, indent=2)}

Available agents:
{self._get_available_agents_summary()}

Provide a coordination plan in JSON format:
{{
    "agent_role": "role to use",
    "action": "what action to take",
    "reasoning": "why this approach"
}}"""

        try:
            result = await self.runner.run(input_data={})

            plan = json.loads(result.get("coordination_plan", "{}"))
            logger.info(f"Coordination plan: {plan}")

            # Execute the plan
            # (This is a simplified version - could be expanded)
            return {
                "task": "custom",
                "description": task_description,
                "plan": plan,
                "status": "planned",
            }

        except Exception as e:
            logger.error(f"Error in custom task handling: {e}")
            return {
                "error": str(e),
                "task": "custom",
                "description": task_description,
                "status": "failed",
            }

    def _get_agent_for_content_type(self, content_type: str) -> Optional[BaseAgent]:
        """Get the appropriate agent for a content type."""
        role_mapping = {
            "quiz": AgentRole.QUIZ_WRITER,
            ContentType.QUIZ: AgentRole.QUIZ_WRITER,
            "story": AgentRole.STORY_WRITER,
            ContentType.BRANCHED_NARRATIVE: AgentRole.STORY_WRITER,
            "game": AgentRole.GAME_DESIGNER,
            ContentType.QUEST_GAME: AgentRole.GAME_DESIGNER,
            "simulation": AgentRole.SIMULATION_DESIGNER,
            ContentType.WEB_SIMULATION: AgentRole.SIMULATION_DESIGNER,
        }

        role = role_mapping.get(content_type)
        if role:
            return self._get_agent_by_role(role)
        return None

    def _get_agent_by_role(self, role: AgentRole) -> Optional[BaseAgent]:
        """Get an agent by role."""
        agents = self.agent_registry.get(role, [])
        return agents[0] if agents else None

    def _get_available_agents_summary(self) -> str:
        """Get a summary of available agents."""
        summary = []
        for role, agents in self.agent_registry.items():
            summary.append(f"- {role.value}: {len(agents)} agent(s)")
        return "\n".join(summary) if summary else "No agents registered"

    def get_registered_agents(self) -> Dict[AgentRole, List[str]]:
        """Get a summary of registered agents."""
        return {
            role: [agent.agent_id for agent in agents]
            for role, agents in self.agent_registry.items()
        }

    def format_task_prompt(self, prompt_template: str, agent_state: Any) -> str:
        """
        Format a task prompt using variable substitution.

        Coordinators can use {variable} syntax in task prompts to inject values
        from the agent's runtime variable storage.

        Args:
            prompt_template: Template string with {variable} placeholders
            agent_state: Agent state containing variables dict

        Returns:
            Formatted prompt with variables substituted

        Examples:
            >>> state.variables = {"topic": "Python", "difficulty": "medium", "num_questions": 10}
            >>> template = "Create a {difficulty} quiz about {topic} with {num_questions} questions"
            >>> coordinator.format_task_prompt(template, state)
            'Create a medium quiz about Python with 10 questions'
        """
        if not hasattr(agent_state, "variables"):
            logger.warning("Agent state does not have variables attribute")
            return prompt_template

        return substitute_variables(prompt_template, agent_state.variables)


__all__ = ["GeminiCoordinatorAgent", "SupportedTask"]
