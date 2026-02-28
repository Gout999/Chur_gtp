"""Integration tests for socratic_companion_node.

Anchored to: COMPANION_PRD §6, COMPANION_LOGIC_FLOW Phases 1-5.
"""

import pytest
from unittest.mock import patch

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

    def test_new_student_bootstraps_target_concept_uncertainty(self, make_state):
        """First turn should initialize target concept with uncertainty=1.0
        when correctness is unknown."""
        student_id = "never-seen-before-uncertainty"
        state = make_state(event_payload={
            "student_id": student_id,
            "target_concept": "force",
            "is_correct": None,
        })
        state = socratic_companion_node(state)
        assert state["response_to_student"]

        model = shared_memory.read("student_cognitive_models", student_id)
        concept = model["value"]["concepts"]["force"]
        assert concept["uncertainty"] == pytest.approx(1.0, abs=0.01)


# ---- Strategy switching (PRD: >=3 -> switch, >=5 -> escalate) ---------------

class TestStrategySwitching:

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


# ---- Knowledge boundary helpers (Task 7 unit tests) -------------------------

class TestBoundaryHelpers:
    """Unit tests for the boundary helper functions added/enhanced in Task 7."""

    def test_tokenize_concept_underscores(self):
        from agents.companion.node import _tokenize_concept
        tokens = _tokenize_concept("newton_second_law")
        assert tokens == {"newton", "second", "law"}

    def test_tokenize_concept_camelCase(self):
        from agents.companion.node import _tokenize_concept
        tokens = _tokenize_concept("newtonSecondLaw")
        assert "newton" in tokens
        assert "second" in tokens

    def test_tokenize_concept_possessive(self):
        from agents.companion.node import _tokenize_concept
        tokens = _tokenize_concept("Newton's Second Law")
        assert "newton" in tokens
        assert "second" in tokens

    def test_concept_matches_topic_substring(self):
        from agents.companion.node import _concept_matches_topic
        assert _concept_matches_topic("force", "forces_and_motion")

    def test_concept_matches_topic_token_overlap(self):
        from agents.companion.node import _concept_matches_topic
        assert _concept_matches_topic("second_law", "newton_second_law")

    def test_concept_no_match(self):
        from agents.companion.node import _concept_matches_topic
        assert not _concept_matches_topic("quantum_mechanics", "newton_second_law")

    def test_collect_curriculum_concepts_merges_topics_and_nodes(self):
        from agents.companion.node import _collect_curriculum_concepts
        boundary = {
            "curriculum_topics": ["force", "momentum"],
            "knowledge_nodes": [
                {"concept": "force"},
                {"concept": "acceleration"},
            ],
        }
        result = _collect_curriculum_concepts(boundary)
        assert "force" in result
        assert "momentum" in result
        assert "acceleration" in result
        assert result.count("force") == 1

    def test_is_out_of_scope_with_knowledge_nodes(self):
        from agents.companion.node import _is_out_of_scope
        boundary = {
            "curriculum_topics": ["newton_second_law"],
            "knowledge_nodes": [{"concept": "force"}, {"concept": "mass"}],
        }
        assert not _is_out_of_scope("force", boundary)
        assert _is_out_of_scope("quantum_mechanics", boundary)

    def test_is_out_of_scope_empty_concept_returns_false(self):
        from agents.companion.node import _is_out_of_scope
        boundary = {"curriculum_topics": ["force"]}
        assert not _is_out_of_scope("", boundary)

    def test_is_out_of_scope_empty_topics_returns_false(self):
        from agents.companion.node import _is_out_of_scope
        boundary = {"curriculum_topics": []}
        assert not _is_out_of_scope("quantum", boundary)

    def test_find_closest_topic_selects_best_match(self):
        from agents.companion.node import _find_closest_topic
        boundary = {
            "curriculum_topics": ["newton_second_law", "conservation_of_energy"],
        }
        result = _find_closest_topic("energy_conservation", boundary)
        assert "energy" in result.lower()

    def test_find_closest_topic_falls_back_to_first(self):
        from agents.companion.node import _find_closest_topic
        boundary = {"curriculum_topics": ["force", "momentum"]}
        result = _find_closest_topic("unrelated_topic", boundary)
        assert result == "force"

    def test_detect_out_of_scope_topic_finds_quantum(self):
        from agents.companion.node import _detect_out_of_scope_topic
        boundary = {"curriculum_topics": ["newton_second_law", "force"]}
        result = _detect_out_of_scope_topic(
            "Can you explain quantum mechanics?", boundary,
        )
        assert result == "quantum"

    def test_detect_out_of_scope_topic_returns_none_for_in_scope(self):
        from agents.companion.node import _detect_out_of_scope_topic
        boundary = {"curriculum_topics": ["newton_second_law", "force"]}
        result = _detect_out_of_scope_topic(
            "What is force?", boundary,
        )
        assert result is None

    def test_detect_out_of_scope_topic_chinese_keywords(self):
        from agents.companion.node import _detect_out_of_scope_topic
        boundary = {"curriculum_topics": ["newton_second_law", "force"]}
        result = _detect_out_of_scope_topic(
            "请讲一下量子力学", boundary,
        )
        assert result == "quantum"


