"""Quiz format specification."""

from ..models.content_models import Quiz
from .base import FormatSpec, ParamSpec

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
  "passing_score": 6,
  "time_limit": 10
}

CRITICAL scoring rules:
- tier MUST be one of exactly: "low", "mid", "high" (NOT the overall difficulty name)
- score MUST match the tier: low=1, mid=2, high=3
- The quiz MUST contain at least one question at EACH tier (low, mid, high)
- passing_score = integer in range 60-80%% of total points (sum of all question scores).
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
        ParamSpec("difficulty", "str", "medium", "Overall difficulty: easy, medium, hard"),
        ParamSpec("num_options", "int", 4, "Answer options per question"),
    ],
    schema_description=QUIZ_SCHEMA,
    sample_output=QUIZ_SAMPLE,
    writer_instruction="""\
You are an expert content creator specializing in interactive and engaging content.
You create engaging educational quizzes with clear, thought-provoking questions,
helpful explanations, and varying difficulty levels.

CRITICAL: Respond with valid JSON only. No markdown, no explanations, no code blocks.
The JSON must exactly match the schema structure provided.""",
    writer_prompt="""\
Generate an educational {flavor} about "{topic}".

The overall TOPIC difficulty is "{difficulty}" — this controls how hard the question
CONTENT is (e.g. easy = beginner-friendly facts, hard = advanced/tricky knowledge).

IMPORTANT -- follow ALL of these rules precisely:

1. Create exactly {num_questions} questions.
2. Each question MUST have exactly {num_options} answer options.
3. Include a brief explanation for each answer.
4. SCORING TIERS:
   Every quiz MUST contain a MIX of three scoring tiers:
     - "low"  tier = 1 point  (straightforward recall)
     - "mid"  tier = 2 points (requires understanding)
     - "high" tier = 3 points (requires analysis / synthesis)
   Include at least one question at EACH tier. Distribute evenly.
5. Create questions wisely, according to global quiz difficulty.
6. Try creative question sequences, not simply round-robin from low to high tiers.""",
    reviewer_prompt="""\
Review this quiz content. Check:
- All questions have the correct number of options
- correct_answer index is within bounds for each question
- Each tier (low/mid/high) is represented
- score matches tier (low=1, mid=2, high=3)
- passing_score is 60-80%% of total points
- Questions are engaging and educationally sound""",
    refiner_prompt="""\
Refine this quiz. Fix any issues from the review. Ensure:
- Tier distribution is balanced
- Explanations are clear and educational
- Questions are engaging and at appropriate difficulty
- All structural rules are met""",
    flavors=["quiz", "trivia", "test"],
    temperature=0.7,
    max_tokens=1536,
)
