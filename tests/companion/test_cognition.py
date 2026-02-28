"""Unit tests for update_student_cognition_map tool.

Anchored to: COMPANION_PRD §5.3, COMPANION_LOGIC_FLOW Phase 4 confidence table.
"""

import pytest

from memory.shared import shared_memory
from tools.cognition import (
    FAST_RESPONSE_THRESHOLD,
    _DELTA_CORRECT_FAST,
    _DELTA_CORRECT_SLOW,
    _DELTA_INCORRECT,
    _LOW_CONFIDENCE_THRESHOLD,
    _detect_misconception,
    _infer_misconception_pattern,
    update_student_cognition_map,
)

pytestmark = pytest.mark.unit

REQUIRED_KEYS = {
    "updated_concepts",
    "new_misconceptions",
    "confidence_changes",
    "recommended_focus_areas",
}


# ---- Schema ----------------------------------------------------------------

class TestReturnSchema:

    def test_returns_required_keys(self, make_interaction_data):
        result = update_student_cognition_map("s1", make_interaction_data())
        assert REQUIRED_KEYS.issubset(result.keys())


# ---- D-S confidence deltas -------------------------------------------------

class TestConfidenceDeltas:
    """Logic Flow Phase 4: confidence update rules."""

    def test_correct_fast_increases_confidence_by_020(self, make_interaction_data):
        data = make_interaction_data(is_correct=True, time_spent=10.0, help_requests=0)
        result = update_student_cognition_map("s1", data)
        assert result["confidence_changes"][data["concept"]] == pytest.approx(
            _DELTA_CORRECT_FAST, abs=0.01,
        )

    def test_correct_slow_increases_confidence_by_005(self, make_interaction_data):
        data = make_interaction_data(is_correct=True, time_spent=45.0, help_requests=0)
        result = update_student_cognition_map("s1", data)
        assert result["confidence_changes"][data["concept"]] == pytest.approx(
            _DELTA_CORRECT_SLOW, abs=0.01,
        )

    def test_correct_with_help_increases_confidence_by_005(self, make_interaction_data):
        data = make_interaction_data(is_correct=True, time_spent=10.0, help_requests=2)
        result = update_student_cognition_map("s1", data)
        assert result["confidence_changes"][data["concept"]] == pytest.approx(
            _DELTA_CORRECT_SLOW, abs=0.01,
        )

    def test_incorrect_decreases_confidence_by_015(self, make_interaction_data):
        sid, concept = "s-decr", "newton_second_law"
        # First raise confidence above the floor so the decrease is observable
        update_student_cognition_map(
            sid, make_interaction_data(concept=concept, is_correct=True, time_spent=5.0),
        )
        data = make_interaction_data(concept=concept, is_correct=False)
        result = update_student_cognition_map(sid, data)
        assert result["confidence_changes"][concept] == pytest.approx(
            _DELTA_INCORRECT, abs=0.01,
        )

    def test_confidence_clamped_to_0_1(self, make_interaction_data):
        sid = "s-clamp"
        concept = make_interaction_data()["concept"]

        for _ in range(10):
            update_student_cognition_map(sid, make_interaction_data(is_correct=False))
        model = shared_memory.read("student_cognitive_models", sid)
        assert model["value"]["concepts"][concept]["confidence"] >= 0.0

        for _ in range(20):
            update_student_cognition_map(
                sid,
                make_interaction_data(is_correct=True, time_spent=5.0, help_requests=0),
            )
        model = shared_memory.read("student_cognitive_models", sid)
        assert model["value"]["concepts"][concept]["confidence"] <= 1.0


# ---- New student -----------------------------------------------------------

class TestNewStudent:

    def test_new_student_initializes_blank_model(self, make_interaction_data):
        result = update_student_cognition_map("brand-new-student", make_interaction_data())
        assert "updated_concepts" in result

        model = shared_memory.read("student_cognitive_models", "brand-new-student")
        assert model is not None
        assert model["value"]["student_id"] == "brand-new-student"


# ---- Misconceptions --------------------------------------------------------

class TestMisconceptions:

    def test_misconception_recorded_on_incorrect(self, make_interaction_data):
        data = make_interaction_data(
            is_correct=False,
            student_response="force = mass * velocity",
        )
        result = update_student_cognition_map("s1", data)
        assert len(result["new_misconceptions"]) > 0
        assert result["new_misconceptions"][0]["concept"] == data["concept"]

    def test_no_misconception_on_correct(self, make_interaction_data):
        data = make_interaction_data(is_correct=True, time_spent=10.0)
        result = update_student_cognition_map("s1", data)
        assert len(result["new_misconceptions"]) == 0


# ---- Consecutive errors tracking -------------------------------------------