class TestBoundaryResponse:
    """Unit tests for _boundary_response with all three scope levels."""

    def test_strict_contains_decline_language(self):
        from agents.companion.node import _boundary_response
        boundary = {"curriculum_topics": ["force"]}
        text = _boundary_response("strict", boundary, "quantum")
        assert "outside" in text.lower() or "focus" in text.lower()

    def test_moderate_contains_bridge_language(self):
        from agents.companion.node import _boundary_response
        boundary = {"curriculum_topics": ["force"]}
        text = _boundary_response("moderate", boundary, "quantum")
        assert "interesting" in text.lower() or "connection" in text.lower()

    def test_permissive_contains_tieback_language(self):
        from agents.companion.node import _boundary_response
        boundary = {"curriculum_topics": ["force"]}
        text = _boundary_response("permissive", boundary, "quantum")
        assert "curiosity" in text.lower() or "explore" in text.lower()

    def test_response_references_closest_topic(self):
        from agents.companion.node import _boundary_response
        boundary = {"curriculum_topics": ["conservation_of_energy", "force"]}
        text = _boundary_response("strict", boundary, "energy_storage")
        assert "energy" in text.lower()


# ---- Boundary integration (full node flow, Task 7) --------------------------

class TestBoundaryIntegration:
    """Integration tests for knowledge boundary compliance through the full node."""

    def test_permissive_scope_allows_exploration_with_tieback(
        self, make_state, seed_authority_graph,
    ):
        """With scope_level='permissive' and out-of-scope concept, the node
        should still respond but include a curriculum tie-back message."""
        seed_authority_graph(
            scope_level="permissive",
            session_id="test-session",
            curriculum_topics=["newton_second_law"],
        )
        state = make_state(
            event_payload={
                "student_id": "s1",
                "content": "Tell me about thermodynamics",
                "target_concept": "thermodynamics",
                "is_correct": False,
            },
        )
        state = socratic_companion_node(state)
        response = state["response_to_student"].lower()
        assert any(phrase in response for phrase in [
            "curiosity", "explore", "focus", "main",
        ])

    def test_no_target_concept_detects_out_of_scope_from_input(
        self, make_state, seed_authority_graph,
    ):
        """When target_concept is empty, the node should detect out-of-scope
        topics from the student's message text."""
        seed_authority_graph(
            scope_level="strict",
            session_id="test-session",
            curriculum_topics=["newton_second_law", "force"],
        )
        state = make_state(
            event_payload={
                "student_id": "s1",
                "content": "Can you teach me about quantum physics?",
                "target_concept": "",
                "is_correct": None,
            },
        )
        state = socratic_companion_node(state)
        response = state["response_to_student"].lower()
        assert any(phrase in response for phrase in [
            "outside", "focus on", "current topic",
        ])

    def test_in_scope_concept_gets_normal_hint(
        self, make_state, seed_authority_graph,
    ):
        """An in-scope concept should receive a normal hint, not a boundary response."""
        seed_authority_graph(
            scope_level="strict",
            session_id="test-session",
            curriculum_topics=["newton_second_law", "force", "momentum"],
        )
        state = make_state(
            event_payload={
                "student_id": "s1",
                "content": "What is force?",
                "target_concept": "force",
                "is_correct": False,
            },
        )
        state = socratic_companion_node(state)
        tool_names = {t["tool"] for t in state["tools_to_call"]}
        assert "construct_hint" in tool_names

    def test_knowledge_nodes_extend_scope(
        self, make_state, seed_authority_graph,
    ):
        """Concepts listed in knowledge_nodes (not just curriculum_topics)
        should be considered in-scope."""
        shared_memory.write("teacher_authority_graph", "test-session", {
            "scope_level": "strict",
            "curriculum_topics": ["newton_second_law"],
            "knowledge_nodes": [
                {"concept": "newton_second_law", "difficulty": 0.5},
                {"concept": "acceleration", "difficulty": 0.4},
            ],
        })
        state = make_state(
            event_payload={
                "student_id": "s1",
                "content": "What is acceleration?",
                "target_concept": "acceleration",
                "is_correct": False,
            },
        )
        state = socratic_companion_node(state)
        tool_names = {t["tool"] for t in state["tools_to_call"]}
        assert "construct_hint" in tool_names

    def test_boundary_response_persisted_in_interaction(
        self, make_state, seed_authority_graph,
    ):
        """Even boundary responses should be persisted in interaction_episodes."""
        seed_authority_graph(
            scope_level="strict",
            session_id="test-session",
            curriculum_topics=["newton_second_law"],
        )
        state = make_state(
            event_payload={
                "student_id": "s-boundary-persist",
                "content": "Tell me about chemistry",
                "target_concept": "chemistry",
                "is_correct": False,
            },
        )
        socratic_companion_node(state)
        episodes = shared_memory.read_all(
            "interaction_episodes",
            filter_dict={"student_id": "s-boundary-persist"},
        )
        assert len(episodes) >= 1

    def test_boundary_loaded_in_working_memory(self, make_state, seed_authority_graph):
        """After the node runs, the loaded boundary should be stored in
        working_memory for inspection."""
        seed_authority_graph(
            scope_level="moderate",
            session_id="test-session",
        )
        state = socratic_companion_node(make_state())
        boundary = state["working_memory"].get("knowledge_boundary", {})
        assert boundary.get("scope_level") == "moderate"

    def test_no_boundary_defaults_to_moderate(self, make_state):
        """When no authority graph exists, scope_level defaults to moderate
        and the node handles it gracefully."""
        state = make_state(
            event_payload={
                "student_id": "s-no-boundary",
                "content": "What is quantum mechanics?",
                "target_concept": "quantum_mechanics",
                "is_correct": False,
            },
        )
        state = socratic_companion_node(state)
        assert state["response_to_student"]
        boundary = state["working_memory"].get("knowledge_boundary", {})
        assert boundary.get("scope_level") == "moderate"

    def test_session_fallback_to_global_boundary(self, make_state):
        """When no session-specific boundary exists, fall back to global."""
        shared_memory.write("teacher_authority_graph", "global", {
            "scope_level": "strict",
            "curriculum_topics": ["force"],
        })
        state = make_state(
            session_id="nonexistent-session",
            event_payload={
                "student_id": "s1",
                "content": "Tell me about chemistry",
                "target_concept": "chemistry",
                "is_correct": False,
            },
        )
        state = socratic_companion_node(state)
        response = state["response_to_student"].lower()
        assert "outside" in response or "focus" in response


