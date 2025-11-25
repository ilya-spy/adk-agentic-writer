"""Agent runtime for instantiating and orchestrating agents, teams, and workflows.

The runtime is responsible for:
- Creating agent instances from configurations
- Building teams from team metadata
- Linking agents with workflows
- Managing agent lifecycle and communication
"""

import logging
from typing import Any, Dict, List, Optional, Type

from ..agents.base_agent import BaseAgent
from ..agents.stateful_agent import StatefulAgent
from ..models.agent_models import (
    AgentConfig,
    AgentTask,
    TeamMetadata,
    WorkflowMetadata,
    WorkflowScope,
)
from ..workflows.base_workflow import Workflow

logger = logging.getLogger(__name__)


class AgentRuntime:
    """Runtime for managing agents, teams, and workflows.

    The runtime provides:
    - Agent instantiation from configurations
    - Team assembly from metadata
    - Workflow registration and execution
    - Agent communication and coordination
    """

    def __init__(self, agent_class: Type[BaseAgent] = StatefulAgent):
        """Initialize the agent runtime.

        Args:
            agent_class: Agent class to use for instantiation (default: StatefulAgent)
        """
        self.agent_class = agent_class
        self.agents: Dict[str, BaseAgent] = {}
        self.teams: Dict[str, TeamMetadata] = {}
        self.workflows: Dict[str, Workflow] = {}

        logger.info(f"Initialized AgentRuntime with agent class {agent_class.__name__}")

    def create_agent(
        self,
        agent_id: str,
        config: AgentConfig,
        workflows: Optional[List[WorkflowMetadata]] = None,
    ) -> BaseAgent:
        """Create an agent instance from configuration.

        Args:
            agent_id: Unique identifier for the agent
            config: Agent configuration
            workflows: Optional workflows for the agent

        Returns:
            Created agent instance
        """
        # Create agent instance
        if self.agent_class == StatefulAgent:
            agent = self.agent_class(agent_id, config, workflows)
        elif issubclass(self.agent_class, StatefulAgent):
            # For StatefulAgent subclasses (like StaticQuizWriterAgent)
            agent = self.agent_class(agent_id)
        else:
            # For other agent classes, use basic initialization
            agent = self.agent_class(
                agent_id=agent_id,
                role=config.role,
                config=config.model_dump(),
            )

        # Register agent
        self.agents[agent_id] = agent
        logger.info(f"Created agent {agent_id} with role {config.role}")

        return agent

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent instance or None
        """
        return self.agents.get(agent_id)

    def create_team(
        self,
        team_metadata: TeamMetadata,
        agent_configs: Dict[str, AgentConfig],
    ) -> List[BaseAgent]:
        """Create a team of agents from metadata.

        Args:
            team_metadata: Team metadata with roles
            agent_configs: Mapping of role names to agent configurations

        Returns:
            List of created agent instances
        """
        team_agents = []

        # Create agents for each role in the team
        for idx, role in enumerate(team_metadata.roles):
            # Get config for this role
            config = agent_configs.get(role)
            if not config:
                logger.warning(
                    f"No config found for role {role} in team {team_metadata.name}"
                )
                continue

            # Create unique agent ID
            agent_id = f"{team_metadata.name}_{role}_{idx}"

            # Create agent
            agent = self.create_agent(agent_id, config)
            team_agents.append(agent)

            # Track agent in team metadata
            if agent_id not in team_metadata.agent_ids:
                team_metadata.agent_ids.append(agent_id)

        # Register team
        self.teams[team_metadata.name] = team_metadata
        logger.info(f"Created team {team_metadata.name} with {len(team_agents)} agents")

        return team_agents

    def get_team(self, team_name: str) -> Optional[TeamMetadata]:
        """Get team metadata by name.

        Args:
            team_name: Team name

        Returns:
            Team metadata or None
        """
        return self.teams.get(team_name)

    def get_team_agents(self, team_name: str) -> List[BaseAgent]:
        """Get all agents in a team.

        Args:
            team_name: Team name

        Returns:
            List of agents in the team
        """
        team = self.get_team(team_name)
        if not team:
            return []

        return [
            self.agents[agent_id]
            for agent_id in team.agent_ids
            if agent_id in self.agents
        ]

    def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow.

        Args:
            workflow: Workflow instance to register
        """
        self.workflows[workflow.name] = workflow
        logger.info(
            f"Registered workflow {workflow.name} "
            f"(pattern: {workflow.pattern}, scope: {workflow.scope})"
        )

    def get_workflow(self, workflow_name: str) -> Optional[Workflow]:
        """Get workflow by name.

        Args:
            workflow_name: Workflow name

        Returns:
            Workflow instance or None
        """
        return self.workflows.get(workflow_name)

    def list_workflows(self, scope: Optional[WorkflowScope] = None) -> List[str]:
        """List available workflows, optionally filtered by scope.

        Args:
            scope: Optional scope filter

        Returns:
            List of workflow names
        """
        if scope:
            return [name for name, wf in self.workflows.items() if wf.scope == scope]
        return list(self.workflows.keys())

    async def execute_workflow(
        self,
        workflow_name: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a registered workflow.

        Args:
            workflow_name: Name of workflow to execute
            input_data: Input data for the workflow

        Returns:
            Workflow execution result
        """
        workflow = self.get_workflow(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow {workflow_name} not found")

        logger.info(f"Executing workflow {workflow_name}")
        result = await workflow.execute(input_data)
        logger.info(f"Workflow {workflow_name} completed")

        return result

    async def execute_task_with_agent(
        self,
        agent_id: str,
        task: AgentTask,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a task with a specific agent.

        Args:
            agent_id: Agent to execute the task
            task: Task to execute
            parameters: Optional task parameters

        Returns:
            Task execution result
        """
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        logger.info(f"Agent {agent_id} executing task {task.task_id}")
        result = await agent.process_task(task, parameters)

        return result

    def create_workflow_with_team(
        self,
        workflow: Workflow,
        team_name: str,
    ) -> Workflow:
        """Link a workflow with a team of agents.

        Args:
            workflow: Workflow instance
            team_name: Name of team to use

        Returns:
            Workflow with agents assigned
        """
        team_agents = self.get_team_agents(team_name)
        if not team_agents:
            logger.warning(f"No agents found for team {team_name}")
            return workflow

        # Assign team agents to workflow
        workflow.agents = team_agents

        logger.info(
            f"Linked workflow {workflow.name} with team {team_name} "
            f"({len(team_agents)} agents)"
        )

        return workflow

    def list_agents(self) -> List[str]:
        """List all registered agent IDs.

        Returns:
            List of agent IDs
        """
        return list(self.agents.keys())

    def list_teams(self) -> List[str]:
        """List all registered team names.

        Returns:
            List of team names
        """
        return list(self.teams.keys())

    def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get the current state of an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent state as dictionary or None
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return None

        return agent.get_state().model_dump()

    def reset_agent(self, agent_id: str) -> bool:
        """Reset an agent's state.

        Args:
            agent_id: Agent identifier

        Returns:
            True if reset successful, False otherwise
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        # Reset state if agent is stateful
        if isinstance(agent, StatefulAgent):
            agent.clear_variables()
            agent.state.completed_tasks.clear()
            agent.state.current_task = None
            logger.info(f"Reset agent {agent_id}")
            return True

        return False

    def shutdown(self) -> None:
        """Shutdown the runtime and cleanup resources."""
        logger.info(
            f"Shutting down runtime with {len(self.agents)} agents, "
            f"{len(self.teams)} teams, {len(self.workflows)} workflows"
        )
        self.agents.clear()
        self.teams.clear()
        self.workflows.clear()


__all__ = ["AgentRuntime"]
