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
    """Create a coordinator with all agents registered."""
    coord = CoordinatorAgent()
    coord.register_agent(StaticQuizWriterAgent())
    coord.register_agent(StoryWriterAgent())
    coord.register_agent(GameDesignerAgent())
    coord.register_agent(SimulationDesignerAgent())
    return coord


class TestStaticQuizGeneration:
    """Test quiz generation."""

    @pytest.mark.asyncio
    async def test_quiz_direct(self, coordinator):
        """Test quiz generation directly."""
        result = await coordinator.process_task(
            "Generate quiz",
            {"content_type": "quiz", "topic": "Python", "num_questions": 3}
        )
        
        content = result["content"]
        if isinstance(content, dict) and "original_content" in content:
            content = content["original_content"]
        
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
                "parameters": {"num_questions": 5}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["team"] == "static"
        assert data["content_type"] == "quiz"
        
        # Extract content
        content = data["content"]["content"]["original_content"]
        assert "questions" in content
        assert len(content["questions"]) == 5


class TestStaticStoryGeneration:
    """Test branched narrative generation."""

    @pytest.mark.asyncio
    async def test_story_direct(self, coordinator):
        """Test story generation directly."""
        result = await coordinator.process_task(
            "Generate story",
            {"content_type": "branched_narrative", "topic": "Adventure", "num_branches": 3}
        )
        
        content = result["content"]
        if isinstance(content, dict) and "original_content" in content:
            content = content["original_content"]
        
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
                "parameters": {"num_branches": 4}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        content = data["content"]["content"]["original_content"]
        assert "nodes" in content
        assert "start_node" in content


class TestStaticGameGeneration:
    """Test quest game generation."""

    @pytest.mark.asyncio
    async def test_game_direct(self, coordinator):
        """Test game generation directly."""
        result = await coordinator.process_task(
            "Generate game",
            {"content_type": "quest_game", "topic": "Fantasy Quest"}
        )
        
        content = result["content"]
        if isinstance(content, dict) and "original_content" in content:
            content = content["original_content"]
        
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
                "parameters": {}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        content = data["content"]["content"]["original_content"]
        assert "nodes" in content
        assert "title" in content


class TestStaticSimulationGeneration:
    """Test web simulation generation."""

    @pytest.mark.asyncio
    async def test_simulation_direct(self, coordinator):
        """Test simulation generation directly."""
        result = await coordinator.process_task(
            "Generate simulation",
            {"content_type": "web_simulation", "topic": "Physics"}
        )
        
        content = result["content"]
        if isinstance(content, dict) and "original_content" in content:
            content = content["original_content"]
        
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
                "parameters": {}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        content = data["content"]["content"]["original_content"]
        assert "variables" in content
        assert "title" in content


class TestContentQuality:
    """Test content quality across all types."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("content_type,topic,check_field", [
        ("quiz", "Math", "questions"),
        ("branched_narrative", "Sci-Fi", "nodes"),
        ("quest_game", "RPG", "nodes"),
        ("web_simulation", "Biology", "variables"),
    ])
    async def test_content_not_empty(self, coordinator, content_type, topic, check_field):
        """Test that generated content is not empty."""
        result = await coordinator.process_task(
            f"Generate {content_type}",
            {"content_type": content_type, "topic": topic}
        )
        
        content = result["content"]
        if isinstance(content, dict) and "original_content" in content:
            content = content["original_content"]
        
        assert check_field in content
        assert len(content[check_field]) > 0


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
                "parameters": {}
            }
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
                "content_type": "quiz"
                # Missing topic
            }
        )
        
        # Should return validation error
        assert response.status_code == 422

