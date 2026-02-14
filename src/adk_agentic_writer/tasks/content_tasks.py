"""Task templates for content generation.

Each task includes content_types (aliases) for discovery.
Agents import tasks and publish via get_supported_tasks().
"""

from ..models.agent_models import AgentRole, AgentTask

# ============================================================================
# Primary Content Tasks - each with content_types aliases
# ============================================================================

GENERATE_CONTENT = AgentTask(
    task_id="generate_content",
    agent_role=AgentRole.WRITER,
    prompt="Generate content about {topic}.",
    parameters={"topic": ""},
    content_types=[],
    output_key="content",
)

GENERATE_QUIZ = AgentTask(
    task_id="generate_quiz",
    agent_role=AgentRole.WRITER,
    prompt="Generate a quiz about {topic} with {num_questions} questions.",
    parameters={"topic": "", "num_questions": 5, "difficulty": "medium"},
    content_types=["quiz", "trivia", "test"],
    output_key="content",
)

GENERATE_STORY = AgentTask(
    task_id="generate_story",
    agent_role=AgentRole.WRITER,
    prompt="Generate a branched narrative about {topic} with {num_nodes} nodes.",
    parameters={"topic": "", "num_nodes": 7, "genre": "fantasy"},
    content_types=["story", "narrative", "branched_narrative", "adventure"],
    output_key="content",
)

GENERATE_GAME = AgentTask(
    task_id="generate_game",
    agent_role=AgentRole.DESIGNER,
    prompt="Generate a quest game about {topic} with {num_nodes} nodes.",
    parameters={"topic": "", "num_nodes": 5, "complexity": "medium"},
    content_types=["game", "quest_game", "quest", "rpg"],
    output_key="content",
)

GENERATE_SIMULATION = AgentTask(
    task_id="generate_simulation",
    agent_role=AgentRole.DESIGNER,
    prompt="Generate an interactive simulation about {topic}.",
    parameters={"topic": "", "complexity": "medium"},
    content_types=["simulation", "web_simulation", "interactive", "simulator"],
    output_key="content",
)

# ============================================================================
# Block-level tasks for granular generation control
# ============================================================================

# Block-level task (internal use)
GENERATE_BLOCK = AgentTask(
    task_id="generate_block",
    agent_role=AgentRole.WRITER,
    prompt="Generate a {block_type} block about {topic}.",
    parameters={"topic": "", "block_type": "content"},
    content_types=[],  # Internal, not for UI
    output_key="content_block",
)

# Task: generate_sequential_blocks
# Produces: content_sequence
GENERATE_SEQUENTIAL_BLOCKS = AgentTask(
    task_id="generate_sequential_blocks",
    agent_role=AgentRole.WRITER,
    prompt="""Generate sequential content blocks about the following topic in the specified style.

Number of blocks: {num_blocks}
Block type: {block_type}
Topic: {topic}
Style: {genre}""",
    output_key="content_block",
)

# Task: generate_looped_blocks
# Produces: content_loop
GENERATE_LOOPED_BLOCKS = AgentTask(
    task_id="generate_looped_blocks",
    agent_role=AgentRole.WRITER,
    prompt="""Generate repeatable content blocks with exit conditions for the following topic.

Number of blocks: {num_blocks}
Block type: {block_type}
Topic: {topic}
Maximum iterations: {num_iterations}""",
    output_key="content_block",
)

# Task: generate_branched_blocks
# Produces: content_branch
GENERATE_BRANCHED_BLOCKS = AgentTask(
    task_id="generate_branched_blocks",
    agent_role=AgentRole.WRITER,
    prompt="""Generate branched content blocks with user choice points for the following topic.

Block type: {block_type}
Topic: {topic}""",
    output_key="content_block",
)

# Task: generate_conditional_blocks
# Produces: content_conditional
GENERATE_CONDITIONAL_BLOCKS = AgentTask(
    task_id="generate_conditional_blocks",
    agent_role=AgentRole.WRITER,
    prompt="""Generate conditional content blocks based on runtime conditions for the following topic.

Block type: {block_type}
Topic: {topic}""",
    output_key="content_block",
)

GENERATE_VARIANT_BLOCKS = AgentTask(
    task_id="generate_variant_blocks",
    agent_role=AgentRole.WRITER,
    prompt="""Generate content variants using the specified style and approach (you can smartly adjust for variance).

Topic: {topic}
Style: {style}
Approach: {approach}
Draft: {content_block}""",
    output_key="content_block",
)

# ============================================================================
# Tasks for AdaptiveContentWorkflow
# Pattern: Analyze Behavior → Adapt Strategy → Generate Block → Repeat
# ============================================================================

# Task: analyze_user_behavior
# Produces: behavior_analysis
ANALYZE_USER_BEHAVIOR = AgentTask(
    task_id="analyze_user_behavior",
    agent_role=AgentRole.WRITER,  # adaptator role
    prompt="""Analyze user behavior patterns to determine adaptation strategy based on the following data.

Previous content: {content_stream}
User interactions: {user_interactions}""",
    output_key="behavior_analysis",
)

# Task: adapt_content_strategy
# Consumes: behavior_analysis
# Produces: content_strategy
ADAPT_CONTENT_STRATEGY = AgentTask(
    task_id="adapt_content_strategy",
    agent_role=AgentRole.WRITER,  # adaptator role
    prompt="""Adapt content generation strategy by adjusting difficulty, style, pacing, or focus based on the following analysis.

Behavior analysis: {behavior_analysis}
Topic: {topic}""",
    output_key="content_strategy",
    dependencies=["analyze_user_behavior"],
)

# Task: generate_adaptive_block
# Consumes: content_strategy
# Produces: adaptive_block
GENERATE_ADAPTIVE_BLOCK = AgentTask(
    task_id="generate_adaptive_block",
    agent_role=AgentRole.WRITER,  # generator role
    prompt="""Generate a content block following the specified strategy.

Block type: {block_type}
Topic: {topic}
Strategy: {content_strategy}""",
    output_key="content_block",
    dependencies=["adapt_content_strategy"],
)

# ============================================================================
# Tasks for StreamingContentWorkflow
# Pattern: Generate Block 1 → Stream → Generate Block 2 → Stream → ...
# ============================================================================

# Task: generate_streaming_block
# Produces: streaming_block
GENERATE_STREAMING_BLOCK = AgentTask(
    task_id="generate_streaming_block",
    agent_role=AgentRole.WRITER,  # generator role
    prompt="""Generate the next content block in sequence, based on draft, and maintaining continuity with previous content.

Block type: {block_type}
Draft: {content_block}
Topic: {topic}
Previous stream: {content_stream}""",
    output_key="stream_block",
)

# Task: stream_content_block
# Consumes: stream_block
# Produces: content_stream
STREAM_CONTENT_BLOCK = AgentTask(
    task_id="stream_content_block",
    agent_role=AgentRole.STREAMER,  # streamer role
    prompt="""Stream content to user interface progressively, managing the buffer size. Append blocks to the content stream.

Buffer size: {buffer_size}
Stream block: {stream_block}
Previous stream: {content_stream}
""",
    output_key="content_stream",
    dependencies=["generate_streaming_block"],
)
