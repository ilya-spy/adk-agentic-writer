# Architecture

## Overview

Task-driven multi-agent content production system built on Google's Agent Development Kit (ADK).

```
src/adk_agentic_writer/
├── formats/              # Content type specifications
│   ├── base.py           # FormatSpec, ParamSpec dataclasses
│   ├── quiz.py           # Quiz format (flavors: quiz, trivia, test)
│   ├── story.py          # Branched narrative (flavors: story, narrative, adventure)
│   ├── game.py           # Quest game (flavors: game, quest, rpg)
│   └── simulation.py     # Web simulation (flavors: simulation, simulator)
├── agents/               # Agent services
│   ├── base.py           # BaseAgentService (runner pool, task registry)
│   ├── ideator.py        # IdeatorAgentService → IDEATE task
│   ├── writer.py         # WriterAgentService → WRITE task
│   ├── reviewer.py       # ReviewerAgentService → REVIEW task + schema_validate
│   ├── refiner.py        # RefinerAgentService → REFINE task
│   ├── publisher.py      # PublisherAgentService → PUBLISH task (pipeline)
│   └── coordinator.py    # CoordinatorService (routes tasks to sub-agents)
├── tasks/                # Task definitions
│   ├── content_tasks.py  # IDEATE, WRITE
│   └── editorial_tasks.py# REVIEW, REFINE, PUBLISH
├── workflows/            # ADK SequentialAgent / LoopAgent compositions
│   ├── tools.py          # exit_loop function tool
│   ├── refine.py         # Writer → LoopAgent(Reviewer, Refiner)
│   └── publish.py        # Ideator → Writer → LoopAgent
├── backend/
│   ├── api.py            # FastAPI app with task-driven endpoints
│   └── runtime.py        # RuntimeStore (agents, services, outputs)
├── models/               # Pydantic data models
└── utils/                # Helpers (response parsing, logging, proxy)
```

## Key Concepts

### Flavors
Each `FormatSpec` declares a list of `flavors` (e.g. quiz → quiz, trivia, test).
The registry creates a separate `FormatSpec` clone per flavor with the `flavor` field set.
`get_format("trivia")` returns a FormatSpec with `flavor="trivia"`, `name="quiz"`.

### Unified Tasks
Five tasks: `IDEATE`, `WRITE`, `REVIEW`, `REFINE`, `PUBLISH`.
Each has an `output_key` (e.g. `draft_content`, `review_result`) used to store results in `RuntimeStore`.

### Agent Services
Each agent service inherits `BaseAgentService`, registers its tasks, and exposes `prepare_task`, `run_prompt`, and `process_task`.
The `CoordinatorService` collects all sub-agent tasks and routes calls to the correct service.

### API
Single generic endpoint: `POST /task/{task_id}` with `{parameters: {...}}`.
Discovery: `GET /tasks`, `GET /content-types`, `GET /outputs`.
`RuntimeStore` holds output keys between task invocations.

### Workflows
ADK `SequentialAgent` and `LoopAgent` compositions for multi-step pipelines.
Used internally by `PublisherAgentService` and available for programmatic use.
