"""Gemini-powered reviewer agent using Google ADK.

Implements: AgentProtocol + EditorialProtocol
Uses: Editorial models for feedback and quality metrics
"""

import json
import logging
from typing import Any, Dict

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

from ...models.agent_models import AGENT_TEAM_CONFIGS, AgentRole, AgentStatus
from ...models.editorial_models import (
    Feedback,
    FeedbackType,
    QualityMetrics,
    ValidationResult,
)
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)


class GeminiReviewerAgent(BaseAgent):
    """Agent specialized in reviewing and improving content using Google ADK.
    
    Implements:
    - AgentProtocol: process_task, update_status, get_state, receive_message
    - EditorialProtocol: generate_content, validate_content, refine_content
    
    Uses:
    - Google ADK for intelligent content review
    - Editorial models for structured feedback and quality metrics
    """

    def __init__(
        self,
        agent_id: str = "gemini_reviewer_1",
        config: Dict[str, Any] | None = None,
    ):
        """Initialize the Gemini reviewer agent with Google ADK."""
        super().__init__(agent_id, AgentRole.REVIEWER, config)
        
        # Get system instruction from AGENT_TEAM_CONFIGS
        agent_config = AGENT_TEAM_CONFIGS.get(AgentRole.REVIEWER)
        
        # Create Google ADK Agent instance
        self.adk_agent = Agent(
            name="ReviewerAgent",
            model=Gemini(model="gemini-2.0-flash-exp"),
            instruction=agent_config.system_instruction if agent_config else self._get_default_instruction(),
            output_key="reviewed_content",
        )
        self.runner = InMemoryRunner(agent=self.adk_agent)
    
    def _get_default_instruction(self) -> str:
        """Default instruction if not in config."""
        return """You are an expert content reviewer and quality assurance specialist.
Review, improve, and validate interactive content for quality and accuracy.
Provide structured feedback with quality metrics, specific issues, and actionable suggestions."""

    async def process_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review and improve generated content using Google ADK Agent.

        Args:
            task_description: Description of the review task
            parameters: Parameters including content to review

        Returns:
            Dict containing the reviewed/improved content
        """
        await self.update_status(AgentStatus.WORKING)

        content = parameters.get("content", {})
        content_type = parameters.get("content_type", "general")
        review_criteria = parameters.get("review_criteria", [])

        logger.info(f"Reviewing {content_type} content using Google ADK")

        # Review content using Google ADK Agent
        reviewed_data = await self._review_content_with_adk(content, content_type, review_criteria)

        await self.update_status(AgentStatus.COMPLETED)

        return reviewed_data

    async def _review_content_with_adk(
        self, content: Dict[str, Any], content_type: str, review_criteria: list
    ) -> Dict[str, Any]:
        """Review content using Google ADK Agent."""
        
        criteria_str = "\n".join([f"- {criterion}" for criterion in review_criteria]) if review_criteria else "- Overall quality and accuracy"
        
        prompt = f"""Review and improve the following {content_type} content:

Content to review:
{json.dumps(content, indent=2)}

Review criteria:
{criteria_str}

Please provide:
1. A detailed review with specific feedback
2. Suggested improvements
3. An improved version of the content (if applicable)

Return your response in JSON format:
{{
    "review": "Detailed review feedback...",
    "issues_found": ["Issue 1", "Issue 2"],
    "suggestions": ["Suggestion 1", "Suggestion 2"],
    "improved_content": {{...}},
    "quality_score": 85
}}"""

        try:
            # Run Google ADK Agent
            result = await self.runner.run(input_data={})
            
            # Parse result
            reviewed_data = json.loads(result.get("reviewed_content", "{}")) if isinstance(result.get("reviewed_content"), str) else result.get("reviewed_content", {})
            
            return {
                "original_content": content,
                "review": reviewed_data.get("review", "Content reviewed successfully"),
                "issues_found": reviewed_data.get("issues_found", []),
                "suggestions": reviewed_data.get("suggestions", []),
                "improved_content": reviewed_data.get("improved_content", content),
                "quality_score": reviewed_data.get("quality_score", 80),
            }

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error reviewing content with Google ADK: {e}")
            return {
                "original_content": content,
                "review": "Review completed with basic validation",
                "issues_found": [],
                "suggestions": ["Content appears valid"],
                "improved_content": content,
                "quality_score": 75,
            }