class TestConsecutiveErrors:

    def test_consecutive_errors_tracked(self, make_interaction_data):
        sid, concept = "s-consec", "force"
        for _ in range(3):
            update_student_cognition_map(
                sid, make_interaction_data(concept=concept, is_correct=False),
            )
        model = shared_memory.read("student_cognitive_models", sid)
        assert model["value"]["concepts"][concept]["consecutive_errors"] == 3

    def test_consecutive_errors_reset_on_correct(self, make_interaction_data):
        sid, concept = "s-reset", "force"
        for _ in range(2):
            update_student_cognition_map(
                sid, make_interaction_data(concept=concept, is_correct=False),
            )
        update_student_cognition_map(
            sid, make_interaction_data(concept=concept, is_correct=True, time_spent=10.0),
        )
        model = shared_memory.read("student_cognitive_models", sid)
        assert model["value"]["concepts"][concept]["consecutive_errors"] == 0


# ---- Persistence -----------------------------------------------------------

class TestPersistence:

    def test_model_persisted_to_shared_memory(self, make_interaction_data):
        data = make_interaction_data()
        update_student_cognition_map("s-persist", data)
        model = shared_memory.read("student_cognitive_models", "s-persist")
        assert model is not None
        assert data["concept"] in model["value"]["concepts"]

    def test_archive_snapshot_written(self, make_interaction_data):
        update_student_cognition_map("s-archive", make_interaction_data())
        snapshots_entries = shared_memory.read_all("cognition_snapshots")
        snapshots = [
            e for e in snapshots_entries
            if e["value"].get("type") == "cognition_snapshot"
            and e["value"].get("student_id") == "s-archive"
        ]
        assert len(snapshots) >= 1

    def test_archive_snapshot_only_for_updated_concept(self, make_interaction_data):
        """Snapshot should only be written for the concept that was updated,
        not for every concept in the model."""
        sid = "s-snap-single"
        update_student_cognition_map(
            sid, make_interaction_data(concept="force", is_correct=True, time_spent=5.0),
        )
        update_student_cognition_map(
            sid, make_interaction_data(concept="momentum", is_correct=False),
        )
        snapshots = shared_memory.read_all("cognition_snapshots")
        student_snaps = [
            e for e in snapshots
            if e["value"].get("student_id") == sid
        ]
        concepts_snapped = [s["value"]["concept_id"] for s in student_snaps]
        assert "force" in concepts_snapped
        assert "momentum" in concepts_snapped
        momentum_snaps = [c for c in concepts_snapped if c == "momentum"]
        assert len(momentum_snaps) == 1, (
            "momentum should have exactly 1 snapshot (not duplicated from "
            "a full-model sweep)"
        )


# ---- Learning preferences --------------------------------------------------

class TestLearningPreferences:

    def test_shaky_concept_flagged_when_correct_but_slow(self, make_interaction_data):
        data = make_interaction_data(
            is_correct=True,
            time_spent=FAST_RESPONSE_THRESHOLD + 15,
            help_requests=0,
        )
        update_student_cognition_map("s-shaky", data)
        model = shared_memory.read("student_cognitive_models", "s-shaky")
        prefs = model["value"].get("learning_style_preferences", {})
        assert data["concept"] in prefs.get("shaky_concepts", [])

    def test_recommended_focus_includes_low_confidence(self, make_interaction_data):
        sid, concept = "s-focus", "hard_topic"
        for _ in range(4):
            update_student_cognition_map(
                sid, make_interaction_data(concept=concept, is_correct=False),
            )
        result = update_student_cognition_map(
            sid, make_interaction_data(concept=concept, is_correct=False),
        )
        assert concept in result["recommended_focus_areas"]


# ---- is_correct=None (neutral observation) ---------------------------------

class TestIsCorrectNone:
    """When correctness is unknown (is_correct=None), the system must treat it
    as a neutral observation: no confidence change, no misconception, and
    consecutive_errors unchanged.

    Guards against regressions where ``if is_correct is None`` is accidentally
    changed back to ``if not is_correct`` or ``if is_correct:``."""

    def test_none_correctness_produces_zero_delta(self, make_interaction_data):
        """_compute_delta(None, ...) must return 0.0."""
        sid, concept = "s-none-delta", "force"
        update_student_cognition_map(
            sid, make_interaction_data(concept=concept, is_correct=True, time_spent=5.0),
        )
        model_before = shared_memory.read("student_cognitive_models", sid)
        conf_before = model_before["value"]["concepts"][concept]["confidence"]

        result = update_student_cognition_map(
            sid, make_interaction_data(concept=concept, is_correct=None),
        )
        assert result["confidence_changes"][concept] == pytest.approx(0.0, abs=1e-6)

        model_after = shared_memory.read("student_cognitive_models", sid)
        assert model_after["value"]["concepts"][concept]["confidence"] == pytest.approx(
            conf_before, abs=1e-6,
        )

    def test_none_correctness_leaves_consecutive_errors_unchanged(
        self, make_interaction_data,
    ):
        """consecutive_errors must NOT increment or reset on is_correct=None."""
        sid, concept = "s-none-err", "force"
        for _ in range(2):
            update_student_cognition_map(
                sid, make_interaction_data(concept=concept, is_correct=False),
            )
        model = shared_memory.read("student_cognitive_models", sid)
        errors_before = model["value"]["concepts"][concept]["consecutive_errors"]
        assert errors_before == 2

        update_student_cognition_map(
            sid, make_interaction_data(concept=concept, is_correct=None),
        )
        model = shared_memory.read("student_cognitive_models", sid)
        assert model["value"]["concepts"][concept]["consecutive_errors"] == errors_before

    def test_none_correctness_skips_misconception_detection(
        self, make_interaction_data,
    ):
        """No misconception should be recorded when correctness is unknown."""
        result = update_student_cognition_map(
            "s-none-misc",
            make_interaction_data(
                is_correct=None,
                student_response="force = mass * velocity",
            ),
        )
        assert len(result["new_misconceptions"]) == 0

    def test_none_correctness_does_not_trigger_false_focus_path(
        self, make_interaction_data, seed_cognitive_model,
    ):
        """The ``if is_correct is False`` path that explicitly adds the
        current concept to recommended_focus must NOT fire when
        is_correct=None.  We pre-seed confidence above the threshold so
        the concept wouldn't appear via the low-confidence scan either."""
        sid, concept = "s-none-focus", "well_known_topic"
        seed_cognitive_model(
            student_id=sid,
            concepts={
                concept: {
                    "confidence": 0.8,
                    "consecutive_errors": 0,
                    "total_attempts": 5,
                    "last_strategy": None,
                    "last_updated": "2024-01-01T00:00:00+00:00",
                },
            },
        )
        result = update_student_cognition_map(
            sid,
            make_interaction_data(concept=concept, is_correct=None),
        )
        assert concept not in result["recommended_focus_areas"]


