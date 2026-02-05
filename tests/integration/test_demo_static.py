"""Integration tests for interactive demo application.

Tests the interactive demo's core functionality:
- Agent creation and management
- Team creation and configuration
"""

import sys
from pathlib import Path

import pytest

# Add examples to path to import demo
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "examples"))

from interactive_demo import InteractiveDemo
from adk_agentic_writer.agents.static.writer import StaticQuizWriterAgent
from adk_agentic_writer.teams.content_team import QUIZ_WRITER, QUIZ_WRITERS_POOL


class TestDemoInitialization:
    """Test demo initialization and setup."""

    @pytest.mark.asyncio
    async def test_demo_initialization(self):
        """Test demo initializes correctly."""
        demo = InteractiveDemo()

        assert demo.runtime is not None
        assert demo.agents == {}
        assert demo.generated_content == []
        assert demo.running is True
        assert len(demo.runtime.agents) == 0
        assert len(demo.runtime.teams) == 0


class TestDemoAgentCreation:
    """Test agent creation functionality."""

    @pytest.mark.asyncio
    async def test_create_single_agent(self):
        """Test creating a single agent."""
        demo = InteractiveDemo()

        # Create agent programmatically
        agent_id = "quiz_agent_1"
        agent = StaticQuizWriterAgent(agent_id)
        agent.update_parameters(
            {
                "topic": "Python Programming",
                "num_questions": 5,
                "difficulty": "medium",
                "passing_score": 70,
            }
        )
        demo.agents[agent_id] = agent

        assert len(demo.agents) == 1
        assert agent_id in demo.agents
        assert demo.agents[agent_id].parameters["topic"] == "Python Programming"
        assert demo.agents[agent_id].parameters["num_questions"] == 5

    @pytest.mark.asyncio
    async def test_create_two_agents(self):
        """Test creating two agents with different configurations."""
        demo = InteractiveDemo()

        # Create first agent
        agent1_id = "quiz_agent_1"
        agent1 = StaticQuizWriterAgent(agent1_id)
        agent1.update_parameters(
            {
                "topic": "Python Programming",
                "num_questions": 5,
                "difficulty": "medium",
            }
        )
        demo.agents[agent1_id] = agent1

        # Create second agent
        agent2_id = "quiz_agent_2"
        agent2 = StaticQuizWriterAgent(agent2_id)
        agent2.update_parameters(
            {
                "topic": "Data Science",
                "num_questions": 3,
                "difficulty": "hard",
            }
        )
        demo.agents[agent2_id] = agent2

        # Verify both agents exist
        assert len(demo.agents) == 2
        assert agent1_id in demo.agents
        assert agent2_id in demo.agents
        assert demo.agents[agent1_id].parameters["topic"] == "Python Programming"
        assert demo.agents[agent2_id].parameters["topic"] == "Data Science"


class TestDemoTeamCreation:
    """Test team creation functionality."""

    @pytest.mark.asyncio
    async def test_create_single_team(self):
        """Test creating a single team."""
        demo = InteractiveDemo()

        # Create team using runtime
        team_agents = demo.runtime.create_team(
            team_metadata=QUIZ_WRITERS_POOL, agent_configs={"quiz_writer": QUIZ_WRITER}
        )

        # Register team agents
        for agent in team_agents:
            demo.agents[agent.agent_id] = agent

        assert len(demo.runtime.teams) == 1
        assert QUIZ_WRITERS_POOL.name in demo.runtime.teams
        assert len(team_agents) > 0
        assert len(demo.agents) == len(team_agents)

    @pytest.mark.asyncio
    async def test_create_three_teams(self):
        """Test creating three separate teams."""
        demo = InteractiveDemo()

        # Create three teams with unique metadata copies
        teams_created = []
        for i in range(3):
            # Create a copy of the team metadata with unique name
            team_metadata = QUIZ_WRITERS_POOL.model_copy(deep=True)
            team_metadata.name = f"quiz_team_{i+1}"
            team_metadata.agent_ids = []  # Reset agent IDs

            team_agents = demo.runtime.create_team(
                team_metadata=team_metadata, agent_configs={"quiz_writer": QUIZ_WRITER}
            )

            teams_created.append((team_metadata.name, team_agents))

            # Register team agents
            for agent in team_agents:
                demo.agents[agent.agent_id] = agent

        # Verify all teams created
        assert len(demo.runtime.teams) == 3
        assert "quiz_team_1" in demo.runtime.teams
        assert "quiz_team_2" in demo.runtime.teams
        assert "quiz_team_3" in demo.runtime.teams

        # Verify all agents registered
        total_agents = sum(len(agents) for _, agents in teams_created)
        assert len(demo.agents) == total_agents


class TestDemoContentGeneration:
    """Test content generation via coordinator."""

    @pytest.mark.asyncio
    async def test_generate_quiz_via_coordinator(self):
        """Test generating quiz via coordinator."""
        from adk_agentic_writer.agents.static import CoordinatorAgent

        coordinator = CoordinatorAgent()

        # Use convenience method
        result = await coordinator.generate_content(
            content_type="quiz",
            topic="Python",
            num_questions=3,
        )

        assert result is not None
        assert result["status"] == "completed"
        assert "content" in result
        assert "title" in result["content"]
        assert "questions" in result["content"]
        assert len(result["content"]["questions"]) == 3

    @pytest.mark.asyncio
    async def test_generate_block_directly(self):
        """Test generating a block using ContentProtocol."""
        from adk_agentic_writer.models.content_models import ContentBlockType

        agent = StaticQuizWriterAgent("test_agent")

        # Generate a single block via protocol
        block = await agent.generate_block(
            ContentBlockType.QUESTION,
            {"topic": "Python", "difficulty": "medium"},
        )

        assert block is not None
        assert block.block_type == ContentBlockType.QUESTION
        assert "question" in block.content
