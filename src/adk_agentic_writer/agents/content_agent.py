"""Base class for content-generating agents.

Inheritance: BaseAgent → StatefulAgent → ContentWriterAgent → WriterAgent/DesignerAgent
"""

import logging
from typing import Any, Dict, List, Optional

from ..models.agent_models import AgentConfig, AgentModel, AgentTask
from ..models.content_models import ContentBlock, ContentBlockType, ContentPattern
from ..protocols.content_protocol import ContentProtocol
from ..utils.text_provider import TextProvider, TemplateTextProvider
from .stateful_agent import StatefulAgent

logger = logging.getLogger(__name__)


class ContentWriterAgent(StatefulAgent, ContentProtocol):
    """Base class for content-generating agents.

    Implements ContentProtocol with 3 methods:
    - generate_text: Text generation via TextProvider
    - generate_block: Single content block (subclasses implement)
    - generate_patterned_blocks: Navigation patterns

    Subclasses implement:
    - generate_block() - ContentProtocol
    - _build_content() - Content type builder
    """

    def __init__(
        self,
        agent_id: str,
        config: AgentConfig,
        model: Optional[AgentModel] = None,
        text_provider: Optional[TextProvider] = None,
    ):
        if model is None:
            model = AgentModel(name=agent_id)
        super().__init__(agent_id=agent_id, config=config, model=model)
        self.text_provider = text_provider or TemplateTextProvider()
        logger.info(
            f"Initialized ContentWriterAgent {agent_id} with {type(self.text_provider).__name__}"
        )

    # Internal task processing forward to content building methods
    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute task by calling _build_content()."""
        return await self._build_content(self.prepare_task_context(task))

    async def _build_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build content. Subclasses must implement."""
        raise NotImplementedError("Subclasses must implement _build_content()")

    # ContentProtocol implementation
    async def generate_text(
        self, prompt_key: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate text using the text provider."""
        full_context = {**self.parameters}
        if context:
            full_context.update(context)
        return await self.text_provider.generate_text(prompt_key, full_context)

    # ContentProtocol - subclasses implement generate_block()
    async def generate_block(
        self,
        block_type: ContentBlockType,
        context: Dict[str, Any],
        previous_blocks: Optional[List[ContentBlock]] = None,
    ) -> ContentBlock:
        """Generate a single content block. Subclasses must implement."""
        raise NotImplementedError("Subclasses must implement generate_block()")

    async def generate_patterned_blocks(
        self,
        block_type: ContentBlockType,
        pattern: ContentPattern,
        context: Dict[str, Any],
    ) -> List[ContentBlock]:
        """Generate blocks with navigation based on pattern.

        Shared navigation engine for all content types.
        Calls generate_block() which subclasses implement.
        """
        count, blocks = context.get("count", 3), []
        for i in range(count):
            block = await self.generate_block(
                block_type,
                {**context, "block_id": f"{block_type.value}_{i}", "index": i},
            )
            block.pattern = pattern
            if pattern == ContentPattern.SEQUENTIAL and i < count - 1:
                block.navigation = {"next": f"{block_type.value}_{i + 1}"}
            elif pattern == ContentPattern.LOOPED:
                block.navigation = {"next": f"{block_type.value}_{(i + 1) % count}"}
                block.exit_condition = context.get(
                    "exit_condition", {"max_iterations": 3}
                )
            elif pattern == ContentPattern.BRANCHED:
                block.choices = [
                    {"text": f"Go to {j}", "target": f"{block_type.value}_{j}"}
                    for j in range(count)
                    if j != i
                ]
            blocks.append(block)
        return blocks


__all__ = ["ContentWriterAgent"]
