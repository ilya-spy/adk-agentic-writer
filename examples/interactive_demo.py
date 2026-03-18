"""Example: Interactive CLI demo using the Coordinator directly.

Usage: python examples/interactive_demo.py

Requires GOOGLE_API_KEY environment variable.
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from adk_agentic_writer.agents.coordinator import Coordinator


async def main():
    print("=== ADK Agentic Writer - Interactive Demo ===\n")

    coordinator = Coordinator()
    tasks = coordinator.get_supported_tasks()
    print("Supported tasks:")
    for t in tasks:
        print(f"  {t.task_id:12s} (output: {t.output_key})")

    print("\n--- Running 'write' task ---")
    result = await coordinator.process_task("write", {
        "format": "quiz",
        "flavor": "quiz",
        "topic": "Python Programming",
        "num_questions": 3,
        "difficulty": "medium",
        "num_options": 4,
    })
    print(f"Draft content keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")

    print("\n--- Running 'review' task ---")
    review = await coordinator.process_task("review", {
        "draft_content": result,
        "format": "quiz",
    })
    print(f"Review: valid={review.get('valid')}, score={review.get('score')}")
    print(f"Summary: {review.get('summary')}")

    if review.get("score", 100) < 90:
        print("\n--- Running 'refine' task ---")
        refined = await coordinator.process_task("refine", {
            "draft_content": result,
            "review_result": review,
        })
        print(f"Refined content keys: {list(refined.keys()) if isinstance(refined, dict) else type(refined)}")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
