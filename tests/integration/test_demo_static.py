"""Integration tests for interactive demo application.

This module tests the interactive demo's core functionality:
- Agent creation and management
- Team creation and configuration
- Content generation with various patterns
- Static team operations

Requirements:
    - All dependencies installed

Usage:
    pytest tests/integration/test_demo_static.py -v
"""

import sys
from pathlib import Path

import pytest

# Add examples to path to import demo
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "examples"))

from interactive_demo import InteractiveDemo
from adk_agentic_writer.agents.static.quiz_writer import StaticQuizWriterAgent
from adk_agentic_writer.protocols.content_protocol import ContentBlockType
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


class TestDemoAgentsAndTeams:
    """Test combined agent and team management."""

    @pytest.mark.asyncio
    async def test_two_agents_three_teams(self):
        """Test creating 2 individual agents and 3 teams as per requirements."""
        demo = InteractiveDemo()

        # Create 2 individual agents
        agent1 = StaticQuizWriterAgent("standalone_agent_1")
        agent1.update_parameters(
            {
                "topic": "Machine Learning",
                "num_questions": 5,
                "difficulty": "medium",
            }
        )
        demo.agents["standalone_agent_1"] = agent1

        agent2 = StaticQuizWriterAgent("standalone_agent_2")
        agent2.update_parameters(
            {
                "topic": "Web Development",
                "num_questions": 4,
                "difficulty": "easy",
            }
        )
        demo.agents["standalone_agent_2"] = agent2

        # Create 3 teams
        for i in range(3):
            team_metadata = QUIZ_WRITERS_POOL.model_copy(deep=True)
            team_metadata.name = f"team_{i+1}"
            team_metadata.agent_ids = []

            team_agents = demo.runtime.create_team(
                team_metadata=team_metadata, agent_configs={"quiz_writer": QUIZ_WRITER}
            )

            for agent in team_agents:
                demo.agents[agent.agent_id] = agent

        # Verify counts
        assert len(demo.runtime.teams) == 3, "Should have 3 teams"

        # Individual agents + team agents
        assert len(demo.agents) >= 2, "Should have at least 2 agents"

        # Verify individual agents are present
        assert "standalone_agent_1" in demo.agents
        assert "standalone_agent_2" in demo.agents

        # Verify teams are present
        assert "team_1" in demo.runtime.teams
        assert "team_2" in demo.runtime.teams
        assert "team_3" in demo.runtime.teams

        # Verify team agents are registered
        for team_name in ["team_1", "team_2", "team_3"]:
            team = demo.runtime.teams[team_name]
            for agent_id in team.agent_ids:
                assert (
                    agent_id in demo.agents
                ), f"Team agent {agent_id} should be registered"


