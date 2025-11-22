"""Coordinator agent that orchestrates the multi-agent system."""

import logging
import uuid
from typing import Any, Dict, List

from ..models.agent_models import AgentRole, AgentStatus, AgentTask
from ..models.content_models import ContentType
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """Coordinator agent that orchestrates content generation tasks."""

    def __init__(self, agent_id: str = "coordinator", config: Dict[str, Any] | None = None):
        """Initialize the coordinator agent."""
        super().__init__(agent_id, AgentRole.COORDINATOR, config)
        self.active_tasks: Dict[str, AgentTask] = {}
        self.agent_registry: Dict[AgentRole, List[BaseAgent]] = {}

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the coordinator."""
        if agent.role not in self.agent_registry:
            self.agent_registry[agent.role] = []
        self.agent_registry[agent.role].append(agent)
        logger.info(f"Registered agent {agent.agent_id} with role {agent.role}")

    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a content generation request by coordinating other agents.

        Args:
            task_description: Description of the content to generate
            parameters: Parameters including content_type, topic, etc.

        Returns:
            Dict containing the generated content and metadata
        """
        await self.update_status(AgentStatus.WORKING)
        
        content_type = parameters.get("content_type")
        topic = parameters.get("topic", task_description)
        
        logger.info(f"Coordinator processing request for {content_type}: {topic}")
        
        # Create tasks based on content type
        tasks = self._create_task_plan(content_type, topic, parameters)
        
        # Execute tasks
        results = await self._execute_tasks(tasks)
        
        await self.update_status(AgentStatus.COMPLETED)
        
        return {
            "content_type": content_type,
            "content": results,
            "agents_involved": [task.agent_role.value for task in tasks],
        }

    def _create_task_plan(
        self, content_type: ContentType, topic: str, parameters: Dict[str, Any]
    ) -> List[AgentTask]:
        """Create a plan of tasks for generating the requested content."""
        tasks = []
        
        # Determine which agent role is needed
        role_mapping = {
            ContentType.QUIZ: AgentRole.QUIZ_WRITER,
            ContentType.QUEST_GAME: AgentRole.GAME_DESIGNER,
            ContentType.BRANCHED_NARRATIVE: AgentRole.STORY_WRITER,
            ContentType.WEB_SIMULATION: AgentRole.SIMULATION_DESIGNER,
        }
        
        writer_role = role_mapping.get(content_type)
        if writer_role:
            # Create writing task
            write_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_role=writer_role,
                description=f"Create {content_type.value} about {topic}",
                parameters={"topic": topic, **parameters},
            )
            tasks.append(write_task)
            
            # Create review task
            review_task = AgentTask(
                task_id=str(uuid.uuid4()),
                agent_role=AgentRole.REVIEWER,
                description=f"Review and improve {content_type.value}",
                parameters={"topic": topic},
                dependencies=[write_task.task_id],
            )
            tasks.append(review_task)
        
        return tasks

    async def _execute_tasks(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        """Execute a list of tasks using the appropriate agents."""
        results = {}
        
        for task in tasks:
            # Check dependencies
            if task.dependencies:
                logger.info(f"Task {task.task_id} has dependencies: {task.dependencies}")
            
            # Find an available agent for this role
            agents = self.agent_registry.get(task.agent_role, [])
            if not agents:
                logger.warning(f"No agents available for role {task.agent_role}")
                results[task.task_id] = {
                    "status": "no_agent_available",
                    "role": task.agent_role.value,
                }
                continue
            
            # Use the first available agent (could implement load balancing)
            agent = agents[0]
            
            logger.info(f"Assigning task {task.task_id} to agent {agent.agent_id}")
            
            # Execute the task
            task.status = AgentStatus.WORKING
            task_result = await agent.process_task(task.description, task.parameters)
            task.status = AgentStatus.COMPLETED
            
            results[task.task_id] = task_result
        
        # Return the final result (from the last task)
        if tasks:
            return results.get(tasks[-1].task_id, {})
        return {}
