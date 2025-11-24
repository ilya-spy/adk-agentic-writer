# Teams

Pre-configured agent teams with specialized roles and agent pools.

## Architecture

```
Workflow → Tasks → Teams → Agents
```

**Flow**: Workflows orchestrate → Tasks setup context → Teams provide configs → Agents instantiate

**Formula**: `Team = Roles + Configs + Pools`

---

## Content Team (`content_team.py`)

Specialized writers for different content types.

| Role | Purpose | Temp |
|------|---------|------|
| `CONTENT_WRITER` | General editorial content | 0.7 |
| `STORY_WRITER` | Interactive narratives | 0.85 |
| `QUIZ_WRITER` | Educational quizzes | 0.7 |
| `GAME_WRITER` | Quest-based games | 0.75 |
| `SIMULATION_WRITER` | Web simulations | 0.65 |

**Pools**: `STORY_WRITERS_POOL` (3), `QUIZ_WRITERS_POOL` (2), `GAME_WRITERS_POOL` (2), `SIMULATION_WRITERS_POOL` (1)

---

## Editorial Team (`editorial_team.py`)

Review and refinement specialists.

| Role | Purpose | Temp |
|------|---------|------|
| `EDITORIAL_REVIEWER` | Quality assurance | 0.5 |
| `EDITORIAL_REFINER` | Content improvement | 0.6 |

**Pools**: `EDITORIAL_REVIEWERS_POOL` (2), `EDITORIAL_REFINERS_POOL` (2), `EDITORIAL_GROUP_POOL` (2)

---

## Usage

```python
from adk_agentic_writer.teams import STORY_WRITER, STORY_WRITERS_POOL
from adk_agentic_writer.agents import BaseAgent

# Instantiate agent from config
story_agent = BaseAgent(config=STORY_WRITER)

# Use pool in workflow
workflow = ParallelEditorialWorkflow(
    name="story_variants",
    team_pool=STORY_WRITERS_POOL,
    generator=story_agent
)
```

---

## Connections

- **Agents**: AgentConfig → BaseAgent instantiation with role-specific settings
- **Tasks**: Tasks specify `agent_role`, matched to team pool agents
- **Workflows**: Orchestrate task execution using agent pools for parallel work

---

## Key Principles

✅ **Role-Based** - Specialized by content type  
✅ **Configurable** - Temperature tuned per role  
✅ **Pooled** - Multi-agent collaboration  
✅ **Type-Safe** - Enum-based roles
