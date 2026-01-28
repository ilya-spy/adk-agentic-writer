"""Interactive CLI demo for ADK Agentic Writer.

Features:
- Menu-driven interface
- Step-by-step wizards for creating agents, teams
- Status bar showing system state
- Interactive quiz generation
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adk_agentic_writer.agents.static.writer import StaticQuizWriterAgent
from adk_agentic_writer.runtime import AgentRuntime
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

        print(f"\n[INFO] Creating team '{team_name}'...")

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

        # Generate content using the new generate() method
        print(f"\n[GENERATE] Generating quiz...")
        print(f"  Agent: {agent_id}")
        print(f"  Topic: {agent.parameters.get('topic', 'N/A')}")
        print(f"  Questions: {agent.parameters.get('num_questions', 'N/A')}")

        try:
            result = await agent.generate(
                topic=agent.parameters.get("topic", "General"),
                num_questions=agent.parameters.get("num_questions", 5),
                difficulty=agent.parameters.get("difficulty", "medium"),
            )

            # Store generated content
            self.generated_content.append({"agent": agent_id, "content": result})

            print(f"\n[SUCCESS] Content generated successfully!")
            self._display_content_summary(result)

        except Exception as e:
            print(f"\n[ERROR] Failed to generate content: {e}")

        input("\nPress Enter to continue...")

    def _display_content_summary(self, content: Dict):
        """Display summary of generated content."""
        title = content.get("title", "N/A")
        num_q = len(content.get("questions", []))
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
                print(f"\n{i}. Agent: {item['agent']}")
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

        print(f"\n[DETAILS] Quiz by {item['agent']}")
        print("=" * 80)

        self._print_quiz_details(content)

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
                    "Generate Content",
                    "View Agents",
                    "View Teams",
                    "View Generated Content",
                ],
            )

            choice = self.get_choice(6)

            if choice == 0:
                self.running = False
                print("\nGoodbye!")
            elif choice == 1:
                await self.wizard_create_agent()
            elif choice == 2:
                await self.wizard_create_team()
            elif choice == 3:
                await self.wizard_generate_content()
            elif choice == 4:
                await self.view_agents()
            elif choice == 5:
                await self.view_teams()
            elif choice == 6:
                await self.view_generated_content()


async def main():
    """Run the interactive demo."""
    demo = InteractiveDemo()
    await demo.main_menu()


if __name__ == "__main__":
    asyncio.run(main())
