"""Quiz format specification and normalization."""

import math
from typing import Dict

from ..models.content_models import Quiz
from .base import FormatSpec, ParamSpec

_QUESTION_ALLOWED_KEYS = {"question", "options", "correct_answer", "explanation", "tier", "score"}
_TIER_FROM_SCORE = {1: "low", 2: "mid", 3: "high"}


def normalize_quiz(data: Dict) -> Dict:
    """Strip non-schema fields and default missing tier / passing_score."""
    for q in data.get("questions", []):
        if "tier" not in q:
            q["tier"] = _TIER_FROM_SCORE.get(q.get("score", 1), "mid")
        for k in set(q.keys()) - _QUESTION_ALLOWED_KEYS:
            del q[k]

    total = data.get("total_score", 0)
    if not data.get("passing_score") and total:
        data["passing_score"] = math.ceil(total * 0.7)

    return data

QUIZ_SCHEMA = """\
Output JSON Schema:
{
  "title": "string - Engaging quiz title",
  "description": "string - Brief quiz description",
  "questions": [
    {
      "question": "string - The question text",
      "options": ["string", "string", ...],
      "correct_answer": 0,
      "explanation": "string - Why this answer is correct",
      "tier": "low|mid|high",
      "score": 1
    }
  ],
  "total_score": 18,
  "passing_score": 6,
  "time_limit": 10
}

STRICT FIELD RULES (violating these is an error):
- Output ONLY the fields shown above. Do NOT add "id", "answer", "category",
  "question_text", or any other field not in the schema.
- correct_answer MUST be a zero-based INTEGER index
  (0 = first option, 1 = second, …). NEVER a letter ("B"), NEVER the answer text.
- Every question MUST include "tier" with value "low", "mid", or "high".
- passing_score MUST be present as an integer (60-80%% of total_score).
- options MUST be plain strings, NOT objects.

CRITICAL scoring rules:
- tier MUST be one of exactly: "low", "mid", "high" (NOT the overall difficulty name)
- score MUST match the tier: low=1, mid=2, high=3
- The quiz MUST contain at least one question at EACH tier (low, mid, high)
- total_score MUST equal the sum of all question score values (verify by adding scores).
- passing_score = integer in range 60-80%% of total points (same as total_score maximum).
- time_limit = integer minutes, reasonable for the question count and difficulty.
- Vary correct_answer index across questions"""

QUIZ_SAMPLE = {
    "title": "This Is a Super Engaging Quiz Title",
    "description": "A short, compelling description of the quiz topic",
    "questions": [
        {
            "question": "What is the hardest natural substance on Earth?",
            "options": ["Diamond", "Granite", "Titanium", "Quartz"],
            "correct_answer": 0,
            "explanation": "Diamond scores 10 on the Mohs hardness scale.",
            "tier": "mid",
            "score": 2,
        },
    ],
    "total_score": 2,
    "passing_score": 4,
    "time_limit": 5,
}

QUIZ_FORMAT = FormatSpec(
    name="quiz",
    label="Quiz",
    model_class=Quiz,
    default_params={
        "num_questions": 5,
        "difficulty": "medium",
        "num_options": 4,
        "passing_score": 70,
    },
    parameter_specs=[
        ParamSpec("topic", "str", "", "Content topic"),
        ParamSpec("flavor", "str", "quiz", "Content flavor"),
        ParamSpec("num_questions", "int", 5, "Number of questions"),
        ParamSpec(
            "difficulty", "str", "medium", "Overall difficulty: easy, medium, hard"
        ),
        ParamSpec("num_options", "int", 4, "Answer options per question"),
    ],
    schema_description=QUIZ_SCHEMA,
    sample_output=QUIZ_SAMPLE,
    writer_instruction="""\
You are an expert content creator specializing in interactive educational content.
You create well-crafted quizzes with clear, thought-provoking questions,
helpful explanations, and varying difficulty levels.
If creative direction and reasoning are provided, use them to guide your content creation style and approach.

CRITICAL: Respond with valid JSON only. No markdown, no explanations, no code blocks.
Do NOT include any commentary, analysis, or discussion of search results.
Your entire response must be a single JSON object matching the schema structure provided.""",
    writer_prompt="""\
Generate an educational {flavor} about "{topic}".

STYLE — adapt to the "{flavor}" format:
- "quiz": Standard educational quiz with clear learning objectives.
- "trivia": Surprising or lesser-known facts; concise, well-paced questions. Match tone to the subject matter.
- "test": Rigorous assessment; well-structured, formal tone.

DIFFICULTY — the overall difficulty is "{difficulty}":
- "easy": Keep questions simple and straightforward, suitable for beginners.
- "medium": Include nuanced questions that require deeper understanding.
- "hard": Make questions challenging, testing advanced knowledge and critical thinking.

RULES — follow ALL of these precisely:

1. Create exactly {num_questions} questions.
2. Most question MUST have exactly {num_options} answer options (not more, not fewer).
3. Include a brief explanation for each answer.
4. SCORING TIERS:
   Every quiz MUST contain a MIX of three scoring tiers:
     - "low"  tier = 1 point  (straightforward recall)
     - "mid"  tier = 2 points (requires understanding)
     - "high" tier = 3 points (requires analysis / synthesis)
   Include at least one question at EACH tier. Distribute evenly.
5. Set "total_score" to the exact sum of all per-question score values (maximum achievable points).
6. Create questions wisely, combining global difficulty with per-question tier.
7. Try creative question sequences, not simply round-robin from low to high tiers.

TONE AWARENESS:
Analyze the topic before writing. Derive your tone, vocabulary, and atmosphere
from what the subject matter demands. Serious or sensitive topics require
a respectful, measured approach. Lighthearted topics allow a more casual,
playful voice. Never impose a default "fun" or "upbeat" tone -- let the topic lead.""",
    reviewer_prompt="""\
Review this quiz content. Check:
- All questions have the correct number of options
- correct_answer index is within bounds for each question
- Each tier (low/mid/high) is represented
- score matches tier (low=1, mid=2, high=3)
- total_score equals the sum of all question scores
- passing_score is 60-80%% of total points
- Questions are engaging and educationally sound""",
    refiner_prompt="""\
Refine this quiz. Fix any issues from the review. Ensure:
- Tier distribution is balanced
- total_score matches the sum of question scores
- Explanations are clear and educational
- Questions are engaging and at appropriate difficulty
- All structural rules are met""",
    flavors=["trivia", "test"],
    temperature=0.7,
    max_tokens=1536,
)
