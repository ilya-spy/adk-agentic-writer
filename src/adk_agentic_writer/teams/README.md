# Teams

Pre-configured agent pools for content generation and editorial workflows.

## Overview

Teams provide `AgentConfig` instances for agent instantiation:

```
Workflow → Tasks → Teams (configs) → Agents
```

## Content Team (`content_team.py`)

Configurations for content-generating agents:

| Config | Role | Purpose |
|--------|------|---------|
| `CONTENT_WRITER` | WRITER | General content |
| `STORY_WRITER` | WRITER | Narratives |
| `QUIZ_WRITER` | WRITER | Quizzes |
| `GAME_WRITER` | DESIGNER | Games |
| `SIMULATION_WRITER` | DESIGNER | Simulations |

**Note**: Static team uses unified `WriterAgent` and `DesignerAgent` that handle multiple content types via task routing.

## Editorial Team (`editorial_team.py`)

Review and refinement specialists:

| Config | Role | Purpose |
|--------|------|---------|
| `EDITORIAL_REVIEWER` | REVIEWER | Quality review |
| `EDITORIAL_REFINER` | REFINER | Content improvement |

## Agent Pools

Pre-defined pools for parallel workflows:

- `STORY_WRITERS_POOL` - Multiple story writers
- `QUIZ_WRITERS_POOL` - Multiple quiz writers
- `EDITORIAL_REVIEWERS_POOL` - Review team

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
- **Pooled**: Multi-agent for parallel work
- **Configurable**: Temperature, max_tokens per role