# ---- Persistence (Phase 5) -------------------------------------------------

class TestPersistence:

    def test_interaction_persisted_to_episodes(self, make_state):
        """After a node call, at least one entry should exist in
        interaction_episodes (written by the cognition tool's archive snapshot)."""
        socratic_companion_node(make_state())
        episodes = shared_memory.read_all("interaction_episodes")
        assert len(episodes) >= 1


# ---- is_correct=None passthrough (neutral observation) ---------------------

class TestIsCorrectNonePassthrough:
    """When payload omits is_correct (or sets it to None), the node must
    pass None through to update_student_cognition_map, producing a neutral
    delta -- no confidence change, no misconception, errors unchanged."""

    def test_none_correctness_no_crash_no_misconception(self, make_state):
        """Node must handle is_correct=None without error, and the
        cognition tool must report zero delta."""
        state = make_state(
            event_payload={
                "student_id": "s-none-node",
                "content": "hmm, I need to think about this",
                "target_concept": "force",
                "is_correct": None,
                "time_spent": 10.0,
            },
        )
        state = socratic_companion_node(state)
        assert state["response_to_student"]

        cognition = state["working_memory"]["cognitive_model"]
        assert cognition["confidence_changes"]["force"] == pytest.approx(0.0, abs=1e-6)
        assert len(cognition["new_misconceptions"]) == 0

    def test_missing_is_correct_key_treated_as_none(self, make_state):
        """When is_correct is entirely absent from payload, the node
        should default to None (not False), producing a neutral observation."""
        state = make_state()
        del state["event_payload"]["is_correct"]
        state = socratic_companion_node(state)

        cognition = state["working_memory"]["cognitive_model"]
        assert cognition["confidence_changes"]["newton_second_law"] == pytest.approx(
            0.0, abs=1e-6,
        )


