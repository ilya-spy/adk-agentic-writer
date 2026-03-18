"""Example: HTTP client for the task-driven API.

Usage:
    1. Start the server: uvicorn adk_agentic_writer.backend.api:app --reload
    2. Run: python examples/api_client.py
"""

import json
import httpx

BASE = "http://localhost:8000"


def main():
    client = httpx.Client(base_url=BASE, timeout=120)

    # List available tasks
    tasks = client.get("/tasks").json()
    print("Available tasks:")
    for t in tasks["tasks"]:
        print(f"  {t['task_id']:12s} -> output: {t['output_key']}")

    # List content types
    types = client.get("/content-types").json()
    print("\nContent types:")
    for ct in types["content_types"]:
        print(f"  {ct['value']:12s} ({ct['label']}) flavors={ct['flavors']}")

    # Run WRITE task
    print("\n--- Running 'write' task ---")
    resp = client.post("/task/write", json={
        "parameters": {
            "format": "quiz",
            "flavor": "trivia",
            "topic": "Solar System",
            "num_questions": 3,
            "difficulty": "easy",
            "num_options": 4,
        }
    })
    data = resp.json()
    print(f"Status: {data['status']}")
    print(f"Output key: {data['output_key']}")
    print(f"Content preview: {json.dumps(data['content'], indent=2)[:500]}...")

    # Check stored outputs
    outputs = client.get("/outputs").json()
    print(f"\nStored output keys: {list(outputs['outputs'].keys())}")

    # Run REVIEW task (uses draft_content from previous step)
    print("\n--- Running 'review' task ---")
    resp = client.post("/task/review", json={
        "parameters": {
            "draft_content": data["content"],
            "format": "quiz",
        }
    })
    review = resp.json()
    print(f"Review score: {review['content'].get('score', 'N/A')}")
    print(f"Summary: {review['content'].get('summary', 'N/A')}")


if __name__ == "__main__":
    main()
