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


# ---- Output filter ---------------------------------------------------------

class TestOutputFilter:

    def test_contains_direct_answer_detected(self):
        """_contains_direct_answer must catch known direct-answer patterns."""
        from tools.hints import _contains_direct_answer
        assert _contains_direct_answer("The answer is 42.")
        assert _contains_direct_answer("The formula is F=ma.")
        assert _contains_direct_answer("The solution is to multiply.")

    def test_safe_content_passes_filter(self):
        from tools.hints import _contains_direct_answer
        assert not _contains_direct_answer(
            "What do you think happens when you apply more force?"
        )
        assert not _contains_direct_answer(
            "Let's think about what force really means."
        )


# ---- Strategy auto-switching (not yet implemented) -------------------------

class TestStrategyAutoSwitch:

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

    def test_confront_strategy_for_misconception_error(self):
        """The 'confront' strategy must be selected for error_analysis
        type='misconception'.  PRD defines 4 strategies; all must be
        reachable via the error-type mapping."""
        result = construct_hint(
            "s1",
            "force IS mass times velocity, I'm certain",
            "force",
            error_analysis={"type": "misconception"},
        )
        assert result["strategy"] == "confront"


# ---- Difficulty mapping from confidence ------------------------------------

class TestDifficultyMapping:

    def test_low_confidence_produces_low_difficulty(self, seed_cognitive_model):
        """A student with low confidence should receive an easier hint
        (lower difficulty_level)."""
        seed_cognitive_model(
            student_id="s-diff-lo",
            concepts={"force": {
                "confidence": 0.15,
                "consecutive_errors": 0,
                "total_attempts": 1,
                "last_strategy": None,
                "last_updated": "2024-01-01T00:00:00+00:00",
            }},
        )
        result = construct_hint("s-diff-lo", "I'm confused", "force")
        assert result["difficulty_level"] <= 0.3

    def test_high_confidence_produces_high_difficulty(self, seed_cognitive_model):
        """A student with high confidence gets a harder hint."""
        seed_cognitive_model(
            student_id="s-diff-hi",
            concepts={"force": {
                "confidence": 0.9,
                "consecutive_errors": 0,
                "total_attempts": 5,
                "last_strategy": None,
                "last_updated": "2024-01-01T00:00:00+00:00",
            }},
        )
        result = construct_hint("s-diff-hi", "almost there", "force")
        assert result["difficulty_level"] >= 0.7


# ---- Template content varies by strategy -----------------------------------

class TestTemplateContentVariation:

    def test_each_strategy_produces_distinct_content(self):
        """The four strategies must generate meaningfully different hint
        content so students don't see the same template repeatedly."""
        contents = {}
        for error_type, expected_strat in [
            ("conceptual", "socratic"),
            ("calculation", "decompose"),
            ("vocabulary", "analogy"),
            ("misconception", "confront"),
        ]:
            result = construct_hint(
                "s-tmpl", "wrong answer", "force",
                error_analysis={"type": error_type},
            )
            assert result["strategy"] == expected_strat
            contents[expected_strat] = result["hint_content"]

        unique_contents = set(contents.values())
        assert len(unique_contents) == 4, (
            f"Expected 4 distinct hint templates, got {len(unique_contents)}"
        )