# ---- Agent decision defaults to empty (no cross-agent routing) ---------------

class TestAgentDecisionDefault:

    def test_agent_decision_is_empty_by_default(self, make_state):
        state = socratic_companion_node(make_state())
        assert state["agent_decision"] == ""

    def test_no_interest_signals_written(self, make_state):
        """Companion must NOT write to interest_signals (Catalyst's domain)."""
        state = make_state(
            event_payload={
                "student_id": "s-no-interest",
                "content": "Interesting",
                "target_concept": "force",
                "interest_keywords": ["physics", "rockets"],
            },
        )
        socratic_companion_node(state)
        entry = shared_memory.read("interest_signals", "s-no-interest")
        assert entry is None


# ---- Guardrail enforcement (post-LLM Iron Rule checks) ----------------------

class TestGuardrailEnforcement:

    def test_guardrail_escalation_on_5_errors_even_if_llm_chose_hint(
        self, make_state, seed_cognitive_model,
    ):
        """Even in deterministic path, if consecutive errors >= 5 and the
        decision would be 'hint', guardrails must override to 'escalate'."""
        sid, concept = "s-guard-esc", "momentum"
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

    def test_guardrail_boundary_strict_overrides_hint(
        self, make_state, seed_authority_graph,
    ):
        """With strict scope and out-of-scope concept, guardrails must
        produce a boundary decline response, not a hint."""
        seed_authority_graph(
            scope_level="strict",
            session_id="test-session",
            curriculum_topics=["newton_second_law"],
        )
        state = make_state(
            event_payload={
                "student_id": "s1",
                "content": "Tell me about thermodynamics",
                "target_concept": "thermodynamics",
                "is_correct": False,
            },
        )
        state = socratic_companion_node(state)
        response = state["response_to_student"].lower()
        assert "outside" in response or "focus on" in response


# ---- Direct-response + emotion guardrails -----------------------------------

class TestDirectResponseAndEmotionGuardrails:

    def test_frustration_signal_forces_escalation_even_without_5_errors(
        self, make_state,
    ):
        """Iron Rule 4: explicit frustration language must trigger escalation,
        even when repeated-failure threshold is not reached."""
        state = make_state(
            event_payload={
                "student_id": "s-frustrated",
                "content": "I give up. This is stupid and I can't do this.",
                "target_concept": "force",
                "is_correct": False,
            },
        )
        with patch(
            "agents.companion.node._llm_reason",
            return_value={
                "action": "hint",
                "reasoning": "mocked llm",
                "tool_params": {
                    "student_id": "s-frustrated",
                    "current_input": "I give up",
                    "target_concept": "force",
                    "error_analysis": {"type": "conceptual"},
                },
                "response_text": "",
            },
        ):
            state = socratic_companion_node(state)

        tool_names = {t["tool"] for t in state["tools_to_call"]}
        assert "escalate_to_human" in tool_names

    def test_direct_response_with_answer_pattern_is_sanitized_to_hint(
        self, make_state,
    ):
        """Iron Rule 1: if LLM text includes direct-answer patterns, node
        must not send it directly to student."""
        state = make_state(
            event_payload={
                "student_id": "s-direct-answer",
                "content": "What is Newton's second law?",
                "target_concept": "newton_second_law",
                "is_correct": False,
            },
        )
        bad_text = "The answer is F = m * a."
        with patch(
            "agents.companion.node._llm_reason",
            return_value={
                "action": "direct_response",
                "reasoning": "mocked direct response",
                "tool_params": {},
                "response_text": bad_text,
            },
        ):
            state = socratic_companion_node(state)

        response = state["response_to_student"].lower()
        tool_names = {t["tool"] for t in state["tools_to_call"]}
        assert "construct_hint" in tool_names
        assert "the answer is" not in response

    def test_direct_response_with_interest_probe_is_sanitized_to_hint(
        self, make_state,
    ):
        """Iron Rule 2: node must block interest/hobby probing in direct text."""
        state = make_state(
            event_payload={
                "student_id": "s-interest-probe",
                "content": "Can we continue with force?",
                "target_concept": "force",
                "is_correct": False,
            },
        )
        bad_text = "What are your interests and hobbies before we continue?"
        with patch(
            "agents.companion.node._llm_reason",
            return_value={
                "action": "direct_response",
                "reasoning": "mocked direct response",
                "tool_params": {},
                "response_text": bad_text,
            },
        ):
            state = socratic_companion_node(state)

        response = state["response_to_student"].lower()
        tool_names = {t["tool"] for t in state["tools_to_call"]}
        assert "construct_hint" in tool_names
        assert "what are your interests" not in response
        assert "hobbies" not in response


