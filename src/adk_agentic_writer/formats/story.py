"""Story / branched narrative format specification."""

from ..models.content_models import BranchedNarrative
from .base import FormatSpec, ParamSpec

STORY_SCHEMA = """\
Output JSON Schema:
{
  "title": "string - Story title",
  "synopsis": "string - Brief story overview",
  "genre": "string - Story genre",
  "start_node": "start",
  "nodes": {
    "start": {
      "node_id": "start",
      "content": "string - Opening narrative",
      "branches": [{"text": "choice", "next_node_id": "node_0"}],
      "tags": ["opening"],
      "is_ending": false
    },
    "ending_0": {
      "node_id": "ending_0",
      "content": "string - Ending narrative",
      "branches": [],
      "tags": ["ending"],
      "is_ending": true
    }
  },
  "characters": ["string"]
}"""

STORY_SAMPLE = {
    "title": "The Quest for Knowledge",
    "synopsis": "An adventure through the realm of learning",
    "genre": "fantasy",
    "start_node": "start",
    "nodes": {
        "start": {
            "node_id": "start",
            "content": "You stand at the entrance of the ancient library...",
            "branches": [
                {"text": "Enter through the main door", "next_node_id": "node_0"},
            ],
            "tags": ["opening"],
            "is_ending": False,
        },
        "ending_0": {
            "node_id": "ending_0",
            "content": "You emerge victorious with newfound wisdom...",
            "branches": [],
            "tags": ["ending", "victory"],
            "is_ending": True,
        },
    },
    "characters": ["Protagonist", "The Keeper"],
}

STORY_FORMAT = FormatSpec(
    name="story",
    label="Branched Narrative",
    model_class=BranchedNarrative,
    default_params={"genre": "fantasy", "num_nodes": 7},
    parameter_specs=[
        ParamSpec("genre", "str", "fantasy", "Story genre: fantasy, scifi, mystery, adventure"),
        ParamSpec("num_nodes", "int", 7, "Approximate number of story nodes"),
    ],
    schema_description=STORY_SCHEMA,
    sample_output=STORY_SAMPLE,
    writer_instruction="""\
You are an expert content creator specializing in interactive and engaging content.
You create immersive branched narratives with compelling opening hooks,
multiple story paths and endings, rich descriptive content,
and meaningful choices that affect the story.

CRITICAL: Respond with valid JSON only. No markdown, no explanations, no code blocks.
The JSON must exactly match the schema structure provided.""",
    writer_prompt="""\
Create a branched interactive narrative about "{topic}".

Requirements:
- Genre: {genre}
- Create approximately {num_nodes} story nodes
- Include a "start" node as the entry point
- Include at least 2 different endings (ending_0, ending_1, etc.)
- Each non-ending node should have 1-3 branches (choices)
- Branches format: {{"text": "choice text", "next_node_id": "node_id"}}

Make the story engaging with vivid descriptions and meaningful choices.""",
    reviewer_prompt="""\
Review this branched narrative. Check:
- A "start" node exists
- All branch next_node_id values reference existing nodes
- At least 2 ending nodes (is_ending=true)
- No orphaned nodes (unreachable from start)
- Content is vivid and engaging
- Choices are meaningful and distinct""",
    refiner_prompt="""\
Refine this branched narrative. Fix any issues from the review. Ensure:
- All node references are valid
- Branch structure is consistent
- Content is vivid with rich descriptions
- Choices feel meaningful to the reader""",
    aliases=["narrative", "branched_narrative", "adventure"],
    temperature=0.85,
    max_tokens=2048,
)
