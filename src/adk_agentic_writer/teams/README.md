# Teams

Pre-configured agent pools and prompt templates for content generation and editorial workflows.

## Overview

Teams provide `AgentConfig` instances for agent instantiation and centralized prompt templates used by both static and Gemini agents:

```
Workflow → Tasks → Teams (configs + prompts) → Agents
```

## Content Team (`content_team.py`)

### Agent Configurations

| Config | Role | Purpose |
|--------|------|---------|
| `CONTENT_WRITER` | WRITER | General content |
| `STORY_WRITER` | WRITER | Narratives |
| `QUIZ_WRITER` | WRITER | Quizzes |
| `GAME_WRITER` | DESIGNER | Games |
| `SIMULATION_WRITER` | DESIGNER | Simulations |

### Prompt Templates

`content_team.py` also defines prompt templates used by the Gemini team:

- **`QUIZ_WRITER.generation_prompt`**: Instructions for quiz generation including difficulty/tier rules, scoring, and output format
- **`quiz_question_complete`**: Per-question generation prompt with tier and score fields
- **`STORY_WRITER.generation_prompt`**: Instructions for branched narrative generation with node structure

These prompts distinguish between:
- **Overall quiz difficulty** (easy/medium/hard) — governs topic complexity
- **Per-question scoring tiers** (low/mid/high → 1/2/3 pts) — governs point distribution

**Note**: Static team uses unified `WriterAgent` and `DesignerAgent` that handle multiple content types via task routing. Gemini team uses these prompts with the LLM.

## Editorial Team (`editorial_team.py`)

Review and refinement specialists:

| Config | Role | Purpose |
|--------|------|---------|
| `EDITORIAL_REVIEWER` | REVIEWER | Quality review |
| `EDITORIAL_REFINER` | REFINER | Content improvement |

## Agent Pools

Pre-defined pools for parallel workflows:

- `STORY_WRITERS_POOL` — Multiple story writers
- `QUIZ_WRITERS_POOL` — Multiple quiz writers
- `EDITORIAL_REVIEWERS_POOL` — Review team

## Usage

```python
from adk_agentic_writer.teams import STORY_WRITER, QUIZ_WRITERS_POOL
from adk_agentic_writer.agents import ContentWriterAgent

# Create agent from config
agent = ContentWriterAgent(
    agent_id="story_1",
    config=STORY_WRITER
)

# Use pool for parallel generation
for config in QUIZ_WRITERS_POOL.configs:
    agent = ContentWriterAgent(f"quiz_{i}", config)
```

## Key Principles

- **Role-Based**: Configs tuned per content type
- **Prompt-Centralized**: LLM prompt templates defined alongside agent configs
- **Pooled**: Multi-agent for parallel work
- **Configurable**: Temperature, max_tokens per role
