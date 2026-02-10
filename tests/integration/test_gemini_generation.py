"""End-to-end Gemini team generation tests via the API.

Tests quiz and story generation through the full API → coordinator → writer pipeline
using the Gemini team (requires GOOGLE_API_KEY).

Usage:
    GOOGLE_API_KEY=your_key pytest tests/integration/test_gemini_generation.py -v
"""

import os

import pytest
from fastapi.testclient import TestClient

from adk_agentic_writer.backend.api import app

requires_key = pytest.mark.skipif(
    not os.environ.get("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set — skipping Gemini generation tests",
)


@pytest.fixture(scope="module")
def client():
    """Create a test client with lifespan events."""
    with TestClient(app) as c:
        yield c


@requires_key
class TestGeminiQuizGeneration:
    """End-to-end quiz generation through Gemini team API."""

    def test_quiz_basic(self, client: TestClient):
        """Generate a small quiz and verify structure."""
        response = client.post(
            "/generate",
            json={
                "team": "gemini",
                "content_type": "quiz",
                "topic": "Python basics",
                "parameters": {"num_questions": 3, "difficulty": "medium"},
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "completed", (
            f"Generation failed: {result.get('content', {}).get('error', 'unknown')}"
        )

        content = result["content"]["content"]
        assert "title" in content
        assert "questions" in content

        questions = content["questions"]
        assert len(questions) >= 3, f"Expected >= 3 questions, got {len(questions)}"

        for i, q in enumerate(questions):
            assert "question" in q, f"Question {i} missing 'question' field"
            assert "options" in q, f"Question {i} missing 'options'"
            assert "correct_answer" in q, f"Question {i} missing 'correct_answer'"
            assert len(q["options"]) >= 2, f"Question {i} has fewer than 2 options"
            assert 0 <= q["correct_answer"] < len(q["options"]), (
                f"Question {i} correct_answer={q['correct_answer']} out of range"
            )

    def test_quiz_has_tiers_and_scores(self, client: TestClient):
        """Quiz should contain questions with tier and matching scores."""
        response = client.post(
            "/generate",
            json={
                "team": "gemini",
                "content_type": "quiz",
                "topic": "World geography",
                "parameters": {"num_questions": 6, "difficulty": "hard"},
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "completed"

        content = result["content"]["content"]
        questions = content["questions"]

        # Each question should have a score >= 1 and a tier field
        for i, q in enumerate(questions):
            assert q.get("score", 0) >= 1, (
                f"Question {i} missing or zero score"
            )
            assert q.get("tier"), (
                f"Question {i} missing tier field"
            )

    @pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
    def test_quiz_always_has_all_three_tiers(self, client: TestClient, difficulty):
        """All 3 scoring tiers (low/mid/high) must appear regardless of difficulty."""
        response = client.post(
            "/generate",
            json={
                "team": "gemini",
                "content_type": "quiz",
                "topic": "World history",
                "parameters": {"num_questions": 6, "difficulty": difficulty},
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "completed"

        content = result["content"]["content"]
        questions = content["questions"]
        tier_score = {"low": 1, "mid": 2, "high": 3}

        actual_tiers = {q["tier"] for q in questions}
        assert actual_tiers >= {"low", "mid", "high"}, (
            f"difficulty={difficulty}: expected all 3 tiers, got {actual_tiers}"
        )

        # Verify score matches tier
        for i, q in enumerate(questions):
            expected_score = tier_score.get(q["tier"])
            assert q["score"] == expected_score, (
                f"Q{i} tier={q['tier']} should have score={expected_score}, "
                f"got {q['score']}"
            )

    def test_quiz_passing_score(self, client: TestClient):
        """Passing score should exist and be a positive number.

        The 55-80% guideline is enforced via prompt; the backend only logs
        a warning if the LLM deviates, so we keep the test non-strict.
        """
        response = client.post(
            "/generate",
            json={
                "team": "gemini",
                "content_type": "quiz",
                "topic": "Basic math",
                "parameters": {"num_questions": 3, "difficulty": "easy"},
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "completed"

        content = result["content"]["content"]
        questions = content["questions"]
        total_points = sum(q.get("score", 1) for q in questions)
        passing = content.get("passing_score", 0)

        # Must have a positive passing score
        assert isinstance(passing, (int, float)) and passing > 0, (
            f"passing_score should be positive, got {passing}"
        )
        # Must not exceed total points
        assert passing <= total_points, (
            f"passing_score={passing} exceeds total_points={total_points}"
        )
        # Soft check: warn (but don't fail) if outside ideal range
        pct = passing / total_points if total_points else 0
        if not (0.55 <= pct <= 0.80):
            import warnings
            warnings.warn(
                f"passing_score={passing}/{total_points} ({pct:.0%}) "
                "outside ideal 55-80% range"
            )


@requires_key
class TestGeminiStoryGeneration:
    """End-to-end story generation through Gemini team API."""

    def test_story_basic(self, client: TestClient):
        """Generate a branched narrative and verify structure."""
        response = client.post(
            "/generate",
            json={
                "team": "gemini",
                "content_type": "branched_narrative",
                "topic": "A magical forest adventure",
                "parameters": {"num_nodes": 3},
            },
        
        )

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "completed", (
            f"Generation failed: {result.get('content', {}).get('error', 'unknown')}"
        )

        content = result["content"]["content"]
        assert "title" in content
        assert "nodes" in content

        nodes = content["nodes"]
        assert len(nodes) >= 2, f"Expected >= 2 nodes, got {len(nodes)}"

        # At least one node should have branches (non-ending)
        has_branching = any(
            len(n.get("branches", [])) > 0
            for n in (nodes.values() if isinstance(nodes, dict) else nodes)
        )
        assert has_branching, "Story has no branching nodes"

        # At least one ending node
        has_ending = any(
            n.get("is_ending", False)
            for n in (nodes.values() if isinstance(nodes, dict) else nodes)
        )
        assert has_ending, "Story has no ending nodes"
