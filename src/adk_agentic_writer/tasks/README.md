# Tasks

Unified task definitions for the ADK Agentic Writer.

## Task List

| Task ID   | Role        | Output Key         | Description                    |
|-----------|-------------|--------------------|---------------------------------|
| `ideate`  | STRATEGIST  | `ideation_result`  | Brainstorm format and topic    |
| `write`   | WRITER      | `draft_content`    | Generate content for a format  |
| `review`  | REVIEWER    | `review_result`    | Review content quality         |
| `refine`  | REFINER     | `draft_content`    | Improve content from feedback  |
| `publish` | COORDINATOR | `published_content`| Full pipeline: write+review+refine |

## Usage

```python
from adk_agentic_writer.tasks import IDEATE, WRITE, REVIEW, REFINE, PUBLISH

WRITE.task_id      # "write"
WRITE.output_key   # "draft_content"
WRITE.parameters   # {"format": "", "flavor": "", "topic": ""}
```

Tasks are executed via the Coordinator's `process_task(task_id, params)` method.
