# Testing Guide

**Single source of truth for all testing documentation.**

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run all tests
pytest

# 3. Set API key for live LLM integration tests (optional)
export GOOGLE_API_KEY="your-key"
```

## Test Structure

```
tests/
├── conftest.py                        # Shared fixtures
├── unit/                              # Fast tests (no API)
│   ├── test_agent_models.py           # AgentTask, AgentConfig, AgentRole
│   ├── test_base_agent.py             # BaseAgent behavior
│   ├── test_content_models.py         # Quiz, QuizQuestion (tier/score), StoryNode
│   └── test_quiz_writer.py            # Static quiz writer, question generation
└── integration/                       # Slower tests (some need API key)
    ├── test_adk.py                    # ADK initialization + Gemini client
    ├── test_all_content_types.py      # All 15 content type aliases
    ├── test_demo_static.py            # Static team demo flows
    ├── test_gemini_generation.py      # Live Gemini quiz/story (tier enforcement, passing score)
    ├── test_gemini_writer.py          # Gemini writer prompts, post-processing, mocked generation
    └── test_google_connectivity.py    # Google API connectivity checks
```

**Total: 113 tests** (unit + integration, including parametrized variants)

## What's Tested

| Area | Coverage |
|------|----------|
| Content models | Quiz difficulty, QuizQuestion tier/score, StoryNode branches |
| Quiz scoring | 3-tier enforcement (low/mid/high), passing score validation |
| Story branches | Fuzzy key normalization, node navigation |
| Gemini writer | Prompt templates, post-processing, field normalization |
| Static writer | Template generation, all content types |
| API endpoints | Generate, tasks, content-types, health |
| LLM refusal | Refusal detection patterns |
| Parameter variations | Difficulty levels, option counts (parametrized) |

## Running Tests

```bash
# All tests
pytest -v

# Unit tests only (fast, no API calls)
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Skip slow LLM tests (no API key needed)
pytest -m "not slow"

# Specific test file
pytest tests/integration/test_gemini_generation.py -v

# With coverage
pytest --cov=src/adk_agentic_writer --cov-report=html
```

## Test Markers

```python
@pytest.mark.slow          # Slow test (live API calls)
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.asyncio       # Async test
```

Filter by marker:
```bash
pytest -m "not slow"       # Skip slow tests
pytest -m integration      # Only integration tests
```

## API Key Setup

Some integration tests require `GOOGLE_API_KEY` for live LLM generation:

```bash
# Environment variable
export GOOGLE_API_KEY="your-key"

# Or .env file (root directory)
echo "GOOGLE_API_KEY=your-key" > .env

# Get your key at: https://aistudio.google.com/apikey
```

Tests will **skip** (not fail) if API key is missing.

## Writing Tests

### Unit Test (content models)
```python
def test_quiz_question_tier():
    q = QuizQuestion(question="Q?", options=["A", "B"], correct_answer=0, tier="high", score=3)
    assert q.tier == "high"
    assert q.score == 3

def test_quiz_difficulty():
    quiz = Quiz(title="T", description="D", difficulty="hard", questions=[], passing_score=8)
    assert quiz.difficulty == "hard"
```

### Integration Test (Gemini generation)
```python
@pytest.mark.asyncio
@pytest.mark.slow
async def test_quiz_has_all_tiers(gemini_writer):
    result = await gemini_writer.generate_quiz("Science", difficulty="easy", num_questions=6)
    tiers = {q.tier for q in result.questions}
    assert tiers >= {"low", "mid", "high"}
```

## Common Commands

```bash
# Quick unit tests
pytest tests/unit/ -v

# Full run with API key
GOOGLE_API_KEY="key" pytest -v

# Verbose with stdout
pytest -v -s

# Collect tests without running
pytest --collect-only

# Run last failed
pytest --lf

# Stop on first failure
pytest -x
```

## CI/CD

```yaml
# Unit tests (always)
pytest tests/unit/

# Integration tests (if API key available)
pytest tests/integration/
env:
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

## IDE Setup (VS Code / Cursor)

1. Select Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter" → `./venv/Scripts/python.exe`
2. Open Test Explorer: beaker icon in sidebar
3. Discover tests: click refresh icon

**Troubleshooting**: `pip install -e .` for import errors, `Ctrl+Shift+P` → "Developer: Reload Window" for stale state.

---

**113 tests across unit and integration suites.**
