"""Task 9: Multi-turn dialogue test script (COMPANION_WORKLIST item 9).

Companion-only: uses agents.companion.node and memory.shared (read); does not
modify graph.py, memory/*, or other agents (Architect/Catalyst).

Single runnable script that verifies all five Phase 3 acceptance scenarios:
  1. Single-concept correct answer -> hint disappears (cognition reset)
  2. Same concept multiple errors -> strategy switch
  3. >=5 errors -> escalation triggered
  4. Out-of-scope question -> boundary intercept
  5. Cognitive model correctly updated after multi-turn

Run (from repo root): pytest Chur_gtp/tests/companion/test_task9_multiturn_script.py -v
Run (from Chur_gtp):  pytest tests/companion/test_task9_multiturn_script.py -v
"""

import pytest

from agents.companion.node import socratic_companion_node
from memory.shared import shared_memory

pytestmark = [pytest.mark.scenario, pytest.mark.integration]


def _node_turn(state, *, content=None, is_correct=None, time_spent=None,
               help_requests=None, target_concept=None, error_analysis=None):
    """Update event_payload fields and run one companion node turn."""
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
# 1. Single-concept correct answer -> confirm hint disappears (cognition reset)
# ---------------------------------------------------------------------------

def test_01_correct_answer_then_hint_disappears(make_state):
    """After 1-2 wrong answers then one correct, consecutive_errors reset and confidence increases."""
    sid, concept = "task9-s1", "force"
    state = make_state(
        event_payload={
            "student_id": sid,
            "content": "force = mass * velocity",
            "target_concept": concept,
            "is_correct": False,
            "time_spent": 20.0,
        },
    )
    # Turn 1: wrong
    state = _node_turn(state, content="wrong first time", is_correct=False)
    assert state["response_to_student"]

    # Turn 2: wrong again
    state = _node_turn(state, content="still wrong", is_correct=False)
    model_after_errors = shared_memory.read("student_cognitive_models", sid)
    assert model_after_errors is not None
    conf_after_errors = model_after_errors["value"]["concepts"][concept]["confidence"]
    errors_after_2 = model_after_errors["value"]["concepts"][concept]["consecutive_errors"]
    assert errors_after_2 >= 1

    # Turn 3: correct answer -> hint "disappears" (cognition state resets)
    state = _node_turn(
        state,
        content="F = m * a",
        is_correct=True,
        time_spent=10.0,
    )
    assert state["response_to_student"]

    model = shared_memory.read("student_cognitive_models", sid)
    assert model is not None
    concept_data = model["value"]["concepts"][concept]
    assert concept_data["consecutive_errors"] == 0
    assert concept_data["confidence"] > conf_after_errors


# ---------------------------------------------------------------------------
# 2. Same concept multiple errors -> confirm strategy switch
# ---------------------------------------------------------------------------

def test_02_same_concept_multiple_errors_strategy_switch(make_state):
    """After 3+ consecutive errors on same concept, hint strategy must change."""
    sid, concept = "task9-s2", "force"
    state = make_state(
        event_payload={
            "student_id": sid,
            "content": "force = mass * velocity",
            "target_concept": concept,
            "is_correct": False,
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
            (t["result"] for t in state["tools_to_call"] if t["tool"] == "construct_hint"),
            None,
        )
        if hint:
            strategies_seen.append(hint["strategy"])

    assert len(strategies_seen) >= 2
    assert strategies_seen[-1] != strategies_seen[0], (
        f"Strategy should have switched but stayed {strategies_seen}"
    )


# ---------------------------------------------------------------------------
# 3. >=5 errors -> confirm escalation triggered
# ---------------------------------------------------------------------------

def test_03_five_errors_triggers_escalation(make_state):
    """After 5 consecutive errors on same concept, escalate_to_human must be called."""
    sid = "task9-s3"
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
    # Tool return shape: escalation_id, student_message, etc. (reason is input, not in return)
    assert esc.get("student_message")


# ---------------------------------------------------------------------------
# 4. Out-of-scope question -> confirm boundary intercept
# ---------------------------------------------------------------------------

def test_04_out_of_scope_boundary_intercept(make_state, seed_authority_graph):
    """Strict scope + out-of-scope question must return boundary decline, not normal hint."""
    seed_authority_graph(
        scope_level="strict",
        session_id="test-session",
        curriculum_topics=["newton_second_law", "force"],
    )
    state = make_state(
        event_payload={
            "student_id": "task9-s4",
            "content": "Explain quantum entanglement please",
            "target_concept": "quantum_mechanics",
            "is_correct": False,
        },
    )
    state = socratic_companion_node(state)

    # Strict boundary uses decline text: "outside... covering... focus on... current topic"
    response = state["response_to_student"].lower()
    assert any(
        phrase in response
        for phrase in ["outside", "focus on", "current topic"]
    )


def test_04_moderate_boundary_bridge(make_state, seed_authority_graph):
    """Moderate scope + out-of-scope question must bridge back to curriculum."""
    seed_authority_graph(
        scope_level="moderate",
        session_id="test-session",
        curriculum_topics=["newton_second_law", "force"],
    )
    state = make_state(
        event_payload={
            "student_id": "task9-s4b",
            "content": "How is E=mc² derived?",
            "target_concept": "relativity",
            "is_correct": False,
        },
    )
    state = socratic_companion_node(state)

    # Moderate boundary uses bridge text: "Interesting connection!... cover later... For now..."
    response = state["response_to_student"].lower()
    assert any(
        phrase in response
        for phrase in ["interesting connection", "cover later", "for now"]
    )


# ---------------------------------------------------------------------------
# 5. Cognitive model correctly updated after multi-turn
# ---------------------------------------------------------------------------

def test_05_cognitive_model_updated_after_multiturn(make_state):
    """Multi-turn mix of right/wrong: model must show correct confidence and consecutive_errors."""
    sid = "task9-s5"
    state = make_state(
        event_payload={
            "student_id": sid,
            "content": "force = mass * velocity",
            "target_concept": "force",
            "is_correct": False,
            "time_spent": 20.0,
        },
    )
    # Force: wrong twice
    state = _node_turn(state, content="wrong", is_correct=False)
    state = _node_turn(state, content="still wrong", is_correct=False)

    # Momentum: correct once
    state = _node_turn(
        state,
        content="p = m * v",
        target_concept="momentum",
        is_correct=True,
        time_spent=10.0,
    )

    # Force: correct once (reset)
    state = _node_turn(
        state,
        content="F = m * a",
        target_concept="force",
        is_correct=True,
        time_spent=8.0,
    )

    model = shared_memory.read("student_cognitive_models", sid)
    assert model is not None
    concepts = model["value"]["concepts"]

    assert "force" in concepts
    assert "momentum" in concepts
    assert concepts["force"]["consecutive_errors"] == 0
    assert concepts["momentum"]["consecutive_errors"] == 0
    # Both concepts updated: confidence is numeric and non-negative after multi-turn
    assert isinstance(concepts["force"]["confidence"], (int, float))
    assert isinstance(concepts["momentum"]["confidence"], (int, float))
    assert concepts["force"]["confidence"] >= 0
    assert concepts["momentum"]["confidence"] >= 0
