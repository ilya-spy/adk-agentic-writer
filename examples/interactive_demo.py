"""Interactive CLI demo for ADK Agentic Writer.

Demonstrates content generation via the Coordinator agent.
Requires GOOGLE_API_KEY environment variable.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv()

from adk_agentic_writer.agents.coordinator import Coordinator


class InteractiveDemo:
    """Interactive demo using the pure ADK agent system."""

    def __init__(self):
        self.coordinator = Coordinator()
        self.generated_content: List[Dict] = []
        self.running = True

    def clear_screen(self):
        print("\033[2J\033[H", end="")

    def print_header(self):
        print("=" * 70)
        print("  ADK Agentic Writer — Interactive Demo")
        print("=" * 70)
        print(f"  Generated items: {len(self.generated_content)}")
        print("=" * 70)

    def get_input(self, prompt: str, default: str = "") -> str:
        suffix = f" [{default}]" if default else ""
        val = input(f"  {prompt}{suffix}: ").strip()
        return val or default

    def get_int(self, prompt: str, default: int, lo: int = 1, hi: int = 50) -> int:
        while True:
            raw = self.get_input(f"{prompt} ({lo}-{hi})", str(default))
            try:
                v = int(raw)
                if lo <= v <= hi:
                    return v
            except ValueError:
                pass
            print(f"    Enter an integer between {lo} and {hi}")

    def choose(self, options: List[str], prompt: str = "Choose") -> int:
        for i, opt in enumerate(options, 1):
            print(f"    {i}. {opt}")
        print(f"    0. Back")
        while True:
            raw = self.get_input(prompt)
            try:
                v = int(raw)
                if v == 0:
                    return -1
                if 1 <= v <= len(options):
                    return v - 1
            except ValueError:
                pass

    async def generate_content(self):
        self.clear_screen()
        self.print_header()
        print("\n  Select content type:\n")

        types = ["quiz", "story", "game", "simulation"]
        idx = self.choose(types, "Content type")
        if idx < 0:
            return

        content_type = types[idx]
        topic = self.get_input("Topic", "Python Programming")

        params: Dict[str, Any] = {}
        if content_type == "quiz":
            params["num_questions"] = self.get_int("Number of questions", 5, 3, 20)
            params["num_options"] = self.get_int("Options per question", 4, 2, 6)
            diff_idx = self.choose(["easy", "medium", "hard"], "Difficulty")
            params["difficulty"] = ["easy", "medium", "hard"][diff_idx] if diff_idx >= 0 else "medium"
        elif content_type == "story":
            params["num_nodes"] = self.get_int("Number of nodes", 7, 3, 15)
            params["genre"] = self.get_input("Genre", "fantasy")
        elif content_type == "game":
            params["num_nodes"] = self.get_int("Number of nodes", 5, 3, 15)
        elif content_type == "simulation":
            params["complexity"] = self.get_input("Complexity", "medium")

        print(f"\n  Generating {content_type} about '{topic}'...")

        task = self.coordinator.resolve_task(content_type=content_type)
        if not task:
            print(f"  ERROR: Unknown content type: {content_type}")
            input("\n  Press Enter...")
            return

        params["content_type"] = content_type
        try:
            result = await self.coordinator.process_task(task, {"topic": topic, **params})
            self.generated_content.append({
                "content_type": content_type,
                "topic": topic,
                "content": result,
            })
            print(f"\n  SUCCESS! Generated {content_type}.")
            self._print_summary(result)
        except Exception as e:
            print(f"\n  ERROR: {e}")

        input("\n  Press Enter...")

    async def generate_with_validation(self):
        self.clear_screen()
        self.print_header()
        print("\n  Generate with Validation\n")

        types = ["quiz", "story", "game", "simulation"]
        idx = self.choose(types, "Content type")
        if idx < 0:
            return

        content_type = types[idx]
        topic = self.get_input("Topic", "Space Exploration")

        task = self.coordinator.resolve_task(content_type=content_type)
        if not task:
            print(f"  ERROR: Unknown content type: {content_type}")
            input("\n  Press Enter...")
            return

        print(f"\n  Generating + validating {content_type} about '{topic}'...")

        try:
            result = await self.coordinator.process_with_validation(
                task, {"topic": topic, "content_type": content_type}
            )
            content = result.get("content", {})
            validation = result.get("validation_result", {})

            self.generated_content.append({
                "content_type": content_type,
                "topic": topic,
                "content": content,
                "validation": validation,
            })

            print(f"\n  Content generated.")
            self._print_summary(content)
            print(f"\n  Validation: valid={validation.get('valid')}, score={validation.get('score')}")
            for err in validation.get("errors", []):
                print(f"    ERROR: {err}")
            for warn in validation.get("warnings", []):
                print(f"    WARN:  {warn}")
        except Exception as e:
            print(f"\n  ERROR: {e}")

        input("\n  Press Enter...")

    def view_generated(self):
        self.clear_screen()
        self.print_header()
        print("\n  Generated Content\n")

        if not self.generated_content:
            print("  No content generated yet.")
        else:
            for i, item in enumerate(self.generated_content, 1):
                ct = item["content_type"]
                topic = item.get("topic", "?")
                print(f"  {i}. [{ct}] {topic}")
                self._print_summary(item["content"], indent=5)

            raw = self.get_input("\n  View details (number, or 0 to skip)")
            try:
                idx = int(raw) - 1
                if 0 <= idx < len(self.generated_content):
                    print(json.dumps(self.generated_content[idx]["content"], indent=2, ensure_ascii=False))
            except (ValueError, IndexError):
                pass

        input("\n  Press Enter...")

    @staticmethod
    def _print_summary(content: Dict, indent: int = 3):
        prefix = " " * indent
        title = content.get("title", "N/A")
        print(f"{prefix}Title: {title}")
        if "questions" in content:
            print(f"{prefix}Questions: {len(content['questions'])}")
        elif "nodes" in content:
            print(f"{prefix}Nodes: {len(content['nodes'])}")

    async def main_menu(self):
        while self.running:
            self.clear_screen()
            self.print_header()

            options = [
                "Generate Content",
                "Generate with Validation",
                "View Generated Content",
            ]
            print()
            idx = self.choose(options, "Action")

            if idx < 0:
                self.running = False
                print("\n  Goodbye!")
            elif idx == 0:
                await self.generate_content()
            elif idx == 1:
                await self.generate_with_validation()
            elif idx == 2:
                self.view_generated()


async def main():
    demo = InteractiveDemo()
    await demo.main_menu()


if __name__ == "__main__":
    asyncio.run(main())
