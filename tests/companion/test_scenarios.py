"""Multi-turn scenario tests simulating realistic teaching conversations.

Each scenario mirrors real usage described in COMPANION_LOGIC_FLOW.md §完整示例
(L196-213) and the PRD verification criteria.  These tests exercise the full
companion stack: node -> tools -> shared memory across multiple turns.

Anchored to: COMPANION_LOGIC_FLOW complete example, COMPANION_PRD §8 MVP criteria.
"""

import pytest

from agents.companion.node import socratic_companion_node
from memory.shared import shared_memory
from tools.cognition import (
    _DELTA_CORRECT_FAST,
    _DELTA_CORRECT_SLOW,
    _DELTA_INCORRECT,
)

pytestmark = pytest.mark.scenario


def _node_turn(state, *, content=None, is_correct=None, time_spent=None,
               help_requests=None, target_concept=None, error_analysis=None):
    """Helper: update event_payload fields and run one node turn."""
    p = state["event_payload"]
    if content is not None:
        p["content"] = content
    if is_correct is not None:
        p["is_correct"] = is_correct
    if time_spent is not None:
        p["time_spent"] = time_spent
    if help_requests is not None:
        p["help_requests"] = help_requests
    if target_concept is not None:
        p["target_concept"] = target_concept
    if error_analysis is not None:
        p["error_analysis"] = error_analysis
    return socratic_companion_node(state)


# ---------------------------------------------------------------------------
# Scenario 1: Happy path — student answers correctly and quickly
# ---------------------------------------------------------------------------

class TestHappyPath:

    def test_correct_fast_answer(self, make_state):
        """Student answers Newton's 2nd law correctly in <30s.
        Expected: confidence +0.20, no misconception, Socratic hint."""
        state = make_state(
            event_payload={
                "student_id": "s-happy",
                "content": "F equals m times a",
                "target_concept": "newton_second_law",
                "is_correct": True,
                "time_spent": 12.0,
                "help_requests": 0,
            },
        )
        state = socratic_companion_node(state)

        assert state["response_to_student"]

        cognition = state["working_memory"]["cognitive_model"]
        concept = "newton_second_law"
        assert cognition["confidence_changes"][concept] == pytest.approx(
            _DELTA_CORRECT_FAST, abs=0.01,
        )
        assert len(cognition["new_misconceptions"]) == 0


# ---------------------------------------------------------------------------
# Scenario 2: Slow learner — correct but slow, with help requests
# ---------------------------------------------------------------------------

class TestSlowLearner:

    def test_correct_slow_with_help(self, make_state):
        """Student answers correctly but takes >30s with 1 help request.
        Expected: confidence +0.05, flagged as 'shaky'."""
        state = make_state(
            event_payload={
                "student_id": "s-slow",
                "content": "F = m * a, right?",
                "target_concept": "newton_second_law",
                "is_correct": True,
                "time_spent": 55.0,
                "help_requests": 1,
            },
        )
        state = socratic_companion_node(state)

        cognition = state["working_memory"]["cognitive_model"]
        concept = "newton_second_law"
        assert cognition["confidence_changes"][concept] == pytest.approx(
            _DELTA_CORRECT_SLOW, abs=0.01,
        )

        model = shared_memory.read("student_cognitive_models", "s-slow")
        prefs = model["value"].get("learning_style_preferences", {})
        assert concept in prefs.get("shaky_concepts", [])


# ---------------------------------------------------------------------------
# Scenario 3: 3-error strategy switch
# ---------------------------------------------------------------------------

class TestThreeErrorSwitch:

    @pytest.mark.xfail(
        reason="Strategy auto-switching after >=3 consecutive errors "
               "not yet implemented in construct_hint / node",
        strict=True,
    )
    def test_strategy_changes_after_3_errors(self, make_state):
        """Student gets same concept wrong 3 times with socratic strategy.
        On 4th attempt, strategy must switch."""
        sid, concept = "s-3err", "force"
        state = make_state(
            event_payload={
                "student_id": sid,
                "content": "force = mass * velocity",
                "target_concept": concept,
                "is_correct": False,
                "time_spent": 20.0,
                "error_analysis": {"type": "conceptual"},
            },
        )

        strategies_seen = []
        for i in range(4):
            state = _node_turn(
                state,
                content=f"wrong attempt {i + 1}",
                is_correct=False,
            )
            hint = next(
                t["result"] for t in state["tools_to_call"]
                if t["tool"] == "construct_hint"
            )
            strategies_seen.append(hint["strategy"])

        assert strategies_seen[-1] != strategies_seen[0], (
            f"Strategy should have switched but stayed {strategies_seen}"
        )