# ---- Misconception pattern detection ---------------------------------------

class TestMisconceptionPatterns:
    """Tests for _infer_misconception_pattern and _detect_misconception
    which detect specific concept confusions from student responses."""

    def test_detects_force_momentum_confusion(self):
        """Student says 'momentum' when concept is 'force' ->
        pattern must be 'confuses_force_and_momentum'."""
        pattern = _infer_misconception_pattern(
            "force", "I think force is the same as momentum",
        )
        assert pattern == "confuses_force_and_momentum"

    def test_detects_force_velocity_confusion(self):
        """Student uses 'velocity' for force concept ->
        pattern must name the specific sibling."""
        pattern = _infer_misconception_pattern(
            "force", "force equals mass times velocity",
        )
        assert "velocity" in pattern
        assert pattern.startswith("confuses_force_and_")

    def test_falls_back_to_generic_on_no_alias_match(self):
        """When no known concept alias is detected, fallback to
        'incorrect_on_{concept}'."""
        pattern = _infer_misconception_pattern(
            "thermodynamics", "I have no idea",
        )
        assert pattern == "incorrect_on_thermodynamics"

    def test_detect_misconception_returns_none_on_correct(self):
        """_detect_misconception must return None when is_correct=True."""
        assert _detect_misconception("force", "F = m*a", True) is None

    def test_detect_misconception_records_on_incorrect(self):
        """_detect_misconception must return a record when is_correct=False."""
        result = _detect_misconception(
            "force", "force = mass * velocity", False,
        )
        assert result is not None
        assert result["concept"] == "force"
        assert "pattern" in result


# ---- hint_strategy pass-through ---------------------------------------------

class TestHintStrategyPassthrough:

    def test_hint_strategy_stored_in_concept_entry(self, make_interaction_data):
        """When interaction_data contains hint_strategy, the concept entry's
        last_strategy must be set accordingly."""
        sid, concept = "s-strat-pass", "force"
        data = make_interaction_data(concept=concept, is_correct=False)
        data["hint_strategy"] = "analogy"
        update_student_cognition_map(sid, data)
        model = shared_memory.read("student_cognitive_models", sid)
        assert model["value"]["concepts"][concept]["last_strategy"] == "analogy"

    def test_no_hint_strategy_leaves_last_strategy_unchanged(
        self, make_interaction_data, seed_cognitive_model,
    ):
        """When hint_strategy is None or absent, last_strategy must not change."""
        sid, concept = "s-strat-none", "force"
        seed_cognitive_model(
            student_id=sid,
            concepts={
                concept: {
                    "confidence": 0.5,
                    "consecutive_errors": 0,
                    "total_attempts": 1,
                    "last_strategy": "socratic",
                    "last_updated": "2024-01-01T00:00:00+00:00",
                },
            },
        )
        data = make_interaction_data(concept=concept, is_correct=True, time_spent=5.0)
        update_student_cognition_map(sid, data)
        model = shared_memory.read("student_cognitive_models", sid)
        assert model["value"]["concepts"][concept]["last_strategy"] == "socratic"


# ---- Total attempts tracking -----------------------------------------------

class TestTotalAttempts:

    def test_total_attempts_incremented_every_interaction(self, make_interaction_data):
        """total_attempts must increment by 1 on every call, regardless of
        correctness (True, False, or None)."""
        sid, concept = "s-attempts", "force"
        for val in [True, False, None, True]:
            update_student_cognition_map(
                sid,
                make_interaction_data(
                    concept=concept, is_correct=val, time_spent=10.0,
                ),
            )
        model = shared_memory.read("student_cognitive_models", sid)
        assert model["value"]["concepts"][concept]["total_attempts"] == 4