# ---- Multi-turn strategy adjustment (Task 6) --------------------------------

class TestMultiTurnStrategy:
    """Session-level error tracking, effective-error injection,
    strategy exhaustion detection, and tracker reset on correct answer.

    All tests use the deterministic fallback path (no LLM).
    """

    def test_session_tracker_initialized_on_first_call(self, make_state):
        """After the first node call, working_memory must contain a
        session_error_tracker dict with an entry for the target concept."""
        state = socratic_companion_node(make_state())
        tracker = state["working_memory"].get("session_error_tracker", {})
        assert isinstance(tracker, dict)
        assert "newton_second_law" in tracker

    def test_session_tracker_accumulates_errors(self, make_state):
        """Calling the node 3 times with is_correct=False on the same
        concept must yield session consecutive_errors == 3."""
        sid, concept = "s-accum", "force"
        state = make_state(
            event_payload={
                "student_id": sid,
                "content": "wrong",
                "target_concept": concept,
                "is_correct": False,
            },
        )
        for _ in range(3):
            state = socratic_companion_node(state)
            state["event_payload"] = {
                "student_id": sid,
                "content": "still wrong",
                "target_concept": concept,
                "is_correct": False,
            }

        tracker = state["working_memory"]["session_error_tracker"]
        assert tracker[concept]["consecutive_errors"] == 3

    def test_effective_errors_injected_in_hint_params(
        self, make_state, seed_cognitive_model,
    ):
        """construct_hint must receive effective_consecutive_errors that
        accounts for both stored and current-turn errors."""
        sid, concept = "s-eff", "force"
        seed_cognitive_model(
            student_id=sid,
            concepts={
                concept: {
                    "confidence": 0.3,
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
                "content": "wrong again",
                "target_concept": concept,
                "is_correct": False,
                "error_analysis": {"type": "conceptual"},
            },
        )
        state = socratic_companion_node(state)
        hint_call = next(
            t for t in state["tools_to_call"] if t["tool"] == "construct_hint"
        )
        assert hint_call["result"]["strategy"] != "socratic"

    def test_strategy_exhaustion_triggers_escalation(
        self, make_state, seed_cognitive_model,
    ):
        """When all 4 strategies have been tried in a session and the
        student still answers incorrectly, escalate_to_human must fire."""
        sid, concept = "s-exhaust", "force"
        seed_cognitive_model(
            student_id=sid,
            concepts={
                concept: {
                    "confidence": 0.1,
                    "consecutive_errors": 3,
                    "total_attempts": 3,
                    "last_strategy": "analogy",
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
            },
        )
        state["working_memory"] = {
            "session_error_tracker": {
                concept: {
                    "consecutive_errors": 3,
                    "strategies_tried": ["socratic", "decompose", "analogy"],
                    "last_strategy": "analogy",
                },
            },
        }
        state = socratic_companion_node(state)

        tool_names = [t["tool"] for t in state["tools_to_call"]]
        assert "escalate_to_human" in tool_names

    def test_session_tracker_resets_on_correct_answer(self, make_state):
        """After a correct answer, the session tracker for that concept
        must reset consecutive_errors to 0 and clear strategies_tried."""
        sid, concept = "s-reset", "force"
        state = make_state(
            event_payload={
                "student_id": sid,
                "content": "wrong",
                "target_concept": concept,
                "is_correct": False,
            },
        )
        state = socratic_companion_node(state)
        tracker = state["working_memory"]["session_error_tracker"]
        assert tracker[concept]["consecutive_errors"] == 1

        state["event_payload"] = {
            "student_id": sid,
            "content": "F = ma",
            "target_concept": concept,
            "is_correct": True,
        }
        state = socratic_companion_node(state)
        tracker = state["working_memory"]["session_error_tracker"]
        assert tracker[concept]["consecutive_errors"] == 0
        assert tracker[concept]["strategies_tried"] == []
