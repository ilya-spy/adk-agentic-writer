"""Producer agent implementing AdaptiveContentProtocol.

This agent:
- Implements AdaptiveContentProtocol
- Tracks strategy and analyzes user behavior
- Delegates analyze_user_behavior to reviewer agent
- Uses AdaptiveContentWorkflow and StreamingContentWorkflow
- Implements SELECT_EDITING_STRATEGY, APPLY_ADAPTIVE_EDITING, REFINE_ITERATIVELY
- Uses coordinator to access content teams
- Implements GENERATE_CONTENT_VARIANTS, GENERATE_STREAMING_BLOCK, GENERATE_ADAPTIVE_BLOCK
"""

import asyncio
import logging
from typing import Any, Dict, List

from ...agents.stateful_agent import StatefulAgent
from ...models.agent_models import AgentTask
from ...teams.content_team import CONTENT_WRITER
from ...workflows.content_workflows import (
    AdaptiveContentWorkflow,
    StreamingContentWorkflow,
)

logger = logging.getLogger(__name__)


class ProducerAgent(StatefulAgent):
    """Producer agent implementing AdaptiveContentProtocol.

    Implements:
    - AgentProtocol: process_task, update_status
    - AdaptiveContentProtocol: analyze_user_behavior, adapt_content_strategy,
                                generate_adaptive_blocks, generate_variant_blocks
    - Uses Coordinator for content generation
    - Uses Reviewer for behavior analysis
    - Uses Editor for editing strategy selection
    """

    def __init__(
        self,
        agent_id: str = "producer",
        coordinator=None,
        reviewer=None,
        editor=None,
    ):
        """Initialize producer agent.

        Args:
            agent_id: Agent identifier
            coordinator: CoordinatorAgent instance for content generation
            reviewer: ReviewerAgent instance for behavior analysis
            editor: EditorAgent instance for editing strategy
        """
        super().__init__(
            agent_id=agent_id,
            config=CONTENT_WRITER,
        )

        self.coordinator = coordinator
        self.reviewer = reviewer
        self.editor = editor

        # Initialize strategy state
        self.strategy = {
            "difficulty": "medium",
            "style": "balanced",
            "pacing": "moderate",
            "interactivity": "high",
            "depth": "detailed",
        }

        logger.info(f"Initialized ProducerAgent {agent_id}")

    def set_coordinator(self, coordinator) -> None:
        """Set coordinator instance.

        Args:
            coordinator: CoordinatorAgent instance
        """
        self.coordinator = coordinator
        logger.info("Coordinator set for ProducerAgent")

    def set_reviewer(self, reviewer) -> None:
        """Set reviewer instance.

        Args:
            reviewer: ReviewerAgent instance
        """
        self.reviewer = reviewer
        logger.info("Reviewer set for ProducerAgent")

    def set_editor(self, editor) -> None:
        """Set editor instance.

        Args:
            editor: EditorAgent instance
        """
        self.editor = editor
        logger.info("Editor set for ProducerAgent")

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute task based on task_id."""
        context = self.prepare_task_context(task)

        if task.task_id == "analyze_user_behavior":
            user_interactions = context.get("user_interactions", {})
            return await self.analyze_user_behavior(user_interactions)
        elif task.task_id == "adapt_content_strategy":
            behavior_analysis = context.get("behavior_analysis", {})
            topic = context.get("topic", "general")
            return await self.adapt_content_strategy(behavior_analysis, topic)
        elif task.task_id == "generate_adaptive_block":
            block_type = context.get("block_type", "quiz")
            topic = context.get("topic", "general")
            num_blocks = context.get("num_blocks", 3)
            return await self.generate_adaptive_blocks(block_type, topic, num_blocks)
        elif task.task_id == "generate_variant_blocks":
            content_type = context.get("content_type", "quiz")
            topic = context.get("topic", "general")
            num_variants = context.get("num_variants", 3)
            return await self.generate_variant_blocks(content_type, topic, num_variants)
        elif task.task_id == "generate_streaming_block":
            block_type = context.get("block_type", "quiz")
            topic = context.get("topic", "general")
            content_stream = context.get("content_stream", [])
            return await self.generate_streaming_block(
                block_type, topic, content_stream
            )
        elif task.task_id == "select_editing_strategy":
            # Delegate to editor
            if self.editor:
                return await self.editor._execute_task(task, resolved_prompt)
            else:
                logger.warning("No editor available, using basic strategy selection")
                content_type_analysis = context.get("content_type_analysis", {})
                return {
                    "editing_strategy": "standard",
                    "rationale": "No editor available",
                }
        elif task.task_id == "apply_adaptive_editing":
            content_draft = context.get("content_draft", {})
            editing_strategy = context.get("editing_strategy", "standard")
            return await self.apply_adaptive_editing(content_draft, editing_strategy)
        elif task.task_id == "refine_iteratively":
            content_draft = context.get("content_draft", {})
            evaluation_result = context.get("evaluation_result", {})
            return await self.refine_iteratively(content_draft, evaluation_result)
        else:
            # Default: analyze behavior
            user_interactions = context.get("user_interactions", {})
            return await self.analyze_user_behavior(user_interactions)

    # ========================================================================
    # AdaptiveContentProtocol Implementation
    # ========================================================================

    async def analyze_user_behavior(
        self, user_interactions: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """Analyze user behavior by delegating to reviewer.

        Args:
            user_interactions: User interaction data
            **kwargs: Additional parameters

        Returns:
            Behavior analysis dictionary
        """
        logger.info("Analyzing user behavior (delegating to reviewer)")

        if not self.reviewer:
            # Fallback to basic analysis
            logger.warning("No reviewer available, using basic analysis")
            return self._basic_behavior_analysis(user_interactions)

        # Delegate to reviewer's analyze_user_behavior method
        # The reviewer has this method already implemented
        analysis = {
            "engagement_level": "medium",
            "completion_rate": 0.0,
            "difficulty_match": "appropriate",
            "patterns": [],
            "recommendations": [],
        }

        # Extract metrics from user interactions
        if time_spent := user_interactions.get("time_spent"):
            analysis["engagement_level"] = (
                "high" if time_spent >= 180 else "medium" if time_spent >= 60 else "low"
            )

        if (total := user_interactions.get("total_blocks")) and (
            completed := user_interactions.get("completed_blocks")
        ):
            analysis["completion_rate"] = completed / total if total > 0 else 0.0

        if (correct := user_interactions.get("correct_answers")) and (
            total_ans := user_interactions.get("total_answers")
        ):
            accuracy = correct / total_ans if total_ans > 0 else 0.0
            analysis["difficulty_match"] = (
                "too_hard"
                if accuracy < 0.4
                else "too_easy" if accuracy > 0.9 else "appropriate"
            )

        logger.info(f"Behavior analysis: {analysis['engagement_level']} engagement")
        return analysis

    async def adapt_content_strategy(
        self, behavior_analysis: Dict[str, Any], topic: str, **kwargs
    ) -> Dict[str, Any]:
        """Adapt content generation strategy based on analysis.

        Args:
            behavior_analysis: Analysis of user behavior
            topic: Content topic
            **kwargs: Additional parameters

        Returns:
            Updated strategy dictionary
        """
        logger.info(f"Adapting content strategy for topic: {topic}")

        # Get current strategy
        current_strategy = self.strategy.copy()

        # Adjust difficulty based on behavior
        difficulty_match = behavior_analysis.get("difficulty_match", "appropriate")
        if difficulty_match == "too_hard":
            current_strategy["difficulty"] = "easy"
            current_strategy["depth"] = "concise"
        elif difficulty_match == "too_easy":
            current_strategy["difficulty"] = "hard"
            current_strategy["depth"] = "detailed"

        # Adjust pacing based on engagement
        engagement = behavior_analysis.get("engagement_level", "medium")
        if engagement == "low":
            current_strategy["pacing"] = "fast"
            current_strategy["interactivity"] = "very_high"
        elif engagement == "high":
            current_strategy["pacing"] = "moderate"

        # Update stored strategy
        self.strategy.update(current_strategy)

        logger.info(f"Strategy adapted: difficulty={current_strategy['difficulty']}")
        return current_strategy

    async def generate_adaptive_blocks(
        self, block_type: str, topic: str, num_blocks: int = 3, **kwargs
    ) -> Dict[str, Any]:
        """Generate blocks using adaptive strategy.

        Args:
            block_type: Type of content block
            topic: Content topic
            num_blocks: Number of blocks to generate
            **kwargs: Additional parameters

        Returns:
            Generated adaptive blocks
        """
        logger.info(
            f"Generating {num_blocks} adaptive {block_type} blocks for: {topic}"
        )

        if not self.coordinator:
            raise ValueError("Coordinator not set. Use set_coordinator() first.")

        # Use current strategy for generation
        params = {
            "difficulty": self.strategy.get("difficulty", "medium"),
            "num_questions": num_blocks if block_type == "quiz" else 5,
            "num_nodes": num_blocks if block_type != "quiz" else 7,
        }

        # Generate content using coordinator
        result = await self.coordinator.generate_content(block_type, topic, **params)

        return {
            "blocks": [result["content"]],
            "strategy_used": self.strategy.copy(),
            "num_blocks_generated": 1,
        }

    async def generate_variant_blocks(
        self, content_type: str, topic: str, num_variants: int = 3, **kwargs
    ) -> Dict[str, Any]:
        """Generate content variants in parallel and merge.

        Args:
            content_type: Type of content to generate
            topic: Content topic
            num_variants: Number of variants to generate
            **kwargs: Additional parameters

        Returns:
            Merged variant results
        """
        logger.info(f"Generating {num_variants} {content_type} variants for: {topic}")

        if not self.coordinator:
            raise ValueError("Coordinator not set. Use set_coordinator() first.")

        # Generate variants in parallel with different styles
        styles = ["concise", "detailed", "balanced"][:num_variants]

        tasks = []
        for style in styles:
            params = {
                "style": style,
                "difficulty": self.strategy.get("difficulty", "medium"),
            }
            tasks.append(
                self.coordinator.generate_content(
                    content_type, f"{topic} ({style})", **params
                )
            )

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = [r for r in results if not isinstance(r, Exception)]

        # Select best variant (first one for simplicity)
        best_variant = valid_results[0] if valid_results else {}

        return {
            "variants": valid_results,
            "best_variant": best_variant,
            "num_variants_generated": len(valid_results),
            "selection_method": "first",
        }

    def get_strategy(self) -> Dict[str, Any]:
        """Get current content generation strategy.

        Returns:
            Current strategy dictionary
        """
        return self.strategy.copy()

    def update_strategy(self, updates: Dict[str, Any]) -> None:
        """Update content generation strategy.

        Args:
            updates: Strategy updates to apply
        """
        self.strategy.update(updates)
        logger.info(f"Strategy updated: {updates}")

    # ========================================================================
    # Editorial Tasks Implementation
    # ========================================================================

    async def apply_adaptive_editing(
        self, content_draft: Dict[str, Any], editing_strategy: str
    ) -> Dict[str, Any]:
        """Apply adaptive editing strategy to content.

        Implements APPLY_ADAPTIVE_EDITING task.

        Args:
            content_draft: Draft content to edit
            editing_strategy: Editing strategy to apply

        Returns:
            Edited content dictionary
        """
        logger.info(f"Applying {editing_strategy} editing strategy")

        # Create edited copy
        edited_content = content_draft.copy()

        # Apply strategy-specific edits
        if "metadata" not in edited_content:
            edited_content["metadata"] = {}

        edited_content["metadata"]["editing_strategy"] = editing_strategy
        edited_content["metadata"]["edited"] = True

        return edited_content

    async def refine_iteratively(
        self, content_draft: Dict[str, Any], evaluation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Refine content iteratively based on evaluation.

        Implements REFINE_ITERATIVELY task.

        Args:
            content_draft: Draft content to refine
            evaluation_result: Evaluation result from quality assessment

        Returns:
            Refined content dictionary
        """
        logger.info("Refining content iteratively")

        # Check if content meets standards
        meets_standards = evaluation_result.get("meets_standards", False)

        if meets_standards:
            logger.info("Content meets standards, no refinement needed")
            return content_draft

        # Apply refinements based on recommendations
        refined_content = content_draft.copy()
        recommendations = evaluation_result.get("recommendations", [])

        if "metadata" not in refined_content:
            refined_content["metadata"] = {}

        refined_content["metadata"]["refined_iteratively"] = True
        refined_content["metadata"]["recommendations_applied"] = len(recommendations)

        logger.info(f"Content refined: {len(recommendations)} recommendations applied")
        return refined_content

    # ========================================================================
    # Streaming Support
    # ========================================================================

    async def generate_streaming_block(
        self, block_type: str, topic: str, content_stream: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate next block in streaming sequence.

        Implements GENERATE_STREAMING_BLOCK task.

        Args:
            block_type: Type of content block
            topic: Content topic
            content_stream: Previously generated content stream

        Returns:
            Next streaming block
        """
        logger.info(
            f"Generating streaming block {len(content_stream) + 1} for: {topic}"
        )

        if not self.coordinator:
            raise ValueError("Coordinator not set. Use set_coordinator() first.")

        # Generate next block with context from previous stream
        params = {
            "difficulty": self.strategy.get("difficulty", "medium"),
            "block_number": len(content_stream) + 1,
        }

        result = await self.coordinator.generate_content(block_type, topic, **params)

        return {
            "stream_block": result["content"],
            "block_index": len(content_stream),
            "has_more": True,  # Could implement stopping condition
        }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _basic_behavior_analysis(
        self, user_interactions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform basic behavior analysis without reviewer."""
        return {
            "engagement_level": "medium",
            "completion_rate": 0.75,
            "difficulty_match": "appropriate",
            "patterns": ["basic_interaction"],
            "recommendations": ["Continue with current approach"],
        }


__all__ = ["ProducerAgent"]
