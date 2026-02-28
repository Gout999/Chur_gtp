"""Behavioral tests encoding the five iron rules from COMPANION_LOGIC_FLOW.md.

These tests serve as guardrails: if any iron rule is violated by future code
changes, the corresponding test must fail.

Iron Rules (L217-224):
  1. Never give direct answers.
  2. Don't ask about interests/hobbies.
  3. Every interaction must update the cognition map.
  4. Strategy must self-adapt (>=3 switch, >=5 escalate).
  5. Respect knowledge boundary.
"""

import pytest

from agents.companion.node import socratic_companion_node
from memory.shared import shared_memory
from prompts.companion import SOCRATIC_COMPANION_PROMPT
from tools.hints import construct_hint

pytestmark = pytest.mark.behavioral


# ---- Rule 1: Never give direct answers -------------------------------------

class TestNeverDirectAnswers:

    def test_hint_never_contains_formula_or_answer(self):
        """Hint content must not contain solution-like patterns."""
        result = construct_hint(
            "s1",
            "What is the formula for force?",
            "newton_second_law",
            error_analysis={"type": "conceptual"},
        )
        content = result["hint_content"].lower()
        assert "the answer is" not in content
        assert "the solution is" not in content
        assert "the formula is" not in content

    def test_hint_always_contains_question_mark(self):
        """A Socratic response must contain at least one question.
        Either hint_content or follow_up_questions should have '?'."""
        result = construct_hint(
            "s1", "I'm stuck", "thermodynamics",
        )
        has_question = (
            "?" in result["hint_content"]
            or any("?" in q for q in result["follow_up_questions"])
        )
        assert has_question, "Socratic response must contain at least one question"


# ---- Rule 2: Don't ask about interests/hobbies ----------------------------

class TestNoInterestQuestions:

    def test_no_interest_hobby_questions(self):
        """follow_up_questions must not ask about hobbies or interests."""
        result = construct_hint("s1", "I don't understand", "velocity")
        for q in result["follow_up_questions"]:
            q_lower = q.lower()
            assert "hobby" not in q_lower
            assert "hobbies" not in q_lower
            assert "what do you want to learn" not in q_lower
            assert "what are your interests" not in q_lower


# ---- Rule 3: Every interaction must update cognition -----------------------

class TestAlwaysUpdateCognition:

    def test_cognition_update_called_every_interaction(self, make_state):
        """The node must call update_student_cognition_map regardless of
        whether the student answered correctly or incorrectly."""
        for correct in (True, False):
            state = make_state(event_payload={"is_correct": correct})
            state = socratic_companion_node(state)
            tool_names = {t["tool"] for t in state["tools_to_call"]}
            assert "update_student_cognition_map" in tool_names, (
                f"cognition not updated when is_correct={correct}"
            )

    def test_cognition_update_even_when_no_answer(self, make_state):
        """Even with an empty student response, cognition must still update."""
        state = make_state(event_payload={"content": "", "student_id": "s-silent"})
        state = socratic_companion_node(state)
        tool_names = {t["tool"] for t in state["tools_to_call"]}
        assert "update_student_cognition_map" in tool_names

    def test_cognition_update_when_correctness_unknown(self, make_state):
        """When is_correct=None (correctness unknown), the cognition tool
        must still be called.  This must produce a neutral 0.0 delta,
        not skip the update entirely."""
        state = make_state(
            event_payload={
                "student_id": "s-ir3-none",
                "content": "Let me think...",
                "is_correct": None,
            },
        )
        state = socratic_companion_node(state)
        tool_names = {t["tool"] for t in state["tools_to_call"]}
        assert "update_student_cognition_map" in tool_names, (
            "cognition not updated when is_correct=None"
        )
        cognition = state["working_memory"]["cognitive_model"]
        concept = state["event_payload"]["target_concept"]
        assert cognition["confidence_changes"][concept] == pytest.approx(0.0, abs=1e-6)


# ---- Rule 4: Strategy self-adaptive ---------------------------------------

class TestStrategyAdaptive:

    def test_strategy_must_switch_after_3_failures(
        self, make_state, seed_cognitive_model,
    ):
        sid, concept = "s-ir4", "force"
        seed_cognitive_model(
            student_id=sid,
            concepts={
                concept: {
                    "confidence": 0.1,
                    "consecutive_errors": 3,
                    "total_attempts": 3,
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
        hint = next(
            t["result"] for t in state["tools_to_call"]
            if t["tool"] == "construct_hint"
        )
        assert hint["strategy"] != "socratic"

    def test_escalate_after_5_failures(self, make_state, seed_cognitive_model):
        sid, concept = "s-ir5", "momentum"
        seed_cognitive_model(
            student_id=sid,
            concepts={
                concept: {
                    "confidence": 0.0,
                    "consecutive_errors": 5,
                    "total_attempts": 5,
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


# ---- Rule 5: Respect knowledge boundary -----------------------------------

class TestBoundaryRespected:

    def test_boundary_respected(self, make_state, seed_authority_graph):
        seed_authority_graph(
            scope_level="strict",
            session_id="test-session",
            curriculum_topics=["newton_second_law"],
        )
        state = make_state(
            event_payload={
                "student_id": "s1",
                "content": "Tell me about black holes",
                "target_concept": "astrophysics",
                "is_correct": False,
            },
        )
        state = socratic_companion_node(state)
        response = state["response_to_student"].lower()
        assert any(w in response for w in [
            "outside", "not covering", "focus on", "current topic",
        ])


# ---- Meta-test: prompt text ------------------------------------------------

class TestPromptContainsIronRules:

    def test_prompt_contains_iron_rules(self):
        """The system prompt must contain key phrases encoding all iron rules."""
        prompt = SOCRATIC_COMPANION_PROMPT.lower()

        assert "never give direct answers" in prompt, "Missing Iron Rule 1"
        assert "never ask about" in prompt, "Missing Iron Rule 2 (interests)"
        assert "update_student_cognition_map" in prompt, "Missing Iron Rule 3"
        assert "escalate_to_human" in prompt, "Missing Iron Rule 4"
        assert "knowledge boundar" in prompt, "Missing Iron Rule 5"
        assert ">= 3" in prompt or ">= 5" in prompt or "3 consecutive" in prompt.replace(
            ">=", ">="
        ), "Missing strategy switching threshold"
