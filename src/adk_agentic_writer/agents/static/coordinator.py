"""Coordinator agent that orchestrates the multi-agent system using workflows.

Implements: AgentProtocol
Uses: Workflows from workflows/ package
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from ...models.agent_models import AgentRole, AgentStatus, AgentTask
from ...models.content_models import ContentType
from ...workflows import SequentialAgentWorkflow, SequentialEditorialWorkflow
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """Coordinator agent that orchestrates content generation using workflows.
    
    Implements:
    - AgentProtocol: process_task, update_status, get_state
    
    Uses:
    - SequentialAgentWorkflow: For multi-agent pipelines
    - SequentialEditorialWorkflow: For content generation → review pipelines
    """

    def __init__(self, agent_id: str = "coordinator", config: Dict[str, Any] | None = None):
        """Initialize the coordinator agent."""
        super().__init__(agent_id, AgentRole.COORDINATOR, config)
        self.active_tasks: Dict[str, AgentTask] = {}
        self.agent_registry: Dict[AgentRole, List[BaseAgent]] = {}

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the coordinator.
        
        Args:
            agent: Agent to register
        """
        if agent.role not in self.agent_registry:
            self.agent_registry[agent.role] = []
        self.agent_registry[agent.role].append(agent)
        logger.info(f"Registered agent {agent.agent_id} with role {agent.role}")

    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a content generation request by coordinating other agents via workflows.

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
        
        # Get agents for the workflow
        writer = self._get_agent_for_content_type(content_type)
        reviewer = self._get_agent_by_role(AgentRole.REVIEWER)
        
        if not writer:
            await self.update_status(AgentStatus.ERROR)
            return {
                "error": f"No agent available for content type {content_type}",
                "content_type": content_type,
            }
        
        # Create and execute workflow
        if reviewer:
            # Use Sequential Editorial Workflow: Generate → Review
            workflow = SequentialEditorialWorkflow(
                name=f"{content_type}_pipeline",
                stages=[writer, reviewer]
            )
        else:
            # Just use the writer
            workflow = SequentialAgentWorkflow(
                name=f"{content_type}_generation",
                agents=[writer]
            )
        
        # Execute workflow
        result = await workflow.execute({
            "task_description": task_description,
            "parameters": parameters,
        })
        
        await self.update_status(AgentStatus.COMPLETED)
        
        return {
            "content_type": content_type,
            "content": result,
            "agents_involved": [writer.agent_id] + ([reviewer.agent_id] if reviewer else []),
            "workflow_used": workflow.name,
        }

    def _get_agent_for_content_type(self, content_type: ContentType) -> Optional[BaseAgent]:
        """Get the appropriate agent for a content type.
        
        Args:
            content_type: Type of content to generate
            
        Returns:
            Agent capable of generating that content type, or None
        """
        role_mapping = {
            ContentType.QUIZ: AgentRole.QUIZ_WRITER,
            ContentType.QUEST_GAME: AgentRole.GAME_DESIGNER,
            ContentType.BRANCHED_NARRATIVE: AgentRole.STORY_WRITER,
            ContentType.WEB_SIMULATION: AgentRole.SIMULATION_DESIGNER,
        }
        
        role = role_mapping.get(content_type)
        if role:
            return self._get_agent_by_role(role)
        return None

    def _get_agent_by_role(self, role: AgentRole) -> Optional[BaseAgent]:
        """Get an agent by role.
        
        Args:
            role: Agent role to find
            
        Returns:
            First available agent with that role, or None
        """
        agents = self.agent_registry.get(role, [])
        return agents[0] if agents else None

    def get_registered_agents(self) -> Dict[AgentRole, List[str]]:
        """Get a summary of registered agents.
        
        Returns:
            Dict mapping roles to lists of agent IDs
        """
        return {
            role: [agent.agent_id for agent in agents]
            for role, agents in self.agent_registry.items()
        }


__all__ = ["CoordinatorAgent"]
