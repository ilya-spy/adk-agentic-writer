"""Content validation agent (static / schema-based).

Validates LLM-generated content against schema expectations for all
built-in content types (quiz, story, game, simulation).
Performs light corrections (score/tier consistency, passing_score range)
and logs warnings.

Inherits from StatefulAgent so it participates in workflows
(e.g. ValidationEditorialWorkflow) alongside writers.

Used by coordinators in a writer → validator workflow.
Subclassed by GeminiValidator for future LLM-assisted validation.
"""

import logging
from typing import Any, Dict, List, Optional

from ...models.agent_models import AgentConfig, AgentModel, AgentTask
from ...tasks.editorial_tasks import VALIDATE_CONTENT
from ...teams.editorial_team import CONTENT_VALIDATOR as CONTENT_VALIDATOR_CONFIG
from ..stateful_agent import StatefulAgent

logger = logging.getLogger(__name__)


class ContentValidator(StatefulAgent):
    """Validates writer-generated content for all built-in types.

    Supports:
    - quiz: field presence, tier/score consistency, passing_score range
    - story/branched_narrative: node structure, start/ending presence
    - game/quest_game: node structure, title/description
    - simulation/web_simulation: variables, controls, rules

    Usage (standalone):
        validator = ContentValidator()
        warnings = validator.validate(result_dict, "quiz")

    Usage (as StatefulAgent in workflow):
        result = await validator.process_task(task, params)
        # result = {"content": ..., "validation_result": "...", "warnings": [...]}
    """

    _TIER_SCORE = {"low": 1, "mid": 2, "high": 3}

    def __init__(
        self,
        agent_id: str = "content_validator",
        config: Optional[AgentConfig] = None,
        model: Optional[AgentModel] = None,
    ):
        if config is None:
            config = CONTENT_VALIDATOR_CONFIG
        if model is None:
            model = AgentModel(name=agent_id)
        super().__init__(agent_id=agent_id, config=config, model=model)

        # Register the VALIDATE_CONTENT task
        self.supported_tasks.append(VALIDATE_CONTENT)

        logger.info("Initialized ContentValidator: %s", agent_id)

    # ------------------------------------------------------------------
    # StatefulAgent task execution
    # ------------------------------------------------------------------

    async def _execute_task(
        self, task: AgentTask, resolved_prompt: str
    ) -> Dict[str, Any]:
        """Execute validation as a task in a workflow.

        Reads from self.parameters (set by process_task → update_parameters)
        because ValidationEditorialWorkflow injects the writer's result
        as params["content"] at runtime, not in the original task.parameters.

        Expected parameters:
            - content: dict — the writer-produced content to validate
            - content_type: str — "quiz", "story", etc.

        Returns:
            {"content": <original>, "validation_result": <summary>,
             "warnings": [...], "status": "validated"}
        """
        # Merge: self.parameters has runtime params; task.parameters has template ones
        params = {**(task.parameters or {}), **self.parameters}
        content = params.get("content", {})
        content_type = params.get("content_type", "")

        if not content:
            logger.warning("[%s] No content to validate", self.agent_id)
            return {
                "content": content,
                "validation_result": "no content provided",
                "warnings": [],
                "status": "skipped",
            }

        warnings = self.validate(content, content_type)

        summary = (
            f"{len(warnings)} warning(s)" if warnings else "validation passed (clean)"
        )

        return {
            "content": content,
            "validation_result": summary,
            "warnings": warnings,
            "status": "validated",
        }

    # ------------------------------------------------------------------
    # Public API (direct invocation, also used by _execute_task)
    # ------------------------------------------------------------------

    def validate(
        self,
        result: Dict[str, Any],
        content_type: str,
    ) -> List[str]:
        """Validate and lightly correct content fields.

        Mutates *result* in-place for light corrections
        (score ↔ tier consistency, passing_score range).

        Returns:
            List of warning strings (empty = clean).
        """
        warnings: List[str] = []

        if content_type == "quiz":
            self._validate_quiz(result, warnings)
        elif content_type in ("story", "branched_narrative"):
            self._validate_story(result, warnings)
        elif content_type in ("game", "quest_game"):
            self._validate_game(result, warnings)
        elif content_type in ("simulation", "web_simulation"):
            self._validate_simulation(result, warnings)

        if warnings:
            for w in warnings:
                logger.warning("[%s] %s", self.agent_id, w)
            logger.info(
                "[%s] %s validation: %d warning(s)",
                self.agent_id,
                content_type,
                len(warnings),
            )
        else:
            logger.info(
                "[%s] %s validation passed (clean)", self.agent_id, content_type
            )

        return warnings

    # ------------------------------------------------------------------
    # Quiz validation
    # ------------------------------------------------------------------

    def _validate_quiz(self, result: Dict[str, Any], warnings: List[str]) -> None:
        if "title" not in result:
            warnings.append("Quiz missing 'title'")
        if "questions" not in result:
            warnings.append("Quiz missing 'questions' array")
        elif isinstance(result["questions"], list):
            self._validate_quiz_questions(result["questions"], warnings)
            self._validate_quiz_tiers(result["questions"], warnings)
            self._validate_quiz_passing_score(result, warnings)
        if "time_limit" not in result:
            warnings.append("Quiz missing 'time_limit' (LLM should recommend one)")

    def _validate_quiz_questions(self, questions: list, warnings: List[str]) -> None:
        """Check individual question fields."""
        for i, q in enumerate(questions):
            if not isinstance(q, dict):
                warnings.append(f"Question {i} is not a dict")
                continue
            if "question" not in q:
                warnings.append(f"Question {i} missing 'question' text")
            if "options" not in q:
                warnings.append(f"Question {i} missing 'options'")
            elif not isinstance(q["options"], list) or len(q["options"]) < 2:
                warnings.append(f"Question {i} has invalid options (need >= 2)")
            if "correct_answer" not in q:
                warnings.append(f"Question {i} missing 'correct_answer'")
            if "explanation" not in q:
                warnings.append(f"Question {i} missing 'explanation'")

    def _validate_quiz_tiers(self, questions: list, warnings: List[str]) -> None:
        """Check tier presence and fix score ↔ tier consistency."""
        dict_qs = [q for q in questions if isinstance(q, dict)]
        if not dict_qs:
            return

        # Warn if not all 3 tiers present
        tiers_found = {q.get("tier") for q in dict_qs if q.get("tier")}
        if tiers_found and not tiers_found >= {"low", "mid", "high"}:
            warnings.append(
                f"Quiz only has tiers {tiers_found}, " "expected all of low/mid/high"
            )

        # Fix score to match tier
        for i, q in enumerate(dict_qs):
            tier = q.get("tier")
            if tier in self._TIER_SCORE:
                expected = self._TIER_SCORE[tier]
                if q.get("score") != expected:
                    warnings.append(
                        f"Q{i} tier={tier} score " f"{q.get('score')}→{expected}"
                    )
                    q["score"] = expected
            elif q.get("score") not in (1, 2, 3):
                q["score"] = 1  # safe fallback

    def _validate_quiz_passing_score(
        self, result: Dict[str, Any], warnings: List[str]
    ) -> None:
        """Validate and correct passing_score range (50-85% of total)."""
        dict_qs = [q for q in result["questions"] if isinstance(q, dict)]
        total_pts = sum(q.get("score", 1) for q in dict_qs)
        passing = result.get("passing_score")

        if total_pts <= 0:
            return

        if not isinstance(passing, (int, float)):
            corrected = max(1, round(total_pts * 0.65))
            warnings.append(
                f"Quiz missing passing_score, set to {corrected}/{total_pts}"
            )
            result["passing_score"] = corrected
        else:
            pct = passing / total_pts
            if not (0.50 <= pct <= 0.85):
                corrected = max(1, round(total_pts * 0.65))
                warnings.append(
                    f"Quiz passing_score={passing}/{total_pts} "
                    f"({pct:.0%}) outside 50-85%, corrected to {corrected}"
                )
                result["passing_score"] = corrected

    # ------------------------------------------------------------------
    # Story validation
    # ------------------------------------------------------------------

    def _validate_story(self, result: Dict[str, Any], warnings: List[str]) -> None:
        if "title" not in result:
            warnings.append("Story missing 'title'")
        if "nodes" not in result:
            warnings.append("Story missing 'nodes' dict")
        elif isinstance(result["nodes"], dict):
            if "start" not in result["nodes"]:
                warnings.append("Story missing 'start' node")
            has_ending = any(
                n.get("is_ending", False)
                for n in result["nodes"].values()
                if isinstance(n, dict)
            )
            if not has_ending:
                warnings.append("Story has no ending nodes")
            for nid, node in result["nodes"].items():
                if not isinstance(node, dict):
                    warnings.append(f"Node '{nid}' is not a dict")
                    continue
                if "content" not in node:
                    warnings.append(f"Node '{nid}' missing 'content'")
                if not node.get("is_ending") and not node.get("branches"):
                    warnings.append(f"Non-ending node '{nid}' has no branches")
        if "synopsis" not in result and "description" not in result:
            warnings.append("Story missing 'synopsis'")

    # ------------------------------------------------------------------
    # Game validation
    # ------------------------------------------------------------------

    def _validate_game(self, result: Dict[str, Any], warnings: List[str]) -> None:
        if "title" not in result:
            warnings.append("Game missing 'title'")
        if "nodes" not in result:
            warnings.append("Game missing 'nodes'")
        elif isinstance(result["nodes"], dict):
            for nid, node in result["nodes"].items():
                if not isinstance(node, dict):
                    warnings.append(f"Game node '{nid}' is not a dict")
                    continue
                if "title" not in node and "description" not in node:
                    warnings.append(f"Game node '{nid}' missing title/description")

    # ------------------------------------------------------------------
    # Simulation validation
    # ------------------------------------------------------------------

    def _validate_simulation(self, result: Dict[str, Any], warnings: List[str]) -> None:
        if "title" not in result:
            warnings.append("Simulation missing 'title'")
        if "variables" not in result:
            warnings.append("Simulation missing 'variables'")
        if "controls" not in result:
            warnings.append("Simulation missing 'controls'")
        if "rules" not in result:
            warnings.append("Simulation missing 'rules'")


__all__ = ["ContentValidator"]
