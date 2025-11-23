"""Task definitions for ContentProtocol methods."""

from ..models.agent_models import AgentRole, AgentTask

# Task: generate_block
# Produces: content_block
GENERATE_BLOCK = AgentTask(
    task_id="generate_block",
    agent_role=AgentRole.WRITER,
    prompt="Generate a single {block_type} content block about {topic}",
    suggested_workflow="sequential_generation",
    suggested_team="content_team",
    output_key="content_block",
)

# Task: generate_sequential_blocks
# Produces: content_draft
GENERATE_SEQUENTIAL_BLOCKS = AgentTask(
    task_id="generate_sequential_blocks",
    agent_role=AgentRole.WRITER,
    prompt="Generate {num_blocks} sequential {block_type} blocks about {topic} in {genre} style",
    suggested_workflow="sequential_generation",
    suggested_team="content_team",
    output_key="content_draft",
)

# Task: generate_looped_blocks
# Produces: content_draft
GENERATE_LOOPED_BLOCKS = AgentTask(
    task_id="generate_looped_blocks",
    agent_role=AgentRole.WRITER,
    prompt="Generate {num_blocks} repeatable {block_type} blocks for {topic} practice with exit condition",
    suggested_workflow="looped_generation",
    suggested_team="content_team",
    output_key="content_draft",
)

# Task: generate_branched_blocks
# Produces: content_draft
GENERATE_BRANCHED_BLOCKS = AgentTask(
    task_id="generate_branched_blocks",
    agent_role=AgentRole.WRITER,
    prompt="Generate branched {block_type} blocks for {topic} with user choice points",
    suggested_workflow="branched_generation",
    suggested_team="content_team",
    output_key="content_draft",
)

# Task: generate_conditional_blocks
# Produces: content_draft
GENERATE_CONDITIONAL_BLOCKS = AgentTask(
    task_id="generate_conditional_blocks",
    agent_role=AgentRole.WRITER,
    prompt="Generate conditional {block_type} blocks for {topic} based on runtime conditions",
    suggested_workflow="branched_generation",
    suggested_team="content_team",
    output_key="content_draft",
)
