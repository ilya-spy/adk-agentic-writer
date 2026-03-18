# ADK Agentic Writer -- Architecture

## Overview

Multi-agent content production system built on Google's Agent Development Kit (ADK).
Generates structured interactive content (quizzes, stories, quest games, simulations)
through composable agent pipelines with LLM-powered orchestration.

## Directory Structure

```
src/adk_agentic_writer/
  formats/          # Content format specifications (self-contained)
    base.py         # FormatSpec + ParamSpec dataclasses
    quiz.py         # Quiz format: schema, prompts, sample, params
    story.py        # Branched narrative format
    game.py         # Quest game format
    simulation.py   # Web simulation format
    __init__.py     # FORMAT_REGISTRY, get_format(), list_formats()

  agents/           # ADK agent factories and coordinator
    ideator.py      # create_ideator() -> LlmAgent (output_key=ideation_result)
    writer_agents.py# create_writer(FormatSpec) -> LlmAgent (output_key=draft_content)
    reviewer.py     # create_reviewer() -> LlmAgent (output_key=review_result)
    refiner.py      # create_refiner() -> LlmAgent (output_key=draft_content)
    coordinator.py  # Coordinator service wrapping all agents + InMemoryRunners
    base.py         # Legacy BaseADKAgent (backward compat)
    writer.py       # Legacy WriterAgent (backward compat)
    validator.py    # Legacy ValidatorAgent (backward compat)

  workflows/        # Deterministic agent compositions
    write_review.py # SequentialAgent: Writer -> Reviewer
    refinement_loop.py  # SequentialAgent: Writer -> LoopAgent(Reviewer, Refiner)
    publish.py      # SequentialAgent: Ideator -> Writer -> LoopAgent(Reviewer, Refiner)
    tools.py        # exit_loop tool for breaking LoopAgent cycles

  backend/
    api.py          # FastAPI application with endpoints

  models/           # Pydantic data models
    agent_models.py # AgentTask, AgentConfig, AgentRole
    content_models.py # Quiz, BranchedNarrative, QuestGame, WebSimulation

  tasks/            # Task definitions with content_types aliases
    content_tasks.py    # GENERATE_QUIZ, GENERATE_STORY, etc.
    editorial_tasks.py  # REVIEW_CONTENT, VALIDATE_CONTENT, REFINE_CONTENT

  formats/          # Content type specifications
  utils/            # Logging, proxy, response parsing, schema helpers

frontend/public/
  index.html        # Landing page
  showcase.html     # Interactive content generation UI

tests/
  test_core.py      # Offline tests for formats, tasks, schemas, workflows
```

## Agent Architecture

```
User/API
  |
  v
Coordinator (Python service)
  |-- ideate()   -> IdeatorAgent (LlmAgent, output_key=ideation_result)
  |-- generate() -> WriterAgent  (LlmAgent per format, output_key=draft_content)
  |-- review()   -> ReviewerAgent (LlmAgent, output_key=review_result)
  |-- refine()   -> RefinerAgent  (LlmAgent, output_key=draft_content)
  |-- publish()  -> generate -> review -> refine (conditional loop)
```

### Workflow Compositions (ADK native)

- **WriteReview**: `SequentialAgent([Writer, Reviewer])`
- **WriteAndRefine**: `SequentialAgent([Writer, LoopAgent([Reviewer, Refiner])])`
- **PublishPipeline**: `SequentialAgent([Ideator, Writer, LoopAgent([Reviewer, Refiner])])`

The Refiner agent in loops has an `exit_loop` tool that calls
`tool_context.actions.escalate = True` to break the cycle when quality is sufficient.

## Format System

Each content type is defined by a `FormatSpec` in `formats/`:

- **name**: canonical identifier ("quiz", "story", "game", "simulation")
- **model_class**: Pydantic model for validation (Quiz, BranchedNarrative, etc.)
- **parameter_specs**: user-facing parameters with types and defaults
- **schema_description**: JSON schema text for LLM instructions
- **sample_output**: example JSON for few-shot prompting
- **writer_prompt / reviewer_prompt / refiner_prompt**: stage-specific prompt templates
- **aliases**: alternative names for discovery ("trivia" -> quiz)

The `FORMAT_REGISTRY` provides lookup by name or alias.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/content-types` | List formats with parameters |
| POST | `/ideate` | Run ideation agent |
| POST | `/generate` | Generate content for a format |
| POST | `/review` | Review content with LLM |
| POST | `/refine` | Refine content based on feedback |
| POST | `/publish` | Full pipeline: generate -> review -> refine |
| GET | `/health` | Health check |

## State Flow

```
ideation_result -> writer prompt -> draft_content -> review_result -> refined draft_content
```

ADK agents use `output_key` to store results in session state.
Instructions reference state variables with `{variable_name}` syntax.

## Key Design Decisions

1. **Format-first**: All content type metadata lives in `formats/`, not scattered across agents.
2. **Factory functions**: Agents are created via `create_*(...)` factories, not subclasses.
3. **Dual execution**: Coordinator provides direct methods (generate, review, etc.) and
   ADK workflow compositions (SequentialAgent, LoopAgent) for different use cases.
4. **Schema validation fallback**: `reviewer.schema_validate()` provides fast local
   validation when LLM review fails.
