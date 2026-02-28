"""Unit tests for construct_hint tool.

Anchored to: COMPANION_PRD §5.1, COMPANION_LOGIC_FLOW strategy table.
"""

import pytest

from tools.hints import construct_hint

pytestmark = pytest.mark.unit

REQUIRED_KEYS = {
    "hint_id",
    "strategy",
    "hint_content",
    "follow_up_questions",
    "difficulty_level",
    "expected_response_type",
}

VALID_STRATEGIES = {"socratic", "analogy", "decompose", "confront"}


# ---- Schema ----------------------------------------------------------------

class TestReturnSchema:

    def test_returns_required_keys(self):
        result = construct_hint(
            student_id="s1",
            current_input="force = mass * velocity",
            target_concept="newton_second_law",
        )
        assert REQUIRED_KEYS.issubset(result.keys())

    def test_follow_up_questions_not_empty(self):
        result = construct_hint("s1", "I don't know", "momentum")
        assert isinstance(result["follow_up_questions"], list)
        assert len(result["follow_up_questions"]) > 0

    def test_difficulty_level_in_range(self):
        result = construct_hint("s1", "something", "energy")
        assert 0.0 <= result["difficulty_level"] <= 1.0

    def test_hint_id_unique_across_calls(self):
        r1 = construct_hint("s1", "input a", "concept_a")
        r2 = construct_hint("s1", "input b", "concept_b")
        assert r1["hint_id"] != r2["hint_id"]


# ---- Strategy selection by error type --------------------------------------

class TestStrategySelection:
    """PRD strategy table: conceptual->socratic, calculation->decompose,
    vocabulary->analogy, default->socratic."""

    def test_strategy_socratic_for_conceptual_error(self):
        result = construct_hint(
            "s1", "force = mass * velocity", "newton_second_law",
            error_analysis={"type": "conceptual"},
        )
        assert result["strategy"] == "socratic"

    def test_strategy_decompose_for_calculation_error(self):
        result = construct_hint(
            "s1", "2 + 3 = 6", "arithmetic",
            error_analysis={"type": "calculation"},
        )
        assert result["strategy"] == "decompose"

    def test_strategy_analogy_for_vocabulary_error(self):
        result = construct_hint(
            "s1", "momentum is the same as inertia", "momentum",
            error_analysis={"type": "vocabulary"},
        )
        assert result["strategy"] == "analogy"

    def test_strategy_defaults_to_socratic(self):
        result = construct_hint("s1", "I'm confused", "force")
        assert result["strategy"] == "socratic"


# ---- Content quality -------------------------------------------------------

class TestHintContent:

    def test_hint_content_never_contains_direct_answer(self):
        """Iron Rule 1: hint guides, never gives direct answers."""
        result = construct_hint(
            "s1", "What is F=ma?", "newton_second_law",
        )
        content = result["hint_content"].lower()
        assert "the answer is" not in content
        assert "the solution is" not in content


# ---- Strategy auto-switching (not yet implemented) -------------------------

class TestStrategyAutoSwitch:

    @pytest.mark.xfail(
        reason="construct_hint does not yet read student history "
               "for auto-switching (PRD: >=3 same-strategy errors -> switch)",
        strict=True,
    )
    def test_strategy_switch_after_3_consecutive_errors(self, seed_cognitive_model):
        """After >=3 consecutive errors on the same concept with the same
        strategy, construct_hint MUST return a different strategy."""
        seed_cognitive_model(
            student_id="s1",
            concepts={
                "force": {
                    "confidence": 0.2,
                    "consecutive_errors": 3,
                    "total_attempts": 3,
                    "last_strategy": "socratic",
                    "last_updated": "2024-01-01T00:00:00+00:00",
                },
            },
        )
        result = construct_hint(
            student_id="s1",
            current_input="force = mass * velocity",
            target_concept="force",
            error_analysis={"type": "conceptual"},
        )
        assert result["strategy"] != "socratic"

    @pytest.mark.xfail(
        reason="No error_analysis type currently maps to 'confront'",
        strict=True,
    )
    def test_confront_strategy_available(self):
        """The 'confront' strategy must be selectable for stubborn
        misconceptions. PRD defines 4 strategies, all must be reachable."""
        result = construct_hint(
            "s1",
            "force IS mass times velocity, I'm certain",
            "force",
            error_analysis={"type": "stubborn_misconception"},
        )
        assert result["strategy"] == "confront"
