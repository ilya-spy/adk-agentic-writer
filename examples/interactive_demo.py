"""Interactive CLI demo for ADK Agentic Writer.

Features:
- Menu-driven interface
- Step-by-step wizards for creating agents, teams, tasks, workflows
- Status bar showing system state
- Interactive quiz generation with multiple patterns
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adk_agentic_writer.agents.static.quiz_writer import StaticQuizWriterAgent
from adk_agentic_writer.models.agent_models import AgentTask, AgentRole, WorkflowPattern
from adk_agentic_writer.protocols.content_protocol import (
    ContentBlockType,
    ContentPattern,
)
from adk_agentic_writer.runtime import AgentRuntime
from adk_agentic_writer.tasks import content_tasks
from adk_agentic_writer.teams.content_team import QUIZ_WRITER, QUIZ_WRITERS_POOL


class InteractiveDemo:
    """Interactive demo application."""

    def __init__(self):
        self.runtime = AgentRuntime(agent_class=StaticQuizWriterAgent)
        self.agents: Dict[str, StaticQuizWriterAgent] = {}
        self.generated_content: List[Dict] = []
        self.running = True

    def clear_screen(self):
        """Clear the console screen."""
        print("\033[2J\033[H", end="")

    def print_status_bar(self):
        """Print status bar with system information."""
        print("=" * 80)
        print(f"ADK AGENTIC WRITER - Interactive Demo")
        print("=" * 80)
        print(
            f"Agents: {len(self.agents)} | "
            f"Teams: {len(self.runtime.teams)} | "
            f"Workflows: {len(self.runtime.workflows)} | "
            f"Generated: {len(self.generated_content)}"
        )
        print("=" * 80)

    def print_menu(self, title: str, options: List[str]):
        """Print a menu with options."""
        print(f"\n{title}")
        print("-" * 80)
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        print(f"  0. Back/Exit")
        print("-" * 80)

    def get_choice(self, max_option: int) -> int:
        """Get user choice."""
        while True:
            try:
                choice = input("\nEnter your choice: ").strip()
                choice_int = int(choice)
                if 0 <= choice_int <= max_option:
                    return choice_int
                print(f"Please enter a number between 0 and {max_option}")
            except ValueError:
                print("Please enter a valid number")

    def get_input(self, prompt: str, default: Optional[str] = None) -> str:
        """Get user input with optional default."""
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            return user_input if user_input else default
        return input(f"{prompt}: ").strip()

    def get_int(
        self, prompt: str, default: int, min_val: int = 1, max_val: int = 100
    ) -> int:
        """Get integer input with validation."""
        while True:
            try:
                user_input = input(
                    f"{prompt} [{default}] (range: {min_val}-{max_val}): "
                ).strip()
                if not user_input:
                    return default
                value = int(user_input)
                if min_val <= value <= max_val:
                    return value
                print(f"Please enter a number between {min_val} and {max_val}")
            except ValueError:
                print("Please enter a valid number")

    async def wizard_create_agent(self):
        """Wizard for creating a new agent."""
        self.clear_screen()
        self.print_status_bar()
        print("\n[WIZARD] Create New Agent")
        print("=" * 80)

        # Get agent ID
        agent_id = self.get_input("Agent ID", f"quiz_agent_{len(self.agents) + 1}")

        if agent_id in self.agents:
            print(f"\n[ERROR] Agent '{agent_id}' already exists!")
            input("\nPress Enter to continue...")
            return

        # Create agent
        print(f"\n[INFO] Creating agent '{agent_id}'...")
        agent = StaticQuizWriterAgent(agent_id)
        self.agents[agent_id] = agent

        # Configure parameters
        print("\n[CONFIG] Configure Agent Parameters")
        topic = self.get_input("Topic", "Python Programming")
        num_questions = self.get_int("Number of questions", 5, 1, 20)

        print("\nDifficulty level:")
        print("  1. Easy")
        print("  2. Medium")
        print("  3. Hard")
        diff_choice = self.get_choice(3)
        difficulty = (
            ["easy", "medium", "hard"][diff_choice - 1] if diff_choice > 0 else "medium"
        )

        agent.update_parameters(
            {
                "topic": topic,
                "num_questions": num_questions,
                "difficulty": difficulty,
                "passing_score": 70,
            }
        )

        print(f"\n[SUCCESS] Agent '{agent_id}' created successfully!")
        print(f"  Topic: {topic}")
        print(f"  Questions: {num_questions}")
        print(f"  Difficulty: {difficulty}")

        input("\nPress Enter to continue...")

    async def wizard_create_team(self):
        """Wizard for creating a team."""
        self.clear_screen()
        self.print_status_bar()
        print("\n[WIZARD] Create Team")
        print("=" * 80)

        team_name = self.get_input("Team name", f"team_{len(self.runtime.teams) + 1}")
        num_agents = self.get_int("Number of agents in team", 2, 1, 5)

        print(f"\n[INFO] Creating team '{team_name}' with {num_agents} agents...")

        team_agents = self.runtime.create_team(
            team_metadata=QUIZ_WRITERS_POOL, agent_configs={"quiz_writer": QUIZ_WRITER}
        )

        # Register team agents in main agents dict
        for agent in team_agents:
            self.agents[agent.agent_id] = agent

        print(f"\n[SUCCESS] Team '{team_name}' created with {len(team_agents)} agents!")
        for agent in team_agents:
            print(f"  - {agent.agent_id}")

        input("\nPress Enter to continue...")

    async def wizard_manage_team(self):
        """Minimal team management: add/remove agents."""
        self.clear_screen()
        self.print_status_bar()
        print("\n[MANAGE] Team")
        print("=" * 80)

        if not self.runtime.teams:
            print("\nNo teams available.")
            input("\nPress Enter to continue...")
            return

        # Select team
        team_list = list(self.runtime.teams.items())
        for i, (name, team) in enumerate(team_list, 1):
            print(f"  {i}. {name} ({len(team.agent_ids)} agents)")

        choice = self.get_choice(len(team_list))
        if choice == 0:
            return

        team_name, team = team_list[choice - 1]

        # Show members
        print(f"\nMembers: {', '.join(team.agent_ids) or 'None'}")

        # Options
        print("\n1. Add agent  2. Remove agent")
        action = self.get_choice(2)

        if action == 1:
            # Add
            available = [
                (aid, a) for aid, a in self.agents.items() if aid not in team.agent_ids
            ]
            if not available:
                print("\nNo available agents.")
            else:
                for i, (aid, _) in enumerate(available, 1):
                    print(f"  {i}. {aid}")
                agent_choice = self.get_choice(len(available))
                if agent_choice > 0:
                    team.agent_ids.append(available[agent_choice - 1][0])
                    print(f"\nAdded {available[agent_choice - 1][0]}")

        elif action == 2:
            # Remove
            if not team.agent_ids:
                print("\nTeam is empty.")
            else:
                for i, aid in enumerate(team.agent_ids, 1):
                    print(f"  {i}. {aid}")
                agent_choice = self.get_choice(len(team.agent_ids))
                if agent_choice > 0:
                    removed = team.agent_ids.pop(agent_choice - 1)
                    print(f"\nRemoved {removed}")

        input("\nPress Enter to continue...")

    async def wizard_generate_content(self):
        """Wizard for generating content."""
        self.clear_screen()
        self.print_status_bar()
        print("\n[WIZARD] Generate Content")
        print("=" * 80)

        if not self.agents:
            print("\n[ERROR] No agents available. Create an agent first!")
            input("\nPress Enter to continue...")
            return

        # Select agent
        print("\nAvailable agents:")
        agent_list = list(self.agents.items())
        for i, (agent_id, agent) in enumerate(agent_list, 1):
            params = agent.parameters
            print(f"  {i}. {agent_id} (topic: {params.get('topic', 'N/A')})")

        agent_choice = self.get_choice(len(agent_list))
        if agent_choice == 0:
            return

        agent_id, agent = agent_list[agent_choice - 1]

        # Select pattern
        print("\nContent Pattern:")
        patterns = [
            ("Single Block", "single"),
            ("Sequential Blocks (Linear)", "sequential"),
            ("Looped Blocks (Practice Mode)", "looped"),
            ("Branched Blocks (Adaptive)", "branched"),
            ("Conditional Blocks (Bonus)", "conditional"),
        ]

        for i, (name, _) in enumerate(patterns, 1):
            print(f"  {i}. {name}")

        pattern_choice = self.get_choice(len(patterns))
        if pattern_choice == 0:
            return

        pattern_name, pattern_type = patterns[pattern_choice - 1]

        # Get pattern-specific parameters
        num_blocks = 1
        if pattern_type in ["sequential", "looped", "branched"]:
            num_blocks = self.get_int("Number of blocks", 3, 1, 10)

        # Generate content
        print(f"\n[GENERATE] Generating {pattern_name}...")
        print(f"  Agent: {agent_id}")
        print(f"  Pattern: {pattern_name}")
        print(f"  Blocks: {num_blocks}")

        try:
            if pattern_type == "single":
                result = await agent.generate_block(
                    ContentBlockType.QUESTION, agent.parameters
                )
                content = {
                    "block_id": result.block_id,
                    "pattern": result.pattern.value,
                    "navigation": result.navigation,
                    "content": result.content,
                }
            elif pattern_type == "sequential":
                blocks = await agent.generate_sequential_blocks(
                    num_blocks, ContentBlockType.QUESTION, agent.parameters
                )
                content = {
                    "blocks": [
                        {
                            "block_id": b.block_id,
                            "pattern": b.pattern.value,
                            "navigation": b.navigation,
                            "content": b.content,
                        }
                        for b in blocks
                    ]
                }
            elif pattern_type == "looped":
                blocks = await agent.generate_looped_blocks(
                    num_blocks,
                    ContentBlockType.QUESTION,
                    agent.parameters,
                    {"score": ">=80", "attempts": ">=3"},
                )
                content = {
                    "blocks": [
                        {
                            "block_id": b.block_id,
                            "pattern": b.pattern.value,
                            "navigation": b.navigation,
                            "exit_condition": b.exit_condition,
                            "content": b.content,
                        }
                        for b in blocks
                    ]
                }
            elif pattern_type == "branched":
                blocks = await agent.generate_branched_blocks([], agent.parameters)
                content = {
                    "blocks": [
                        {
                            "block_id": b.block_id,
                            "pattern": b.pattern.value,
                            "navigation": b.navigation,
                            "choices": b.choices,
                            "content": b.content,
                        }
                        for b in blocks
                    ]
                }
            elif pattern_type == "conditional":
                blocks = await agent.generate_conditional_blocks(
                    [{"condition": {"score": ">80"}, "num_questions": 3}],
                    agent.parameters,
                )
                content = {
                    "blocks": [
                        {
                            "block_id": b.block_id,
                            "pattern": b.pattern.value,
                            "metadata": b.metadata,
                            "content": b.content,
                        }
                        for b in blocks
                    ]
                }

            # Store generated content
            self.generated_content.append(
                {"agent": agent_id, "pattern": pattern_name, "content": content}
            )

            print(f"\n[SUCCESS] Content generated successfully!")
            self._display_content_summary(content)

        except Exception as e:
            print(f"\n[ERROR] Failed to generate content: {e}")

        input("\nPress Enter to continue...")

    def _display_content_summary(self, content: Dict):
        """Display summary of generated content."""
        if "blocks" in content:
            print(f"\n  Generated {len(content['blocks'])} blocks")
            for i, block in enumerate(content["blocks"], 1):
                block_data = block.get("content", block)
                title = block_data.get("title", "N/A")
                num_q = len(block_data.get("questions", []))
                pattern = block.get("pattern", "N/A")
                print(f"    Block {i}: {title} ({num_q} questions, {pattern})")
        else:
            block_data = content.get("content", content)
            title = block_data.get("title", "N/A")
            num_q = len(block_data.get("questions", []))
            print(f"\n  Title: {title}")
            print(f"  Questions: {num_q}")

    async def view_agents(self):
        """View all agents."""
        self.clear_screen()
        self.print_status_bar()
        print("\n[VIEW] Agents")
        print("=" * 80)

        if not self.agents:
            print("\nNo agents created yet.")
        else:
            for agent_id, agent in self.agents.items():
                state = agent.get_state()
                params = agent.parameters
                print(f"\nAgent: {agent_id}")
                print(f"  Status: {state.status}")
                print(f"  Role: {state.role}")
                print(f"  Parameters:")
                for key, value in params.items():
                    print(f"    - {key}: {value}")
                print(f"  Completed Tasks: {len(state.completed_tasks)}")
                print(f"  Variables: {list(state.variables.keys())}")

        input("\nPress Enter to continue...")

    async def view_teams(self):
        """View all teams."""
        self.clear_screen()
        self.print_status_bar()
        print("\n[VIEW] Teams")
        print("=" * 80)

        if not self.runtime.teams:
            print("\nNo teams created yet.")
        else:
            for team_name, team in self.runtime.teams.items():
                print(f"\nTeam: {team_name}")
                print(f"  Scope: {team.scope}")
                print(f"  Description: {team.description}")
                print(f"  Agents: {len(team.agent_ids)}")
                for agent_id in team.agent_ids:
                    print(f"    - {agent_id}")

        input("\nPress Enter to continue...")

    async def view_tasks(self):
        """View available tasks."""
        self.clear_screen()
        self.print_status_bar()
        print("\n[VIEW] Available Tasks")
        print("=" * 80)

        tasks = [
            ("GENERATE_BLOCK", content_tasks.GENERATE_BLOCK),
            ("GENERATE_SEQUENTIAL_BLOCKS", content_tasks.GENERATE_SEQUENTIAL_BLOCKS),
            ("GENERATE_LOOPED_BLOCKS", content_tasks.GENERATE_LOOPED_BLOCKS),
            ("GENERATE_BRANCHED_BLOCKS", content_tasks.GENERATE_BRANCHED_BLOCKS),
            ("GENERATE_CONDITIONAL_BLOCKS", content_tasks.GENERATE_CONDITIONAL_BLOCKS),
        ]

        for name, task in tasks:
            print(f"\nTask: {name}")
            print(f"  ID: {task.task_id}")
            print(f"  Role: {task.agent_role}")
            print(f"  Output: {task.output_key}")
            print(f"  Prompt: {task.prompt[:60]}...")

        input("\nPress Enter to continue...")

    async def view_generated_content(self):
        """View generated content."""
        self.clear_screen()
        self.print_status_bar()
        print("\n[VIEW] Generated Content")
        print("=" * 80)

        if not self.generated_content:
            print("\nNo content generated yet.")
        else:
            for i, item in enumerate(self.generated_content, 1):
                print(f"\n{i}. Agent: {item['agent']} | Pattern: {item['pattern']}")
                self._display_content_summary(item["content"])

        if self.generated_content:
            print("\n" + "-" * 80)
            view_choice = input(
                "\nEnter number to view details (0 to go back): "
            ).strip()
            if view_choice.isdigit() and 0 < int(view_choice) <= len(
                self.generated_content
            ):
                await self._view_content_details(int(view_choice) - 1)
        else:
            input("\nPress Enter to continue...")

    async def _view_content_details(self, index: int):
        """View detailed content."""
        self.clear_screen()
        self.print_status_bar()

        item = self.generated_content[index]
        content = item["content"]

        print(f"\n[DETAILS] {item['pattern']} by {item['agent']}")
        print("=" * 80)

        if "blocks" in content:
            for i, block in enumerate(content["blocks"], 1):
                block_data = block.get("content", block)
                print(f"\n--- Block {i}: {block.get('block_id', 'N/A')} ---")
                print(f"Pattern: {block.get('pattern', 'N/A')}")

                # Show navigation
                if block.get("navigation"):
                    nav = block["navigation"]
                    nav_info = []
                    if nav.get("next"):
                        nav_info.append(f"next: {nav['next']}")
                    if nav.get("prev"):
                        nav_info.append(f"prev: {nav['prev']}")
                    if nav.get("exit"):
                        nav_info.append(f"exit: {nav['exit']}")
                    if nav_info:
                        print(f"Navigation: {', '.join(nav_info)}")

                # Show choices (branched)
                if block.get("choices"):
                    print("Choices:")
                    for choice in block["choices"]:
                        print(
                            f"  - {choice.get('text', 'N/A')} -> {choice.get('next_block', 'N/A')}"
                        )

                # Show exit condition (looped)
                if block.get("exit_condition"):
                    print(f"Exit Condition: {block['exit_condition']}")

                # Show metadata (conditional)
                if block.get("metadata"):
                    print(f"Metadata: {block['metadata']}")

                self._print_quiz_details(block_data)
        else:
            # Single block
            block_data = content.get("content", content)
            print(f"\nBlock ID: {content.get('block_id', 'N/A')}")
            print(f"Pattern: {content.get('pattern', 'N/A')}")
            if content.get("navigation"):
                nav = content["navigation"]
                nav_info = []
                if nav.get("next"):
                    nav_info.append(f"next: {nav['next']}")
                if nav.get("prev"):
                    nav_info.append(f"prev: {nav['prev']}")
                if nav_info:
                    print(f"Navigation: {', '.join(nav_info)}")
            self._print_quiz_details(block_data)

        input("\nPress Enter to continue...")

    def _print_quiz_details(self, quiz: Dict):
        """Print quiz details."""
        print(f"\nTitle: {quiz.get('title', 'N/A')}")
        print(f"Description: {quiz.get('description', 'N/A')}")
        print(f"Questions: {len(quiz.get('questions', []))}")
        print(f"Passing Score: {quiz.get('passing_score', 'N/A')}%")

        for i, q in enumerate(quiz.get("questions", []), 1):
            print(f"\nQ{i}: {q.get('question', 'N/A')}")
            for j, opt in enumerate(q.get("options", []), 1):
                marker = (
                    "[CORRECT]" if j - 1 == q.get("correct_answer", -1) else "         "
                )
                print(f"  {marker} {j}. {opt}")

    async def main_menu(self):
        """Main menu loop."""
        while self.running:
            self.clear_screen()
            self.print_status_bar()

            self.print_menu(
                "Main Menu",
                [
                    "Create Agent",
                    "Create Team",
                    "Manage Team",
                    "Generate Content",
                    "View Agents",
                    "View Teams",
                    "View Tasks",
                    "View Generated Content",
                ],
            )

            choice = self.get_choice(8)

            if choice == 0:
                self.running = False
                print("\nGoodbye!")
            elif choice == 1:
                await self.wizard_create_agent()
            elif choice == 2:
                await self.wizard_create_team()
            elif choice == 3:
                await self.wizard_manage_team()
            elif choice == 4:
                await self.wizard_generate_content()
            elif choice == 5:
                await self.view_agents()
            elif choice == 6:
                await self.view_teams()
            elif choice == 7:
                await self.view_tasks()
            elif choice == 8:
                await self.view_generated_content()


async def main():
    """Run the interactive demo."""
    demo = InteractiveDemo()
    await demo.main_menu()


if __name__ == "__main__":
    asyncio.run(main())
