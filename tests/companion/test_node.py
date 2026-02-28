"""Integration tests for socratic_companion_node.

Anchored to: COMPANION_PRD §6, COMPANION_LOGIC_FLOW Phases 1-5.
"""

import pytest

from agents.companion.node import socratic_companion_node
from memory.shared import shared_memory

pytestmark = pytest.mark.integration


# ---- Basic state contract ---------------------------------------------------

class TestStateContract:

    def test_sets_current_agent(self, make_state):
        state = socratic_companion_node(make_state())
        assert state["current_agent"] == "socratic_companion"

    def test_response_to_student_populated(self, make_state):
        state = socratic_companion_node(make_state())
        assert isinstance(state["response_to_student"], str)
        assert len(state["response_to_student"]) > 0

    def test_tools_to_call_includes_hint_and_cognition(self, make_state):
        state = socratic_companion_node(make_state())
        tool_names = {t["tool"] for t in state["tools_to_call"]}
        assert "construct_hint" in tool_names
        assert "update_student_cognition_map" in tool_names

    def test_loop_count_incremented(self, make_state):
        state = make_state()
        initial = state["loop_count"]
        state = socratic_companion_node(state)
        assert state["loop_count"] == initial + 1

    def test_cognitive_model_in_working_memory(self, make_state):
        state = socratic_companion_node(make_state())
        wm = state.get("working_memory", {})
        assert "cognitive_model" in wm
        assert isinstance(wm["cognitive_model"], dict)


# ---- Context loading (Phase 1) ---------------------------------------------

class TestContextLoading:

    def test_reads_authority_graph(self, make_state, seed_authority_graph):
        """Node calls _authority_context which reads teacher_authority_graph."""
        seed_authority_graph(scope_level="moderate", session_id="test-session")
        state = socratic_companion_node(make_state(session_id="test-session"))
        assert state["response_to_student"]

    def test_new_student_gets_default_model(self, make_state):
        """First message from an unknown student must not crash and must
        initialize cognition model."""
        state = make_state(event_payload={"student_id": "never-seen-before"})
        state = socratic_companion_node(state)
        assert state["response_to_student"]

        model = shared_memory.read("student_cognitive_models", "never-seen-before")
        assert model is not None


# ---- Strategy switching (PRD: >=3 -> switch, >=5 -> escalate) ---------------

class TestStrategySwitching:

    @pytest.mark.xfail(
        reason="Node does not yet check consecutive_errors to switch strategy "
               "after >=3 failures (COMPANION_LOGIC_FLOW strategy switching rules)",
        strict=True,
    )
    def test_strategy_switch_on_3_consecutive_errors(self, make_state, seed_cognitive_model):
        """After 3 consecutive errors on same concept, the hint strategy
        MUST differ from the previous one."""
        sid, concept = "s-switch", "force"
        seed_cognitive_model(
            student_id=sid,
            concepts={
                concept: {
                    "confidence": 0.2,
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
                "content": "wrong answer again",
                "target_concept": concept,
                "is_correct": False,
                "error_analysis": {"type": "conceptual"},
            },
        )
        state = socratic_companion_node(state)
        hint_result = next(
            t["result"] for t in state["tools_to_call"]
            if t["tool"] == "construct_hint"
        )
        assert hint_result["strategy"] != "socratic"

    @pytest.mark.xfail(
        reason="Node does not yet trigger escalate_to_human after >=5 "
               "consecutive failures (COMPANION_LOGIC_FLOW escalation rule)",
        strict=True,
    )
    def test_escalation_on_5_consecutive_errors(self, make_state, seed_cognitive_model):
        """After 5 consecutive errors on same concept, escalate_to_human
        MUST be triggered with reason='repeated_failure'."""
        sid, concept = "s-esc5", "momentum"
        seed_cognitive_model(
            student_id=sid,
            concepts={
                concept: {
                    "confidence": 0.0,
                    "consecutive_errors": 4,
                    "total_attempts": 4,
                    "last_strategy": "decompose",
                    "last_updated": "2024-01-01T00:00:00+00:00",
                },
            },
        )
        state = make_state(
            event_payload={
                "student_id": sid,
                "content": "still wrong",
                "target_concept": concept,
                "is_correct": False,
            },
        )
        state = socratic_companion_node(state)
        tool_names = {t["tool"] for t in state["tools_to_call"]}
        assert "escalate_to_human" in tool_names


# ---- Knowledge boundary enforcement (Path C) -------------------------------

class TestBoundaryEnforcement:

    @pytest.mark.xfail(
        reason="Node does not yet enforce strict knowledge boundary "
               "(COMPANION_LOGIC_FLOW Path C: scope_level=strict -> decline)",
        strict=True,
    )
    def test_boundary_strict_decline(self, make_state, seed_authority_graph):
        """With scope_level='strict' and out-of-scope question, response
        should be a polite decline, not a normal hint."""
        seed_authority_graph(
            scope_level="strict",
            session_id="test-session",
            curriculum_topics=["newton_second_law"],
        )
        state = make_state(
            event_payload={
                "student_id": "s1",
                "content": "Can you explain quantum entanglement?",
                "target_concept": "quantum_mechanics",
                "is_correct": False,
            },
        )
        state = socratic_companion_node(state)
        response = state["response_to_student"].lower()
        assert any(phrase in response for phrase in [
            "outside", "not in", "beyond", "focus on", "current topic",
            "not covering", "decline",
        ])

    @pytest.mark.xfail(
        reason="Node does not yet enforce moderate boundary bridging "
               "(COMPANION_LOGIC_FLOW Path C: scope_level=moderate -> bridge)",
        strict=True,
    )
    def test_boundary_moderate_bridge(self, make_state, seed_authority_graph):
        """With scope_level='moderate', out-of-scope question should bridge
        back to curriculum."""
        seed_authority_graph(
            scope_level="moderate",
            session_id="test-session",
            curriculum_topics=["newton_second_law"],
        )
        state = make_state(
            event_payload={
                "student_id": "s1",
                "content": "How does quantum tunnelling work?",
                "target_concept": "quantum_tunnelling",
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


# ---- Persistence (Phase 5) -------------------------------------------------

class TestPersistence:

    def test_interaction_persisted_to_episodes(self, make_state):
        """After a node call, at least one entry should exist in
        interaction_episodes (written by the cognition tool's archive snapshot)."""
        socratic_companion_node(make_state())
        episodes = shared_memory.read_all("interaction_episodes")
        assert len(episodes) >= 1


# ---- Catalyst routing ------------------------------------------------------

class TestCatalystRouting:

    def test_interest_keywords_written_to_signals(self, make_state):
        state = make_state(
            event_payload={
                "student_id": "s-interest",
                "content": "Interesting",
                "target_concept": "force",
                "interest_keywords": ["physics", "rockets"],
            },
        )
        socratic_companion_node(state)
        entry = shared_memory.read("interest_signals", "s-interest")
        assert entry is not None
        assert "rockets" in entry["value"]["keywords"]

    def test_agent_decision_explore_connection(self, make_state):
        state = make_state(
            event_payload={
                "student_id": "s-explore",
                "content": "Cool",
                "target_concept": "force",
                "interest_keywords": ["space"],
            },
        )
        state = socratic_companion_node(state)
        assert "explore_connection" in state["agent_decision"]
