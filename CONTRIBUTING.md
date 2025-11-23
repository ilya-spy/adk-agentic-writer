# Contributing to ADK Agentic Writer

Thank you for your interest in contributing to ADK Agentic Writer! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/adk-agentic-writer.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest`
6. Commit your changes: `git commit -m 'Add some feature'`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Development Setup

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linters
ruff check src/ tests/
mypy src/

# Format code
black src/ tests/
ruff check --fix src/ tests/
```

## Code Style

- Follow PEP 8 for Python code
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Run `black` and `ruff` before committing

## Testing

- Write unit tests for new functionality
- Maintain or improve code coverage
- Run the full test suite before submitting PRs

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update tests to cover new functionality
3. Ensure all tests pass
4. Update documentation as needed
5. Request review from maintainers

## Adding New Agents

To add a new agent:

1. Create a new file in `src/adk_agentic_writer/agents/`
2. Inherit from `BaseAgent`
3. Implement the `process_task` method
4. Register in `agents/__init__.py`
5. Add tests in `tests/unit/`

## Adding New Content Types

To add a new content type:

1. Define the model in `src/adk_agentic_writer/models/content_models.py`
2. Create a specialized agent for the content type
3. Update the coordinator to handle the new type
4. Add API endpoints in `backend/api.py`
5. Update static HTML UI in `frontend/public/` to support the new type
6. Add tests in `tests/unit/` and `tests/integration/`

## Questions?

Feel free to open an issue for any questions or concerns.
