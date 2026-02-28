"""
Socratic Companion node: guide student via hints, update cognition map.
PRD §4.1; Phase 3 – Engineer B. graph.py imports this.
"""
from typing import Dict, Any

State = Dict[str, Any]


def socratic_companion_node(state: State) -> State:
    """
    Load student cognition from memory; reason with Companion prompt; call construct_hint, update_student_cognition_map;
    read teacher_authority_graph for boundary; write interest_signals if new interest; set response_to_student.
    """
    # TODO: Load prompt from prompts.companion; bind tools from tools.hints, tools.cognition;
    # run ReAct; update state["response_to_student"]
    state["current_agent"] = "socratic_companion"
    state["agent_decision"] = ""
    state.setdefault("response_to_student", "")
    return state
