# Testing Guide

**Single source of truth for all testing documentation.**

## Quick Start

```bash
# 1. Install dependencies
pip install pytest pytest-asyncio
pip install -r requirements.txt

# 2. Run tests
pytest

# 3. Set API key for integration tests (optional)
export GOOGLE_API_KEY="your-key"
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Fast tests (no API)
│   ├── test_agent_models.py
│   ├── test_base_agent.py
│   ├── test_content_models.py
│   └── test_quiz_writer.py
└── integration/             # Slow tests (needs API key)
    ├── test_adk.py         # ADK + Gemini (8 tests)
    └── test_api.py         # API endpoints (5 tests)
```

**Total: 26 tests** (13 unit + 13 integration)

## Running Tests

```bash
# All tests
pytest

# Fast tests only (no API calls)
pytest tests/unit/
pytest -m "not slow"

# Integration tests (requires GOOGLE_API_KEY)
pytest tests/integration/

# Specific test
pytest tests/integration/test_adk.py::test_gemini_client_initialization -v

# With coverage
pytest --cov=src/adk_agentic_writer
```

## Test Explorer (VS Code/Cursor)

### Setup (One-Time)

1. **Select Python Interpreter**
   - `Ctrl+Shift+P` → "Python: Select Interpreter"
   - Choose: `./venv/Scripts/python.exe`

2. **Open Test Explorer**
   - Click beaker icon in sidebar
   - Or `Ctrl+Shift+P` → "Test: Focus on Test Explorer View"

3. **Discover Tests**
   - Click refresh icon
   - Or `Ctrl+Shift+P` → "Python: Discover Tests"

### Troubleshooting

**Tests not showing?**
1. Reload window: `Ctrl+Shift+P` → "Developer: Reload Window"
2. Check interpreter is selected
3. Check output: View → Output → "Python Test Log"
4. Verify: `python -m pytest --collect-only`

**Import errors?**
```bash
pip install -e .
```

## Configuration Files

All configured automatically:
- `pytest.ini` - Pytest settings
- `.vscode/settings.json` - Test Explorer config
- `.vscode/launch.json` - Debug configs

## Test Markers

```python
@pytest.mark.slow          # Slow test (API calls)
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.asyncio       # Async test
```

Filter by marker:
```bash
pytest -m "not slow"       # Skip slow tests
pytest -m integration      # Only integration tests
```

## Writing Tests

### Unit Test
```python
def test_quiz_creation():
    quiz = Quiz(title="Test", description="Test", questions=[], passing_score=70)
    assert quiz.title == "Test"
```

### Integration Test
```python
@pytest.mark.asyncio
@pytest.mark.slow
async def test_quiz_generation(workflow_manager):
    result = await workflow_manager.process_task(
        task_description="Create a quiz",
        parameters={"content_type": ContentType.QUIZ, "topic": "Python"}
    )
    assert result is not None
```

## Fixtures

**Shared** (`conftest.py`):
- `sample_topic` - "Ancient Rome"
- `sample_parameters` - Default test params

**Integration** (`test_adk.py`):
- `api_key` - Gets `GOOGLE_API_KEY` from env
- `gemini_client` - Creates GeminiClient
- `workflow_manager` - Creates GeminiWorkflowManager

## API Key Setup

Integration tests require `GOOGLE_API_KEY`:

```bash
# Option 1: Environment variable
export GOOGLE_API_KEY="your-key"

# Option 2: .env file (root directory)
echo "GOOGLE_API_KEY=your-key" > .env

# Get your key at: https://aistudio.google.com/apikey
```

Tests will **skip** (not fail) if API key is missing.

## CI/CD

```yaml
# Run unit tests (always)
pytest tests/unit/

# Run integration tests (if API key available)
pytest tests/integration/
env:
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

## Debug Configurations

Available in `.vscode/launch.json`:
- **Python: Pytest Current File** - Debug open test file
- **Python: Pytest All** - Debug all tests
- **Python: FastAPI** - Debug API server

Press `F5` to start debugging.

## Common Commands

```bash
# Quick test run (fast tests only)
pytest tests/unit/ -v

# Full test run (with API key)
export GOOGLE_API_KEY="key" && pytest -v

# Test with output
pytest -v -s

# Test with coverage report
pytest --cov=src/adk_agentic_writer --cov-report=html

# Collect tests without running
pytest --collect-only

# Run last failed tests
pytest --lf

# Stop on first failure
pytest -x
```

## Best Practices

✅ **DO:**
- Write unit tests for all new code
- Mark slow tests with `@pytest.mark.slow`
- Use fixtures for common setup
- Keep tests focused and simple
- Run `pytest -m "not slow"` for quick feedback

❌ **DON'T:**
- Make API calls in unit tests
- Commit API keys
- Write tests that depend on each other
- Test implementation details

## Support

- **Test not found?** Check `pytest --collect-only`
- **Import error?** Run `pip install -e .`
- **API error?** Set `GOOGLE_API_KEY`
- **VS Code issues?** Reload window

---

**26 tests ready to run!** 🧪
