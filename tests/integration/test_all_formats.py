#!/usr/bin/env python3
"""Test all static team content generation formats."""

import asyncio
from src.adk_agentic_writer.agents.static import (
    CoordinatorAgent,
    StaticQuizWriterAgent,
    StoryWriterAgent,
    GameDesignerAgent,
    SimulationDesignerAgent,
)


async def test_all_formats():
    """Test generation of all content types."""
    print("Testing Static Team Content Generation\n" + "="*50)
    
    # Initialize coordinator
    coordinator = CoordinatorAgent()
    coordinator.register_agent(StaticQuizWriterAgent())
    coordinator.register_agent(StoryWriterAgent())
    coordinator.register_agent(GameDesignerAgent())
    coordinator.register_agent(SimulationDesignerAgent())
    
    # Test cases
    tests = [
        {
            "name": "Quiz",
            "content_type": "quiz",
            "topic": "Python Programming",
            "params": {"num_questions": 3},
            "check": lambda r: "questions" in r and len(r["questions"]) == 3
        },
        {
            "name": "Branched Narrative",
            "content_type": "branched_narrative",
            "topic": "Space Adventure",
            "params": {"num_branches": 3},
            "check": lambda r: "nodes" in r and len(r["nodes"]) > 0
        },
        {
            "name": "Quest Game",
            "content_type": "quest_game",
            "topic": "Medieval Quest",
            "params": {},
            "check": lambda r: "nodes" in r and "title" in r
        },
        {
            "name": "Web Simulation",
            "content_type": "web_simulation",
            "topic": "Physics Gravity",
            "params": {},
            "check": lambda r: "variables" in r and len(r["variables"]) > 0
        },
    ]
    
    results = []
    
    for test in tests:
        print(f"\n[TEST] {test['name']}")
        print(f"  Type: {test['content_type']}")
        print(f"  Topic: {test['topic']}")
        
        try:
            result = await coordinator.process_task(
                f"Generate {test['content_type']}",
                {
                    "content_type": test["content_type"],
                    "topic": test["topic"],
                    **test["params"]
                }
            )
            
            # Extract actual content (unwrap reviewer)
            content = result.get("content", {})
            if isinstance(content, dict) and "original_content" in content:
                content = content["original_content"]
            
            # Check content
            if test["check"](content):
                print(f"  [OK] Generated successfully")
                print(f"  [OK] Content keys: {list(content.keys())[:5]}")
                results.append((test['name'], True, None))
            else:
                print(f"  [FAIL] Content validation failed")
                print(f"  [INFO] Keys: {list(content.keys())}")
                results.append((test['name'], False, "Validation failed"))
                
        except Exception as e:
            print(f"  [ERROR] {e}")
            results.append((test['name'], False, str(e)))
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, error in results:
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {name}")
        if error:
            print(f"     Error: {error}")
    
    print(f"\nPassed: {passed}/{total}")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(test_all_formats())
    exit(0 if success else 1)

