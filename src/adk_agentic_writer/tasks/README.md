# Tasks

Atomic work units with prompts, roles, and data flow definitions.

## Overview

**AgentTask** defines a single unit of work for an agent:

- **Role**: Agent type (WRITER, REVIEWER, REFINER, EDITOR, STREAMER)
- **Prompt**: Instruction template with `{variable}` substitution
- **Output Key**: State variable to store result
- **Dependencies**: Required predecessor task IDs

**Data Flow**: Task `output_key` → Next task's `{input_variable}`

---

## Task Categories

### Content Tasks (`content_tasks.py`)

All generation tasks output to `content_block`:

- `GENERATE_BLOCK` - Single content unit
- `GENERATE_SEQUENTIAL_BLOCKS` - Linear sequence
- `GENERATE_LOOPED_BLOCKS` - Repeatable with exit conditions
- `GENERATE_BRANCHED_BLOCKS` - Choice-based navigation
- `GENERATE_CONDITIONAL_BLOCKS` - State-based display
- `GENERATE_VARIANT_BLOCKS` - Multiple variations
- `GENERATE_ADAPTIVE_BLOCK` - Behavior-adapted content
- `GENERATE_STREAMING_BLOCK` - Progressive generation

**Support Tasks**:
- `ANALYZE_USER_BEHAVIOR` → `behavior_analysis`
- `ADAPT_CONTENT_STRATEGY` → `content_strategy`
- `STREAM_CONTENT_BLOCK` → `content_stream`

### Editorial Tasks (`editorial_tasks.py`)

Refinement and quality improvement:

- `REVIEW_DRAFT` → `review_feedback`
- `REFINE_BASED_ON_REVIEW` → `refined_draft`
- `FINALIZE_CONTENT` → `final_content`
- `EVALUATE_CONTENT_QUALITY` → `evaluation_result`
- `REFINE_ITERATIVELY` → `refined_content`
- `ANALYZE_CONTENT_TYPE` → `content_type_analysis`
- `SELECT_EDITING_STRATEGY` → `editing_strategy`
- `APPLY_ADAPTIVE_EDITING` → `edited_content`
- `REVIEW_VARIANTS_QUALITY` → `quality_scores`
- `SELECT_BEST_VARIANT` → `selected_content`

---

## Usage

```python
from adk_agentic_writer.tasks import content_tasks, editorial_tasks

# Access task
task = content_tasks.GENERATE_ADAPTIVE_BLOCK

# Task properties
task.task_id          # "generate_adaptive_block"
task.agent_role       # AgentRole.WRITER
task.output_key       # "content_block"
task.dependencies     # ["adapt_content_strategy"]
task.prompt           # Template with {variables}
```

---

## Key Principles

✅ **Atomic** - Each task does one thing  
✅ **Composable** - Tasks chain via output → input  
✅ **Declarative** - Dependencies explicitly defined  
✅ **Unified Output** - All generation → `content_block`

