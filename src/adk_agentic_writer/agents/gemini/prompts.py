"""Prompts for Gemini-powered content generation.

Centralized prompt templates for ADK agents. Each content type has:
- SYSTEM_INSTRUCTION: Base instruction for the agent
- GENERATION_PROMPT: Template for content generation requests
- EXAMPLE_OUTPUT: Sample output to guide structured generation
"""

from typing import Dict, Any

# =============================================================================
# Common Instructions
# =============================================================================

COMMON_INSTRUCTION = """You are an expert content creator specializing in interactive educational content.
Your responses must be valid JSON matching the exact schema provided.
Be creative, engaging, and educational. Ensure all content is appropriate for general audiences."""

JSON_OUTPUT_INSTRUCTION = """
CRITICAL: You MUST respond with valid JSON only. No markdown, no explanations, no code blocks.
The JSON must exactly match the schema structure provided."""

# =============================================================================
# Quiz Generation Prompts
# =============================================================================

QUIZ_SYSTEM_INSTRUCTION = f"""{COMMON_INSTRUCTION}

You create engaging educational quizzes with:
- Clear, thought-provoking questions
- 4 distinct answer options (1 correct, 3 plausible distractors)
- Helpful explanations for the correct answer
- Varying difficulty levels

{JSON_OUTPUT_INSTRUCTION}"""

QUIZ_GENERATION_PROMPT = """Generate an educational quiz about "{topic}".

Requirements:
- Create exactly {num_questions} questions
- Difficulty level: {difficulty}
- Each question must have exactly 4 options
- correct_answer is the 0-based index of the correct option
- Include a brief explanation for each answer

Topic context: Create engaging, factual questions that test understanding of {topic}.
Make questions progressively more challenging if difficulty is "medium" or "hard"."""

QUIZ_SCHEMA_DESCRIPTION = """
Output JSON Schema:
{
  "title": "string - Engaging quiz title",
  "description": "string - Brief quiz description",
  "questions": [
    {
      "question": "string - The question text",
      "options": ["string", "string", "string", "string"],
      "correct_answer": 0-3,
      "explanation": "string - Why this answer is correct",
      "difficulty": "easy|medium|hard"
    }
  ],
  "passing_score": 70,
  "time_limit": null
}"""

# =============================================================================
# Story/Narrative Generation Prompts
# =============================================================================

STORY_SYSTEM_INSTRUCTION = f"""{COMMON_INSTRUCTION}

You create immersive branched narratives with:
- Compelling opening hooks
- Multiple story paths and endings
- Rich descriptive content
- Meaningful choices that affect the story

{JSON_OUTPUT_INSTRUCTION}"""

STORY_GENERATION_PROMPT = """Create a branched interactive narrative about "{topic}".

Requirements:
- Genre: {genre}
- Create approximately {num_nodes} story nodes
- Include a "start" node as the entry point
- Include at least 2 different endings (ending_0, ending_1, etc.)
- Each non-ending node should have 1-3 branches (choices)
- Branches format: {{"text": "choice text", "next_node_id": "node_id"}}

Make the story engaging with vivid descriptions and meaningful choices."""

STORY_SCHEMA_DESCRIPTION = """
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
    "node_0": {...},
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

# =============================================================================
# Block-level Generation Prompts
# =============================================================================

QUESTION_BLOCK_PROMPT = """Generate a single quiz question about "{topic}".

Difficulty: {difficulty}
Context: {context}

Create an engaging question with 4 options where option at index {correct_index} is correct."""

STORY_NODE_PROMPT = """Generate a story node for an interactive narrative.

Node ID: {node_id}
Topic: {topic}
Genre: {genre}
Node type: {node_type}
Previous context: {previous_context}

Create immersive content appropriate for this node's position in the story."""

# =============================================================================
# Prompt Builder Functions
# =============================================================================


def build_quiz_prompt(
    topic: str, num_questions: int = 5, difficulty: str = "medium", **kwargs
) -> str:
    """Build complete quiz generation prompt."""
    prompt = QUIZ_GENERATION_PROMPT.format(
        topic=topic, num_questions=num_questions, difficulty=difficulty
    )
    return f"{prompt}\n\n{QUIZ_SCHEMA_DESCRIPTION}"


def build_story_prompt(
    topic: str, num_nodes: int = 7, genre: str = "fantasy", **kwargs
) -> str:
    """Build complete story generation prompt."""
    prompt = STORY_GENERATION_PROMPT.format(
        topic=topic, num_nodes=num_nodes, genre=genre
    )
    return f"{prompt}\n\n{STORY_SCHEMA_DESCRIPTION}"


def get_system_instruction(content_type: str) -> str:
    """Get system instruction for content type."""
    instructions = {
        "quiz": QUIZ_SYSTEM_INSTRUCTION,
        "trivia": QUIZ_SYSTEM_INSTRUCTION,
        "test": QUIZ_SYSTEM_INSTRUCTION,
        "story": STORY_SYSTEM_INSTRUCTION,
        "narrative": STORY_SYSTEM_INSTRUCTION,
        "branched_narrative": STORY_SYSTEM_INSTRUCTION,
        "adventure": STORY_SYSTEM_INSTRUCTION,
    }
    return instructions.get(content_type, COMMON_INSTRUCTION)


def build_generation_prompt(task_id: str, params: Dict[str, Any]) -> str:
    """Build generation prompt based on task ID."""
    builders = {
        "generate_quiz": build_quiz_prompt,
        "generate_story": build_story_prompt,
    }
    builder = builders.get(task_id)
    if builder:
        return builder(**params)
    return f"Generate content about {params.get('topic', 'the topic')}"


# =============================================================================
# Sample Outputs for Training/Validation
# =============================================================================

SAMPLE_QUIZ_OUTPUT = {
    "title": "Python Programming Fundamentals",
    "description": "Test your knowledge of Python basics",
    "questions": [
        {
            "question": "What is the correct way to define a function in Python?",
            "options": [
                "function myFunc():",
                "def myFunc():",
                "func myFunc():",
                "define myFunc():",
            ],
            "correct_answer": 1,
            "explanation": "In Python, functions are defined using the 'def' keyword.",
            "difficulty": "easy",
        }
    ],
    "passing_score": 70,
    "time_limit": None,
}

SAMPLE_STORY_OUTPUT = {
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
                {"text": "Search for a side entrance", "next_node_id": "node_1"},
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


__all__ = [
    "QUIZ_SYSTEM_INSTRUCTION",
    "STORY_SYSTEM_INSTRUCTION",
    "COMMON_INSTRUCTION",
    "build_quiz_prompt",
    "build_story_prompt",
    "build_generation_prompt",
    "get_system_instruction",
    "SAMPLE_QUIZ_OUTPUT",
    "SAMPLE_STORY_OUTPUT",
]
