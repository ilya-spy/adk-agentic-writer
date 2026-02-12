# Workflows

Task-driven orchestration for content generation.

## Overview

Workflows orchestrate `AgentTask` execution using patterns:

| Pattern | Description | Example |
|---------|-------------|---------|
| SEQUENTIAL | Execute in order | Review → Refine → Finalize |
| PARALLEL | Execute concurrently | Generate variants → Select |
| LOOP | Repeat until condition | Generate → Stream → Repeat |
| CONDITIONAL | Route by condition | Analyze → Apply strategy |

## Content Workflows

### AdaptiveContentWorkflow (LOOP)

Adapts generation based on user behavior:

```
ANALYZE_USER_BEHAVIOR → ADAPT_CONTENT_STRATEGY → GENERATE_ADAPTIVE_BLOCK
```

### StreamingContentWorkflow (LOOP)

Progressive content generation:

```
GENERATE_STREAMING_BLOCK → STREAM_CONTENT_BLOCK
```

## Editorial Workflows

### ValidationEditorialWorkflow

Writer → Validator sequential quality pipeline:

```
[input task] → VALIDATE_CONTENT
```

### ParallelEditorialWorkflow

Generate variants, select best:

```
[GENERATE_VARIANT × 3] → SELECT_BEST_VARIANT
```

### IterativeEditorialWorkflow (LOOP)

Repeated improvement until quality threshold:

```
EVALUATE_CONTENT_QUALITY → REFINE_ITERATIVELY (loop)
```

## Usage

```python
from adk_agentic_writer.workflows import AdaptiveContentWorkflow

workflow = AdaptiveContentWorkflow(
    name="adaptive_learning",
    generator=writer_agent,
    adaptator=analyzer_agent,
    max_iterations=10
)

result = await workflow.execute({
    "topic": "Python basics",
    "user_interactions": user_data
})
```

## Key Principles

- **Task-Driven**: Orchestrate AgentTask execution
- **Pattern-Based**: Strategy decoupled from logic
- **Composable**: Tasks reusable across workflows
- **State-Managed**: Unified `content_block` and `content_stream` variables
