"""Coordinator agent for orchestrating content generation teams.

This agent:
- Implements ContentProtocol
- Uses ParallelEditorialWorkflow and SequentialEditorialWorkflow
- Orchestrates content teams (quiz, story, game, simulation writers)
- Provides access to content teams for Producer agent
"""

import logging
from typing import Any, Dict, List, Optional

from ...agents.stateful_agent import StatefulAgent
from ...models.agent_models import AgentStatus, AgentTask
from ...protocols.content_protocol import ContentBlock, ContentBlockType, ContentPattern
from ...runtime.agent_runtime import AgentRuntime
from ...teams.content_team import (
    CONTENT_WRITER,
    GAME_WRITER,
    GAME_WRITERS_POOL,
    QUIZ_WRITER,
    QUIZ_WRITERS_POOL,
    SIMULATION_WRITER,
    SIMULATION_WRITERS_POOL,
    STORY_WRITER,
    STORY_WRITERS_POOL,
    ContentRole,
)
from ...workflows.editorial_workflows import (
    ParallelEditorialWorkflow,
    SequentialEditorialWorkflow,
)

# Import actual agent implementations
from .game_designer import GameDesignerAgent
from .quiz_writer import StaticQuizWriterAgent
from .simulation_designer import SimulationDesignerAgent
from .story_writer import StoryWriterAgent

logger = logging.getLogger(__name__)

# Content type to agent class mapping
CONTENT_TYPE_MAP = {
    "quiz": StaticQuizWriterAgent,
    "branched_narrative": StoryWriterAgent,
    "quest_game": GameDesignerAgent,
    "web_simulation": SimulationDesignerAgent,
}

# Content type to role mapping
ROLE_MAP = {
    "quiz": ContentRole.QUIZ_WRITER,
    "branched_narrative": ContentRole.STORY_WRITER,
    "quest_game": ContentRole.GAME_WRITER,
    "web_simulation": ContentRole.SIMULATION_WRITER,
}


