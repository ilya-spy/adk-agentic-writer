"""Integration tests for all content types with static team."""

import pytest
from fastapi.testclient import TestClient

from adk_agentic_writer.backend.api import app
from adk_agentic_writer.agents.static import (
    CoordinatorAgent,
    StaticQuizWriterAgent,
    StoryWriterAgent,
    GameDesignerAgent,
    SimulationDesignerAgent,
)


@pytest.fixture(scope="module")
def client():
    """Create a test client with lifespan events."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def coordinator():
    """Create a coordinator (agents auto-registered via runtime)."""
    return CoordinatorAgent()


class TestStaticQuizGeneration:
    """Test quiz generation."""

    @pytest.mark.asyncio
    async def test_quiz_direct(self, coordinator):
        """Test quiz generation directly."""
        result = await coordinator.generate_content(
            "quiz", topic="Python", num_questions=3
        )

        content = result["content"]

        assert "title" in content
        assert "questions" in content
        assert len(content["questions"]) == 3
        assert all("question" in q for q in content["questions"])
        assert all("options" in q for q in content["questions"])

    def test_quiz_api(self, client: TestClient):
        """Test quiz generation via API."""
        response = client.post(
            "/generate",
            json={
                "team": "static",
                "content_type": "quiz",
                "topic": "JavaScript",
                "parameters": {"num_questions": 5},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["team"] == "static"
        assert data["content_type"] == "quiz"

        # Extract content
        content = data["content"]["content"]
        assert "questions" in content
        assert len(content["questions"]) == 5


class TestStaticStoryGeneration:
    """Test branched narrative generation."""

    @pytest.mark.asyncio
    async def test_story_direct(self, coordinator):
        """Test story generation directly."""
        result = await coordinator.generate_content(
            "branched_narrative", topic="Adventure", num_nodes=5
        )

        content = result["content"]

        assert "title" in content
        assert "nodes" in content
        assert "start_node" in content
        assert len(content["nodes"]) > 0

    def test_story_api(self, client: TestClient):
        """Test story generation via API."""
        response = client.post(
            "/generate",
            json={
                "team": "static",
                "content_type": "branched_narrative",
                "topic": "Mystery",
                "parameters": {"num_nodes": 5},
            },
        )

        assert response.status_code == 200
        data = response.json()
        content = data["content"]["content"]
        assert "nodes" in content
        assert "start_node" in content


class TestStaticGameGeneration:
    """Test quest game generation."""

    @pytest.mark.asyncio
    async def test_game_direct(self, coordinator):
        """Test game generation directly."""
        result = await coordinator.generate_content(
            "quest_game", topic="Fantasy Quest", num_nodes=5
        )

        content = result["content"]

        assert "title" in content
        assert "nodes" in content
        assert "victory_conditions" in content

    def test_game_api(self, client: TestClient):
        """Test game generation via API."""
        response = client.post(
            "/generate",
            json={
                "team": "static",
                "content_type": "quest_game",
                "topic": "Space Quest",
                "parameters": {},
            },
        )

        assert response.status_code == 200
        data = response.json()
        content = data["content"]["content"]
        assert "nodes" in content
        assert "title" in content
        assert "victory_conditions" in content


class TestStaticSimulationGeneration:
    """Test web simulation generation."""

    @pytest.mark.asyncio
    async def test_simulation_direct(self, coordinator):
        """Test simulation generation directly."""
        result = await coordinator.generate_content(
            "web_simulation", topic="Physics", num_variables=4
        )

        content = result["content"]

        assert "title" in content
        assert "variables" in content
        assert len(content["variables"]) > 0

    def test_simulation_api(self, client: TestClient):
        """Test simulation generation via API."""
        response = client.post(
            "/generate",
            json={
                "team": "static",
                "content_type": "web_simulation",
                "topic": "Chemistry",
                "parameters": {},
            },
        )

        assert response.status_code == 200
        data = response.json()
        content = data["content"]["content"]
        assert "variables" in content
        assert "title" in content


class TestContentQuality:
    """Test content quality across all types."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "content_type,topic,check_field",
        [
            ("quiz", "Math", "questions"),
            ("branched_narrative", "Sci-Fi", "nodes"),
            ("quest_game", "RPG", "nodes"),
            ("web_simulation", "Biology", "variables"),
        ],
    )
    async def test_content_not_empty(
        self, coordinator, content_type, topic, check_field
    ):
        """Test that generated content is not empty."""
        # Use generate_content for all types
        if content_type == "quiz":
            result = await coordinator.generate_content(
                "quiz", topic=topic, num_questions=3
            )
        elif content_type == "branched_narrative":
            result = await coordinator.generate_content(
                "branched_narrative", topic=topic, num_nodes=5
            )
        elif content_type == "quest_game":
            result = await coordinator.generate_content(
                "quest_game", topic=topic, num_nodes=5
            )
        elif content_type == "web_simulation":
            result = await coordinator.generate_content(
                "web_simulation", topic=topic, num_variables=3
            )
        else:
            raise ValueError(f"Unknown content type: {content_type}")

        content = result["content"]

        assert check_field in content
        assert len(content[check_field]) > 0


