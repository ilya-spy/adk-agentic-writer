# Workflows

Task-driven orchestration for content generation and editorial refinement.

## Overview

Workflows orchestrate **AgentTask** execution using patterns. Data flows through unified state variables:

- **`content_block`**: Current content unit (all generation outputs here)
- **`content_stream`**: Accumulated history (enables continuity and streaming)

**Formula**: `Workflow = Pattern + Scope + Tasks + Agents`

- **Pattern**: Execution strategy (SEQUENTIAL, PARALLEL, LOOP, CONDITIONAL)
- **Scope**: Domain (CONTENT, EDITORIAL, AGENT)
- **Tasks**: AgentTask instances defining work units
- **Agents**: Agent configurations that execute tasks

### Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| SEQUENTIAL | Execute in order | Review → Refine → Finalize |
| PARALLEL | Execute concurrently | Generate variants → Select |
| LOOP | Repeat until condition | Generate → Stream → Repeat |
| CONDITIONAL | Route by condition | Analyze → Apply strategy |

---

## Content Workflows

Generate structured content with different interaction patterns.

### AdaptiveContentWorkflow (LOOP)
Adapts generation based on user behavior patterns.

**Tasks**: `ANALYZE_USER_BEHAVIOR` → `ADAPT_CONTENT_STRATEGY` → `GENERATE_ADAPTIVE_BLOCK`

**Use Cases**: Adaptive learning, personalized stories, difficulty scaling

### StreamingContentWorkflow (LOOP)
Generates and streams content progressively.

**Tasks**: `GENERATE_STREAMING_BLOCK` → `STREAM_CONTENT_BLOCK`

**Use Cases**: Real-time generation, progressive tutorials, live content

---

## Editorial Workflows

Refine and improve content through review, validation, and editing.

### SequentialEditorialWorkflow (SEQUENTIAL)
Linear refinement through stages.

**Tasks**: `REVIEW_DRAFT` → `REFINE_BASED_ON_REVIEW` → `FINALIZE_CONTENT`

**Use Cases**: Standard editorial process, quality assurance

### ParallelEditorialWorkflow (PARALLEL)
Generates variants concurrently, selects best.

**Tasks**: `GENERATE_CONTENT_VARIANTS` (×3 parallel)

**Use Cases**: A/B testing, creative exploration

### IterativeEditorialWorkflow (LOOP)
Iterative improvement through repeated evaluation.

**Tasks**: `EVALUATE_CONTENT_QUALITY` → `REFINE_ITERATIVELY` (loop)

**Use Cases**: High-quality content, quality thresholds

### AdaptiveEditorialWorkflow (CONDITIONAL)
Adapts editing strategy based on content type.

**Tasks**: `ANALYZE_CONTENT_TYPE` → `SELECT_EDITING_STRATEGY` → `APPLY_ADAPTIVE_EDITING`

**Use Cases**: Multi-format content, specialized editing

---

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
    "content_stream": previous_content,
    "user_interactions": user_data
})
```

---

## Key Principles

✅ **Task-Driven** - Workflows orchestrate AgentTask execution  
✅ **Unified State** - `content_block` and `content_stream` enable flexible flow  
✅ **Pattern-Based** - Execution strategy decoupled from logic  
✅ **Composable** - Tasks reusable across workflows  
✅ **Type-Safe** - Output keys match input variables
