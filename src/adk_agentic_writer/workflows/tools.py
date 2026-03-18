"""Shared tools for workflow agents."""

from google.adk.tools.tool_context import ToolContext


def exit_loop(tool_context: ToolContext):
    """Call this when the review indicates content quality is sufficient
    and no further refinement is needed. This exits the refinement loop."""
    tool_context.actions.escalate = True
    return {}
