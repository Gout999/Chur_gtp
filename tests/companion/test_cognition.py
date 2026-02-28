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
        episodes = shared_memory.read_all("interaction_episodes")
        snapshots = [
            e for e in episodes
            if e["value"].get("type") == "cognition_snapshot"
            and e["value"].get("student_id") == "s-archive"
        ]
        assert len(snapshots) >= 1


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
