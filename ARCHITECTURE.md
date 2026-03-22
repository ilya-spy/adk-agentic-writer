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
│   ├── verifier.py       # VerifierAgentService → VERIFY task (google_search)
│   ├── refiner.py        # RefinerAgentService → REFINE task
│   ├── publisher.py      # PublisherAgentService → PUBLISH task (pipeline)
│   └── coordinator.py    # CoordinatorService (routes tasks to sub-agents)
├── tasks/                # Task definitions
│   ├── content_tasks.py  # IDEATE, WRITE
│   └── editorial_tasks.py# REVIEW, VERIFY, REFINE, PUBLISH
├── workflows/            # ADK workflow compositions
│   ├── tools.py          # exit_loop function tool
│   ├── verify.py         # ParallelAgent(Reviewer, Verifier)
│   ├── refine.py         # LoopAgent(Refiner, Reviewer)
│   └── publish.py        # Ideator → Writer → Parallel → Loop
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
Six tasks: `IDEATE`, `WRITE`, `REVIEW`, `VERIFY`, `REFINE`, `PUBLISH`.
Each has an `output_key` (e.g. `draft_content`, `review_result`, `verification_result`) used to store results in `RuntimeStore`.

### Agent Services
Each agent service inherits `BaseAgentService`, registers its tasks, and exposes `prepare_task`, `run_prompt`, and `process_task`.
The `CoordinatorService` collects all sub-agent tasks and routes calls to the correct service.

### API
Single generic endpoint: `POST /task/{task_id}` with `{parameters: {...}}`.
Discovery: `GET /tasks`, `GET /content-types`, `GET /outputs`.
`RuntimeStore` holds output keys between task invocations.

### Domain (realworld / fictional)
Every request carries a `domain` parameter (`"realworld"` or `"fictional"`) that flows through all agents via `prepare_task` params:

- **Ideator**: suggests fact-grounded topics for realworld, imaginative ones for fictional.
- **Writer**: equipped with `google_search`; realworld writers verify facts via search, fictional writers create freely without search.
- **Reviewer**: penalizes vague/unverifiable claims in realworld; focuses on internal consistency for fictional.
- **Verifier**: rigorously fact-checks all claims for realworld; checks only internal consistency for fictional; performs domain-match detection (flags fictional content marked as realworld and vice versa).
- **Refiner**: uses verification details for realworld corrections; maintains creative freedom for fictional.

The showcase UI provides domain selectors in both the Ideator panel (chips) and Writer panel (dropdown), and propagates domain through all downstream tasks.

### Workflows
ADK `SequentialAgent`, `ParallelAgent`, and `LoopAgent` compositions for multi-step pipelines.
The publish pipeline runs: Ideator -> Writer -> Parallel(Reviewer, Verifier) -> Loop(Refiner, Reviewer).
The writer and verifier both use `google_search` as their sole tool (ADK single-tool-per-agent constraint).
Used internally by `PublisherAgentService` and available for programmatic use.
