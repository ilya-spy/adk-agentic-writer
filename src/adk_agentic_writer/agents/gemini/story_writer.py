"""Gemini-powered story writer agent using Google ADK."""

import json
import logging
from typing import Any, Dict

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

from ...models.agent_models import AGENT_TEAM_CONFIGS, AgentRole, AgentStatus
from ...models.content_models import BranchedNarrative, StoryNode
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)


class GeminiStoryWriterAgent(BaseAgent):
    """Agent specialized in creating branched narratives using Google ADK."""

    def __init__(
        self,
        agent_id: str = "gemini_story_writer_1",
        config: Dict[str, Any] | None = None,
    ):
        """Initialize the Gemini story writer agent with Google ADK."""
        super().__init__(agent_id, AgentRole.STORY_WRITER, config)
        
        # Get system instruction from AGENT_TEAM_CONFIGS
        agent_config = AGENT_TEAM_CONFIGS.get(AgentRole.STORY_WRITER)
        
        # Create Google ADK Agent instance
        self.adk_agent = Agent(
            name="StoryWriterAgent",
            model=Gemini(model="gemini-2.0-flash-exp"),
            instruction=agent_config.system_instruction if agent_config else self._get_default_instruction(),
            output_key="story_content",
        )
        self.runner = InMemoryRunner(agent=self.adk_agent)
    
    def _get_default_instruction(self) -> str:
        """Default instruction if not in config."""
        return """You are a creative storyteller specializing in interactive branched narratives.
Create engaging stories with meaningful choices that lead to different outcomes."""

    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a branched narrative based on the given topic and parameters.

        Args:
            task_description: Description of the story to create
            parameters: Parameters including topic, genre, complexity

        Returns:
            Dict containing the generated branched narrative
        """
        await self.update_status(AgentStatus.WORKING)

        topic = parameters.get("topic", "adventure")
        genre = parameters.get("genre", "fantasy")
        num_branches = parameters.get("num_branches", 3)

        logger.info(f"Generating branched narrative about {topic} in {genre} genre using Google ADK")

        # Generate story using Google ADK Agent
        story_data = await self._generate_story_with_adk(topic, genre, num_branches)

        await self.update_status(AgentStatus.COMPLETED)

        return story_data

    async def _generate_story_with_adk(
        self, topic: str, genre: str, num_branches: int
    ) -> Dict[str, Any]:
        """Generate branched narrative using Google ADK Agent."""
        
        prompt = f"""Create an interactive branched narrative story with the following specifications:

Topic: {topic}
Genre: {genre}
Number of Major Branches: {num_branches}

Create a story with:
- An engaging opening scene
- At least {num_branches} major decision points
- Multiple endings (at least 2-3 different outcomes)
- Rich descriptions and character development

Return the story in the following JSON format:
{{
    "title": "Story title",
    "synopsis": "Brief story overview",
    "genre": "{genre}",
    "start_node": "start",
    "characters": ["Character 1", "Character 2"],
    "nodes": {{
        "start": {{
            "node_id": "start",
            "content": "Opening scene description...",
            "branches": [
                {{"text": "Choice 1", "next_node_id": "node1"}},
                {{"text": "Choice 2", "next_node_id": "node2"}}
            ],
            "tags": ["opening"],
            "is_ending": false
        }},
        "node1": {{
            "node_id": "node1",
            "content": "What happens after choice 1...",
            "branches": [...],
            "tags": ["branch1"],
            "is_ending": false
        }},
        "ending1": {{
            "node_id": "ending1",
            "content": "One possible ending...",
            "branches": [],
            "tags": ["ending", "victory"],
            "is_ending": true
        }}
    }}
}}

Make the story engaging, emotionally resonant, and ensure choices have meaningful consequences."""

        try:
            # Run Google ADK Agent
            result = await self.runner.run(input_data={})
            
            # Parse result
            story_data = json.loads(result.get("story_content", "{}")) if isinstance(result.get("story_content"), str) else result.get("story_content", {})
            
            # Validate and create BranchedNarrative object
            nodes_dict = {}
            for node_id, node_data in story_data.get("nodes", {}).items():
                nodes_dict[node_id] = StoryNode(**node_data)
            
            story = BranchedNarrative(
                title=story_data.get("title", f"{topic.title()} Story"),
                synopsis=story_data.get("synopsis", f"An interactive {genre} story about {topic}"),
                genre=story_data.get("genre", genre),
                start_node=story_data.get("start_node", "start"),
                nodes=nodes_dict,
                characters=story_data.get("characters", []),
            )
            
            return story.model_dump()

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error generating story with Google ADK: {e}")
            return await self._generate_fallback_story(topic, genre)

    async def _generate_fallback_story(self, topic: str, genre: str) -> Dict[str, Any]:
        """Fallback story generation."""
        logger.warning("Using fallback story generation")
        
        nodes = {
            "start": StoryNode(
                node_id="start",
                content=f"You find yourself at the beginning of an adventure about {topic}...",
                branches=[
                    {"text": "Take the left path", "next_node_id": "left"},
                    {"text": "Take the right path", "next_node_id": "right"},
                ],
                tags=["opening"],
                is_ending=False,
            ),
            "left": StoryNode(
                node_id="left",
                content="You chose the left path and discovered something amazing!",
                branches=[],
                tags=["ending", "victory"],
                is_ending=True,
            ),
            "right": StoryNode(
                node_id="right",
                content="You chose the right path and found a different outcome!",
                branches=[],
                tags=["ending"],
                is_ending=True,
            ),
        }

        story = BranchedNarrative(
            title=f"{topic.title()} Adventure",
            synopsis=f"An interactive {genre} story about {topic}",
            genre=genre,
            start_node="start",
            nodes=nodes,
            characters=["Hero"],
        )

        return story.model_dump()


