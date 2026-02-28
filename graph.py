"""
EduGuide LangGraph: state definition, node registration, routing.
PRD §4.1, Phase 1. Only imports agent nodes; no agent business logic here.
"""
from typing import TypedDict, Dict, Any, List, Optional

# Optional: use LangGraph when available
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    _HAS_LANGGRAPH = True
except ImportError:
    _HAS_LANGGRAPH = False
    END = None  # sentinel when LangGraph not installed

from agents.architect import pedagogical_architect_node
from agents.companion import socratic_companion_node
from agents.catalyst import curiosity_catalyst_node


class EduGuideState(TypedDict, total=False):
    """Shared state across all agents. PRD §4.1."""
    event_type: str
    event_payload: Dict[str, Any]
    current_agent: str
    agent_decision: str
    tools_to_call: List[Dict[str, Any]]
    working_memory: Dict[str, Any]
    response_to_student: Optional[str]
    response_to_teacher: Optional[str]
    notifications: List[Dict[str, Any]]
    session_id: str
    timestamp: str
    loop_count: int


def route_by_event_type(state: EduGuideState) -> str:
    """Route to initial node by event_type. PRD §4.1."""
    event_type = state.get("event_type", "student_message")
    routing_map = {
        "file_upload": "pedagogical_architect",
        "student_message": "socratic_companion",
        "student_question": "socratic_companion",
        "new_content_detected": "curiosity_catalyst",
        "validation_request": "pedagogical_architect",
        "escalation": "socratic_companion",
    }
    return routing_map.get(event_type, "socratic_companion")


def route_by_agent_decision(state: EduGuideState) -> str:
    """Next node from agent_decision. PRD §4.1."""
    decision = state.get("agent_decision", "") or ""
    if "request_validation" in decision:
        return "pedagogical_architect"
    if "need_student_guidance" in decision:
        return "socratic_companion"
    if "explore_connection" in decision:
        return "curiosity_catalyst"
    return END


def should_continue_monitoring(state: EduGuideState) -> str:
    """Catalyst self-loop or end. PRD §4.1."""
    if state.get("loop_count", 0) > 100:
        return END
    return "curiosity_catalyst"


def build_eduguide_graph():
    """
    Build the EduGuide graph with three agent nodes and conditional edges.
    Returns compiled workflow (with checkpointer if LangGraph available).
    """
    if not _HAS_LANGGRAPH:
        return None

    workflow = StateGraph(EduGuideState)

    workflow.add_node("pedagogical_architect", pedagogical_architect_node)
    workflow.add_node("socratic_companion", socratic_companion_node)
    workflow.add_node("curiosity_catalyst", curiosity_catalyst_node)

    workflow.set_conditional_entry_point(route_by_event_type)

    workflow.add_conditional_edges(
        "pedagogical_architect",
        route_by_agent_decision,
        ["socratic_companion", "curiosity_catalyst", END],
    )
    workflow.add_conditional_edges(
        "socratic_companion",
        route_by_agent_decision,
        ["pedagogical_architect", "curiosity_catalyst", END],
    )
    workflow.add_conditional_edges(
        "curiosity_catalyst",
        should_continue_monitoring,
        ["curiosity_catalyst", END],
    )

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