# ---------------------------------------------------------------------------
# Scenario 4: 5-error escalation (COMPANION_LOGIC_FLOW L207-213)
# ---------------------------------------------------------------------------

class TestFiveErrorEscalation:

    @pytest.mark.xfail(
        reason="Node does not yet trigger escalate_to_human after "
               ">=5 consecutive failures",
        strict=True,
    )
    def test_escalation_after_5_errors(self, make_state):
        """Student gets 'force vs momentum' wrong 5 times consecutively.
        5th interaction must trigger escalate_to_human(reason='repeated_failure',
        urgency='high') and return a comfort message."""
        sid = "s-5err"
        state = make_state(
            event_payload={
                "student_id": sid,
                "content": "force = mass * velocity",
                "target_concept": "force",
                "is_correct": False,
                "time_spent": 25.0,
            },
        )
        for i in range(5):
            state = _node_turn(state, content=f"still wrong #{i + 1}", is_correct=False)

        tool_names = {t["tool"] for t in state["tools_to_call"]}
        assert "escalate_to_human" in tool_names

        esc = next(
            t["result"] for t in state["tools_to_call"]
            if t["tool"] == "escalate_to_human"
        )
        assert esc.get("student_message")


# ---------------------------------------------------------------------------
# Scenario 5: New student cold start
# ---------------------------------------------------------------------------

class TestColdStart:

    def test_new_student_first_message(self, make_state):
        """Unknown student_id sends first message. Must not crash and
        must initialize cognition model."""
        state = make_state(
            event_payload={
                "student_id": "first-timer",
                "content": "What is force?",
                "target_concept": "force",
                "is_correct": False,
            },
        )
        state = socratic_companion_node(state)

        assert state["response_to_student"]
        model = shared_memory.read("student_cognitive_models", "first-timer")
        assert model is not None
        assert model["value"]["student_id"] == "first-timer"


# ---------------------------------------------------------------------------
# Scenario 6: Out-of-scope strict boundary
# ---------------------------------------------------------------------------

class TestStrictBoundary:

    @pytest.mark.xfail(
        reason="Node does not yet enforce strict scope boundary "
               "(should decline out-of-scope questions)",
        strict=True,
    )
    def test_strict_scope_decline(self, make_state, seed_authority_graph):
        """Authority graph has strict scope for Newtonian mechanics.
        Student asks about quantum mechanics. Response must politely decline."""
        seed_authority_graph(
            scope_level="strict",
            session_id="test-session",
            curriculum_topics=["newton_second_law", "force"],
        )
        state = make_state(
            event_payload={
                "student_id": "s1",
                "content": "Explain quantum entanglement please",
                "target_concept": "quantum_mechanics",
                "is_correct": False,
            },
        )
        state = socratic_companion_node(state)

        response = state["response_to_student"].lower()
        assert any(w in response for w in [
            "outside", "not covering", "focus on", "current topic",
        ])


# ---------------------------------------------------------------------------
# Scenario 7: Out-of-scope moderate boundary
# ---------------------------------------------------------------------------

class TestModerateBoundary:

    @pytest.mark.xfail(
        reason="Node does not yet implement moderate scope bridging "
               "(should bridge back to curriculum)",
        strict=True,
    )
    def test_moderate_scope_bridge(self, make_state, seed_authority_graph):
        """Moderate scope: acknowledge the connection, bridge back."""
        seed_authority_graph(
            scope_level="moderate",
            session_id="test-session",
            curriculum_topics=["newton_second_law", "force"],
        )
        state = make_state(
            event_payload={
                "student_id": "s1",
                "content": "How is E=mc² derived?",
                "target_concept": "relativity",
                "is_correct": False,
            },
        )
        state = socratic_companion_node(state)

        response = state["response_to_student"].lower()
        assert any(phrase in response for phrase in [
            "interesting connection",
            "cover later",
            "for now, let",
            "bridge",
            "we'll get to",
        ])


# ---------------------------------------------------------------------------
# Scenario 8: Confidence recovery after errors
# ---------------------------------------------------------------------------

