"""Test configuration and fixtures."""

import pytest


@pytest.fixture
def sample_topic() -> str:
    """Provide a sample topic for testing."""
    return "Ancient Rome"


@pytest.fixture
def sample_parameters() -> dict:
    """Provide sample parameters for testing."""
    return {
        "num_questions": 5,
        "difficulty": "medium",
    }