class CoordinatorAgent(StatefulAgent):
    """Coordinator agent for orchestrating content generation.

    Implements:
    - AgentProtocol: process_task, update_status
    - ContentProtocol: generate_block, generate_sequential_blocks, etc.

    Uses AgentRuntime to manage content teams and delegates generation to specialist agents.
    """

    def __init__(self, agent_id: str = "coordinator"):
        """Initialize coordinator agent with runtime and teams."""
        super().__init__(
            agent_id=agent_id,
            config=CONTENT_WRITER,
        )

        # Initialize runtime
        self.runtime = AgentRuntime()

        # Setup content teams
        self._setup_teams()

        logger.info(f"Initialized CoordinatorAgent {agent_id} with runtime and teams")

    def _setup_teams(self) -> None:
        """Setup content generation teams using runtime."""
        # Register agent configs
        configs = {
            ContentRole.QUIZ_WRITER.value: QUIZ_WRITER,
            ContentRole.STORY_WRITER.value: STORY_WRITER,
            ContentRole.GAME_WRITER.value: GAME_WRITER,
            ContentRole.SIMULATION_WRITER.value: SIMULATION_WRITER,
        }

        # Create teams
        self.runtime.create_team(QUIZ_WRITERS_POOL, configs)
        self.runtime.create_team(STORY_WRITERS_POOL, configs)
        self.runtime.create_team(GAME_WRITERS_POOL, configs)
        self.runtime.create_team(SIMULATION_WRITERS_POOL, configs)

        # Create specialist agent instances
        self.quiz_agent = StaticQuizWriterAgent("quiz_writer")
        self.story_agent = StoryWriterAgent("story_writer")
        self.game_agent = GameDesignerAgent("game_designer")
        self.simulation_agent = SimulationDesignerAgent("simulation_designer")

        logger.info("Setup content teams: quiz, story, game, simulation")

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute task based on task_id."""
        context = self.prepare_task_context(task)

        # Route to appropriate ContentProtocol method
        if task.task_id == "generate_block":
            block_type = ContentBlockType(context.get("block_type", "custom"))
            block = await self.generate_block(block_type, context)
            return block.content
        elif task.task_id == "generate_sequential_blocks":
            num_blocks = context.get("num_blocks", 3)
            block_type = ContentBlockType(context.get("block_type", "custom"))
            blocks = await self.generate_sequential_blocks(
                num_blocks, block_type, context
            )
            return {"blocks": [b.content for b in blocks]}
        elif task.task_id == "generate_branched_blocks":
            branch_points = context.get("branch_points", [])
            blocks = await self.generate_branched_blocks(branch_points, context)
            return {"blocks": [b.content for b in blocks]}
        elif task.task_id == "generate_with_workflow":
            # add route to generate with parallel or sequential workflow
            workflow_type = context.get("workflow_type", "parallel")
            content_types = context.get(
                "content_types", ["quiz", "story", "game", "simulation"]
            )
            return await self.generate_with_workflow(
                workflow_type, content_types, context
            )
        else:
            # Default: route to content generation
            content_type = context.get("content_type", "quiz")
            return await self._generate_content(content_type, context)

    # ========================================================================
    # Public API for other agents (Producer, Editor)
    # ========================================================================

    async def generate_content(
        self, content_type: str, topic: str, **parameters
    ) -> Dict[str, Any]:
        """Generate content of specified type.

        Public API method for other agents to request content generation.

        Args:
            content_type: Type of content (quiz, branched_narrative, quest_game, web_simulation)
            topic: Content topic
            **parameters: Additional parameters for content generation

        Returns:
            Generated content dictionary
        """
        logger.info(f"Generating {content_type} content: {topic}")

        # Get appropriate agent
        agent = self._get_agent_for_type(content_type)
        if not agent:
            raise ValueError(f"Unknown content type: {content_type}")

        # Set parameters
        params = {"topic": topic, **parameters}
        agent.update_parameters(params)

        # Generate content using agent's internal method
        if content_type == "quiz":
            num_questions = parameters.get("num_questions", 5)
            difficulty = parameters.get("difficulty", "medium")
            result = await agent._generate_quiz_data(topic, num_questions, difficulty)
        elif content_type == "branched_narrative":
            genre = parameters.get("genre", "fantasy")
            num_nodes = parameters.get("num_nodes", 7)
            result = await agent._generate_story_data(topic, genre, num_nodes)
        elif content_type == "quest_game":
            num_nodes = parameters.get("num_nodes", 7)
            difficulty = parameters.get("difficulty", "medium")
            result = await agent._generate_game_data(topic, num_nodes, difficulty)
        elif content_type == "web_simulation":
            num_variables = parameters.get("num_variables", 5)
            complexity = parameters.get("complexity", "medium")
            result = await agent._generate_simulation_data(
                topic, num_variables, complexity
            )
        else:
            raise ValueError(f"Unknown content type: {content_type}")

        await agent.update_status(AgentStatus.COMPLETED)

        return {
            "content_type": content_type,
            "topic": topic,
            "content": result,
            "status": "completed",
        }

    def get_team_agents(self, team_name: str) -> List[Any]:
        """Get agents from a specific team.

        Args:
            team_name: Team name (e.g., "quiz_writers_pool")

        Returns:
            List of agent instances
        """
        return self.runtime.get_team_agents(team_name)

    def get_runtime(self) -> AgentRuntime:
        """Get the runtime instance for direct access.

        Returns:
            AgentRuntime instance
        """
        return self.runtime

    async def generate_with_workflow(
        self, workflow_type: str, content_types: List[str], topic: str, **parameters
    ) -> Dict[str, Any]:
        """Generate content using specified workflow pattern.

        Args:
            workflow_type: "parallel" or "sequential"
            content_types: List of content types to generate (e.g., ["quiz", "story"])
            topic: Content topic
            **parameters: Additional parameters for content generation

        Returns:
            Workflow execution result with keys from Workflow.execute()
        """
        logger.info(f"Generating {workflow_type} content: {content_types} for {topic}")

        # Get agents for requested content types
        agents = [self._get_agent_for_type(ct) for ct in content_types]
        agents = [a for a in agents if a is not None]

        if not agents:
            raise ValueError(f"No agents found for content types: {content_types}")

        # Create workflow based on type
        if workflow_type == "parallel":
            workflow = ParallelEditorialWorkflow(
                name=f"parallel_{'-'.join(content_types)}",
                generators=agents,
                selection_strategy=parameters.get("merge_strategy", "combine"),
            )
        elif workflow_type == "sequential":
            workflow = SequentialEditorialWorkflow(
                name=f"sequential_{'-'.join(content_types)}",
                stages=agents,
            )
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

        # Prepare input data for workflow
        input_data = {
            "parameters": {
                "topic": topic,
                **parameters,
            }
        }

        # Execute workflow
        result = await workflow.execute(input_data)

        return {
            "workflow_type": workflow_type,
            "content_types": content_types,
            "topic": topic,
            "result": result,
            "status": "completed",
        }

    # ========================================================================
    # ContentProtocol Implementation
    # ========================================================================

    async def generate_block(
        self,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        previous_blocks: Optional[List[ContentBlock]] = None,
    ) -> ContentBlock:
        """Generate a single content block by delegating to appropriate agent."""
        content_type = context.get("content_type", "quiz")
        topic = context.get("topic", "general")

        agent = self._get_agent_for_type(content_type)
        if not agent:
            raise ValueError(f"No agent found for content type: {content_type}")

        # Delegate to agent's generate_block
        return await agent.generate_block(block_type, context, previous_blocks)

    async def generate_sequential_blocks(
        self,
        num_blocks: int,
        block_type: ContentBlockType,
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate sequential blocks by delegating to appropriate agent."""
        content_type = context.get("content_type", "quiz")

        agent = self._get_agent_for_type(content_type)
        if not agent:
            raise ValueError(f"No agent found for content type: {content_type}")

        # Delegate to agent's generate_sequential_blocks
        return await agent.generate_sequential_blocks(num_blocks, block_type, context)

    async def generate_looped_blocks(
        self,
        num_blocks: int,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        exit_condition: Dict[str, Any],
        allow_back: bool = True,
    ) -> List[ContentBlock]:
        """Generate looped blocks by delegating to appropriate agent."""
        content_type = context.get("content_type", "quiz")

        agent = self._get_agent_for_type(content_type)
        if not agent:
            raise ValueError(f"No agent found for content type: {content_type}")

        # Delegate to agent's generate_looped_blocks
        return await agent.generate_looped_blocks(
            num_blocks, block_type, context, exit_condition, allow_back
        )

    async def generate_branched_blocks(
        self,
        branch_points: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate branched blocks by delegating to appropriate agent."""
        content_type = context.get("content_type", "quest_game")

        agent = self._get_agent_for_type(content_type)
        if not agent:
            raise ValueError(f"No agent found for content type: {content_type}")

        # Delegate to agent's generate_branched_blocks
        return await agent.generate_branched_blocks(branch_points, context)

    async def generate_conditional_blocks(
        self,
        blocks_config: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate conditional blocks by delegating to appropriate agent."""
        content_type = context.get("content_type", "quiz")

        agent = self._get_agent_for_type(content_type)
        if not agent:
            raise ValueError(f"No agent found for content type: {content_type}")

        # Delegate to agent's generate_conditional_blocks
        return await agent.generate_conditional_blocks(blocks_config, context)

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _generate_content(
        self, content_type: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate content by routing to appropriate agent."""
        topic = context.get("topic", "general")
        return await self.generate_content(content_type, topic, **context)

    def _get_agent_for_type(self, content_type: str) -> Optional[Any]:
        """Get the appropriate agent for a content type."""
        agent_map = {
            "quiz": self.quiz_agent,
            "branched_narrative": self.story_agent,
            "quest_game": self.game_agent,
            "web_simulation": self.simulation_agent,
        }
        return agent_map.get(content_type)


__all__ = ["CoordinatorAgent"]
