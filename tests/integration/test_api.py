"""Integration tests for the API."""

import pytest
from fastapi.testclient import TestClient

from adk_agentic_writer.backend.api import app


@pytest.fixture(scope="module")
def client():
    """Create a test client with lifespan events."""
    with TestClient(app) as c:
        yield c


def test_root_endpoint(client: TestClient) -> None:
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "ADK Agentic Writer API"
    assert data["status"] == "operational"


def test_health_endpoint(client: TestClient) -> None:
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_content_types_endpoint(client: TestClient) -> None:
    """Test getting available content types."""
    response = client.get("/content-types")
    assert response.status_code == 200
    data = response.json()
    assert "content_types" in data
    assert "quiz" in data["content_types"]
    assert "quest_game" in data["content_types"]


def test_list_agents_endpoint(client: TestClient) -> None:
    """Test listing agents."""
    response = client.get("/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) > 0


def test_generate_quiz_endpoint(client: TestClient) -> None:
    """Test generating a quiz."""
    response = client.post(
        "/generate",
        json={
            "content_type": "quiz",
            "topic": "Python programming",
            "parameters": {"num_questions": 3},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content_type"] == "quiz"
    assert "content" in data
    assert "agents_involved" in data