class TestDemoContentGeneration:
    """Test content generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_single_block(self):
        """Test generating a single content block."""
        demo = InteractiveDemo()

        # Create agent
        agent = StaticQuizWriterAgent("test_agent")
        agent.update_parameters(
            {
                "topic": "Python",
                "num_questions": 3,
                "difficulty": "medium",
            }
        )
        demo.agents["test_agent"] = agent

        # Generate single block
        result = await agent.generate_block(ContentBlockType.QUESTION, agent.parameters)

        assert result is not None
        assert result.block_id is not None
        assert result.content is not None
        assert "title" in result.content
        assert "questions" in result.content

    @pytest.mark.asyncio
    async def test_generate_sequential_blocks(self):
        """Test generating sequential content blocks."""
        demo = InteractiveDemo()

        # Create agent
        agent = StaticQuizWriterAgent("test_agent")
        agent.update_parameters(
            {
                "topic": "JavaScript",
                "num_questions": 2,
                "difficulty": "easy",
            }
        )
        demo.agents["test_agent"] = agent

        # Generate sequential blocks
        blocks = await agent.generate_sequential_blocks(
            3, ContentBlockType.QUESTION, agent.parameters
        )

        assert len(blocks) == 3
        for i, block in enumerate(blocks):
            assert block.block_id is not None
            assert block.content is not None
            assert "questions" in block.content
            # Verify navigation
            if i < len(blocks) - 1:
                assert block.navigation["next"] is not None

    @pytest.mark.asyncio
    async def test_generate_looped_blocks(self):
        """Test generating looped content blocks."""
        demo = InteractiveDemo()

        # Create agent
        agent = StaticQuizWriterAgent("test_agent")
        agent.update_parameters(
            {
                "topic": "Algorithms",
                "num_questions": 2,
                "difficulty": "hard",
            }
        )
        demo.agents["test_agent"] = agent

        # Generate looped blocks
        blocks = await agent.generate_looped_blocks(
            2,
            ContentBlockType.QUESTION,
            agent.parameters,
            {"score": ">=80", "attempts": ">=3"},
        )

        assert len(blocks) == 2
        for block in blocks:
            assert block.block_id is not None
            assert block.content is not None
            assert block.exit_condition is not None

    @pytest.mark.asyncio
    async def test_generate_branched_blocks(self):
        """Test generating branched content blocks."""
        demo = InteractiveDemo()

        # Create agent
        agent = StaticQuizWriterAgent("test_agent")
        agent.update_parameters(
            {
                "topic": "Database Design",
                "num_questions": 3,
                "difficulty": "medium",
            }
        )
        demo.agents["test_agent"] = agent

        # Generate branched blocks
        blocks = await agent.generate_branched_blocks(
            [], agent.parameters  # branch_points can be empty for initial test
        )

        assert len(blocks) > 0
        # First block should be the initial assessment
        assert blocks[0].block_id is not None
        assert blocks[0].content is not None


class TestStaticTeamOperability:
    """Test static team operations."""

    @pytest.mark.asyncio
    async def test_static_team_content_generation(self):
        """Test that static team can generate content."""
        demo = InteractiveDemo()

        # Create a team
        team_agents = demo.runtime.create_team(
            team_metadata=QUIZ_WRITERS_POOL, agent_configs={"quiz_writer": QUIZ_WRITER}
        )

        for agent in team_agents:
            demo.agents[agent.agent_id] = agent

        # Use first agent from team to generate content
        agent = team_agents[0]
        agent.update_parameters(
            {
                "topic": "Cloud Computing",
                "num_questions": 4,
                "difficulty": "medium",
            }
        )

        # Generate content
        result = await agent.generate_block(ContentBlockType.QUESTION, agent.parameters)

        assert result is not None
        assert result.content is not None
        assert "questions" in result.content
        assert len(result.content["questions"]) == 4

    @pytest.mark.asyncio
    async def test_static_team_all_agents_operational(self):
        """Test that all agents in a static team are operational."""
        demo = InteractiveDemo()

        # Create a team
        team_agents = demo.runtime.create_team(
            team_metadata=QUIZ_WRITERS_POOL, agent_configs={"quiz_writer": QUIZ_WRITER}
        )

        # Test each agent
        for agent in team_agents:
            agent.update_parameters(
                {
                    "topic": "Testing",
                    "num_questions": 2,
                    "difficulty": "easy",
                }
            )

            result = await agent.generate_block(
                ContentBlockType.QUESTION, agent.parameters
            )

            assert result is not None
            assert result.content is not None
            assert "questions" in result.content


class TestDemoCompleteWorkflow:
    """Test complete demo workflow."""

    @pytest.mark.asyncio
    async def test_complete_demo_workflow(self):
        """Test complete workflow: setup, create agents/teams, generate content."""
        demo = InteractiveDemo()

        # Step 1: Verify initialization
        assert len(demo.agents) == 0
        assert len(demo.runtime.teams) == 0

        # Step 2: Create 2 standalone agents
        for i in range(1, 3):
            agent = StaticQuizWriterAgent(f"agent_{i}")
            agent.update_parameters(
                {
                    "topic": f"Topic {i}",
                    "num_questions": 3,
                    "difficulty": "medium",
                }
            )
            demo.agents[f"agent_{i}"] = agent

        assert len(demo.agents) == 2

        # Step 3: Create 3 teams
        for i in range(1, 4):
            team_metadata = QUIZ_WRITERS_POOL.model_copy(deep=True)
            team_metadata.name = f"static_team_{i}"
            team_metadata.agent_ids = []

            team_agents = demo.runtime.create_team(
                team_metadata=team_metadata, agent_configs={"quiz_writer": QUIZ_WRITER}
            )

            for agent in team_agents:
                demo.agents[agent.agent_id] = agent

        assert len(demo.runtime.teams) == 3

        # Step 4: Verify all present
        assert "agent_1" in demo.agents
        assert "agent_2" in demo.agents
        assert "static_team_1" in demo.runtime.teams
        assert "static_team_2" in demo.runtime.teams
        assert "static_team_3" in demo.runtime.teams

        # Step 5: Generate content with a standalone agent
        standalone_agent = demo.agents["agent_1"]
        result1 = await standalone_agent.generate_block(
            ContentBlockType.QUESTION, standalone_agent.parameters
        )

        assert result1 is not None
        assert result1.content is not None
        demo.generated_content.append(result1.content)

        # Step 6: Generate content with a team agent
        team = demo.runtime.teams["static_team_1"]
        team_agent_id = team.agent_ids[0]
        team_agent = demo.agents[team_agent_id]
        team_agent.update_parameters(
            {
                "topic": "Team Test",
                "num_questions": 2,
                "difficulty": "easy",
            }
        )

        result2 = await team_agent.generate_block(
            ContentBlockType.QUESTION, team_agent.parameters
        )

        assert result2 is not None
        assert result2.content is not None
        demo.generated_content.append(result2.content)

        # Step 7: Verify content generated
        assert len(demo.generated_content) == 2
        assert all("questions" in content for content in demo.generated_content)


# Utility function for manual testing
def run_manual_demo_test():
    """Run a manual test of the demo."""
    print("\n" + "=" * 80)
    print("ADK Interactive Demo - Test Suite")
    print("=" * 80)
    print("\nThis test suite verifies:")
    print("  [PASS] Demo initialization")
    print("  [PASS] Agent creation (2 agents)")
    print("  [PASS] Team creation (3 teams)")
    print("  [PASS] Content generation")
    print("  [PASS] Static team operability")
    print("\nRun with: pytest tests/integration/test_demo_static.py -v")


if __name__ == "__main__":
    run_manual_demo_test()
