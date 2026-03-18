"""Refiner agent -- improves content based on review feedback.

Creates a native ADK LlmAgent that reads draft_content and
review_result from session state, refines the content, and
overwrites draft_content with the improved version.
"""

from google.adk.agents import Agent

MODEL = "gemini-2.5-flash"

_INSTRUCTION = """\
You are an expert content refiner.

You receive content JSON (draft) and review feedback.
Your task is to improve the content based on the review.

**Current Content:**
{draft_content}

**Review Feedback:**
{review_result}

TASK:
1. Read every error and warning from the review.
2. Fix all errors -- these are critical.
3. Address warnings where possible.
4. Apply suggestions to improve quality.
5. Maintain the same JSON schema structure.
6. Keep the content engaging and creative.

OUTPUT: The refined content as valid JSON only.
Same schema as the input, but improved.
No markdown, no explanations -- just the JSON object.
"""

_INSTRUCTION_WITH_EXIT = """\
You are an expert content refiner.

You receive content JSON (draft) and review feedback.
Your task is to improve the content OR signal completion.

**Current Content:**
{draft_content}

**Review Feedback:**
{review_result}

TASK:
- If the review indicates the content is excellent (score >= 90, no errors):
  You MUST call the 'exit_loop' function. Do not output any text.
- Otherwise:
  1. Fix all errors from the review.
  2. Address warnings where possible.
  3. Apply suggestions to improve quality.
  4. Output the refined content as valid JSON only.

OUTPUT: Either call exit_loop OR output refined JSON. Nothing else.
"""


def create_refiner(model: str = MODEL) -> Agent:
    return Agent(
        name="RefinerAgent",
        model=model,
        instruction=_INSTRUCTION,
        description="Refines and improves content based on review feedback.",
        output_key="draft_content",
        include_contents="none",
    )


def create_loop_refiner(exit_loop_tool, model: str = MODEL) -> Agent:
    """Create a refiner that can call exit_loop to break out of a LoopAgent."""
    return Agent(
        name="RefinerAgent",
        model=model,
        instruction=_INSTRUCTION_WITH_EXIT,
        description="Refines content or exits the loop when quality is sufficient.",
        output_key="draft_content",
        include_contents="none",
        tools=[exit_loop_tool],
    )
