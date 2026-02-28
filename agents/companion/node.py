"""
Socratic Companion node: guide students via hints and update cognition map.
PRD section 4.1; Phase 3 (Engineer B). graph.py imports this node.
"""
from typing import Any, Dict, List

from memory.shared import shared_memory
from tools.cognition import update_student_cognition_map
from tools.hints import construct_hint

State = Dict[str, Any]


def _authority_context(state: State) -> Dict[str, Any]:
    key = state.get("session_id") or "global"
    entry = shared_memory.read("teacher_authority_graph", key)
    if not entry:
        return {}
    return entry.get("value", {})


def socratic_companion_node(state: State) -> State:
    """
    Generate a hint and update cognitive model for the active student.
    """
    payload = state.get("event_payload", {})
    student_id = payload.get("student_id", "unknown-student")
    current_input = payload.get("content", "")
    target_concept = payload.get("target_concept", "current_topic")
    error_analysis = payload.get("error_analysis") or {}
    authority = _authority_context(state)

    hint_result = construct_hint(
        student_id=student_id,
        current_input=current_input,
        target_concept=target_concept,
        error_analysis=error_analysis,
    )
    cognition_result = update_student_cognition_map(
        student_id=student_id,
        interaction_data={
            "input": current_input,
            "target_concept": target_concept,
            "error_analysis": error_analysis,
            "authority_scope": authority.get("latest_boundary", {}),
        },
    )

    shared_memory.write("student_cognitive_models", student_id, cognition_result)

    interest_keywords: List[str] = payload.get("interest_keywords", [])
    if interest_keywords:
        shared_memory.write(
            "interest_signals",
            student_id,
            {"student_id": student_id, "keywords": interest_keywords},
        )

    state["current_agent"] = "socratic_companion"
    state["response_to_student"] = hint_result["hint_content"]
    state["tools_to_call"] = [
        {"tool": "construct_hint", "result": hint_result},
        {"tool": "update_student_cognition_map", "result": cognition_result},
    ]
    state["working_memory"] = state.get("working_memory", {})
    state["working_memory"]["cognitive_model"] = cognition_result
    state["agent_decision"] = "explore_connection" if interest_keywords else ""
    state["loop_count"] = state.get("loop_count", 0) + 1
    return state