class TestGenerateWithValidation:
    """Test /generate/with-validation endpoint."""

    def test_quiz_with_validation(self, client: TestClient):
        """Test quiz generation with validation workflow via API."""
        response = client.post(
            "/generate/with-validation",
            json={
                "team": "static",
                "content_type": "quiz",
                "topic": "Python",
                "parameters": {"num_questions": 3},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["team"] == "static"
        assert data["content_type"] == "quiz"

        content = data["content"]
        assert "content" in content  # writer output (named output_key)
        assert "validation_result" in content  # validator output (named output_key)
        assert content["status"] == "validated"

    def test_story_with_validation(self, client: TestClient):
        """Test story generation with validation workflow via API."""
        response = client.post(
            "/generate/with-validation",
            json={
                "team": "static",
                "content_type": "branched_narrative",
                "topic": "Adventure",
                "parameters": {"num_nodes": 3},
            },
        )

        assert response.status_code == 200
        data = response.json()
        content = data["content"]
        assert "content" in content
        assert "validation_result" in content
        assert content["status"] == "validated"

    @pytest.mark.asyncio
    async def test_direct_generate_with_validation(self, coordinator):
        """Test generate_with_validation directly on coordinator."""
        result = await coordinator.generate_with_validation(
            "quiz", topic="Math", num_questions=3
        )

        assert result["status"] == "validated"
        assert "validation_result" in result
        assert "content" in result

    @pytest.mark.asyncio
    async def test_state_variables_after_validation(self, coordinator):
        """Test coordinator.state.variables populated after validation workflow."""
        await coordinator.generate_with_validation(
            "quiz", topic="Science", num_questions=3
        )

        # Coordinator state should have the named output_key results
        assert "content" in coordinator.state.variables
        assert "validation_result" in coordinator.state.variables
        assert coordinator.state.variables["content"] is not None
        assert coordinator.state.variables["validation_result"] is not None

    def test_coordinator_has_team_and_workflow(self):
        """Test coordinator registers validation team and workflow in state."""
        coord = CoordinatorAgent()

        # Team registered
        assert len(coord.state.teams) >= 1
        team = coord.state.teams[0]
        assert team.name == "validation_team"
        assert len(team.agent_ids) == 2

        # Workflow registered
        assert len(coord.state.workflows) >= 1
        wf = coord.state.workflows[0]
        assert wf.name == "generate_validate"
        assert wf.pattern.value == "sequential"

        # Also in model
        assert len(coord.model.teams) >= 1
        assert len(coord.model.workflows) >= 1

    def test_invalid_content_type_with_validation(self, client: TestClient):
        """Test validation endpoint with invalid content type."""
        response = client.post(
            "/generate/with-validation",
            json={
                "team": "static",
                "content_type": "invalid_type",
                "topic": "Test",
                "parameters": {},
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Should return error in content
        assert "error" in str(data["content"]).lower()


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_content_type(self, client: TestClient):
        """Test handling of invalid content type."""
        response = client.post(
            "/generate",
            json={
                "team": "static",
                "content_type": "invalid_type",
                "topic": "Test",
                "parameters": {},
            },
        )

        # System handles gracefully - coordinator returns error in content
        assert response.status_code == 200
        data = response.json()
        # Check if error is reported in content
        assert "error" in str(data).lower() or "content" in data

    def test_missing_parameters(self, client: TestClient):
        """Test handling of missing parameters."""
        response = client.post(
            "/generate",
            json={
                "team": "static",
                "content_type": "quiz",
                # Missing topic
            },
        )

        # Should return validation error
        assert response.status_code == 422