class TestConfidenceRecovery:

    def test_confidence_recovers_after_correct_answers(
        self, make_state, seed_cognitive_model,
    ):
        """Student gets wrong 3 times (confidence drops), then gets right
        2 times quickly (confidence recovers, consecutive_errors resets)."""
        sid, concept = "s-recover", "force"
        seed_cognitive_model(
            student_id=sid,
            concepts={
                concept: {
                    "confidence": 0.6,
                    "consecutive_errors": 0,
                    "total_attempts": 3,
                    "last_strategy": None,
                    "last_updated": "2024-01-01T00:00:00+00:00",
                },
            },
        )
        state = make_state(
            event_payload={
                "student_id": sid,
                "content": "wrong",
                "target_concept": concept,
                "is_correct": False,
                "time_spent": 20.0,
            },
        )

        for _ in range(3):
            state = _node_turn(state, content="wrong again", is_correct=False)

        model = shared_memory.read("student_cognitive_models", sid)
        conf_after_errors = model["value"]["concepts"][concept]["confidence"]
        assert conf_after_errors < 0.6

        for _ in range(2):
            state = _node_turn(
                state, content="F = m * a", is_correct=True, time_spent=8.0,
            )

        model = shared_memory.read("student_cognitive_models", sid)
        conf_after_recovery = model["value"]["concepts"][concept]["confidence"]
        assert conf_after_recovery > conf_after_errors

        errors = model["value"]["concepts"][concept]["consecutive_errors"]
        assert errors == 0


# ---------------------------------------------------------------------------
# Scenario 9: Cross-concept independence
# ---------------------------------------------------------------------------

class TestCrossConceptIndependence:

    def test_concepts_do_not_interfere(self, make_state):
        """Getting concept A wrong and concept B right must only affect
        their respective confidence values independently."""
        sid = "s-cross"
        state = make_state(
            event_payload={
                "student_id": sid,
                "content": "force = mass * velocity",
                "target_concept": "force",
                "is_correct": False,
                "time_spent": 20.0,
            },
        )
        state = socratic_companion_node(state)

        state = _node_turn(
            state,
            content="p = m * v",
            target_concept="momentum",
            is_correct=True,
            time_spent=10.0,
        )

        model = shared_memory.read("student_cognitive_models", sid)
        concepts = model["value"]["concepts"]

        assert concepts["momentum"]["confidence"] > concepts["force"]["confidence"]
        assert concepts["force"]["consecutive_errors"] >= 1
        assert concepts["momentum"]["consecutive_errors"] == 0


# ---------------------------------------------------------------------------
# Scenario 10: Full Logic Flow walkthrough (L197-205)
# ---------------------------------------------------------------------------

class TestFullLogicFlowWalkthrough:
    """Replicates the exact example from COMPANION_LOGIC_FLOW.md:
    Student says 'force = mass * velocity' for the 3rd time.
    Expected: strategy switches from socratic (used 2x) to confront;
    misconception 'confuses_force_and_momentum' is recorded."""

    @pytest.mark.xfail(
        reason="Full Logic Flow walkthrough requires strategy auto-switching "
               "and confront strategy, both not yet implemented",
        strict=True,
    )
    def test_third_error_switches_to_confront(self, make_state, seed_cognitive_model):
        sid, concept = "s-walkthrough", "force_vs_momentum"
        seed_cognitive_model(
            student_id=sid,
            concepts={
                concept: {
                    "confidence": 0.1,
                    "consecutive_errors": 2,
                    "total_attempts": 2,
                    "last_strategy": "socratic",
                    "last_updated": "2024-01-01T00:00:00+00:00",
                },
            },
        )
        state = make_state(
            event_payload={
                "student_id": sid,
                "content": "force = mass * velocity",
                "target_concept": concept,
                "is_correct": False,
                "time_spent": 45.0,
                "error_analysis": {"type": "conceptual"},
            },
        )
        state = socratic_companion_node(state)

        hint = next(
            t["result"] for t in state["tools_to_call"]
            if t["tool"] == "construct_hint"
        )
        assert hint["strategy"] == "confront", (
            f"Expected 'confront' after 2 failed socratic attempts, "
            f"got '{hint['strategy']}'"
        )

        model = shared_memory.read("student_cognitive_models", sid)
        misconceptions = model["value"].get("misconceptions", [])
        assert any(
            concept in str(m) for m in misconceptions
        ), "Misconception for force/momentum confusion not recorded"
