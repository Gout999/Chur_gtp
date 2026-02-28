"""
Pedagogical Architect node: reason and act on knowledge authority.
PRD section 4.1; Phase 2 (Engineer A). graph.py imports this node.
"""
from typing import Any, Dict, List

from memory.shared import shared_memory
from tools.boundary import establish_knowledge_boundary
from tools.ingest import ingest_material

State = Dict[str, Any]


def _resolve_state_key(state: State) -> str:
    return state.get("session_id") or state.get("event_payload", {}).get("course_id") or "global"


def pedagogical_architect_node(state: State) -> State:
    """
    Process teacher-facing events and update authority graph in shared memory.
    """
    payload = state.get("event_payload", {})
    tools_called: List[Dict[str, Any]] = []
    authority_update: Dict[str, Any] = {}

    file_path = payload.get("file_path")
    if file_path:
        ingest_result = ingest_material(
            file_path=file_path,
            source_type="teacher_upload",
            auto_chunk=payload.get("auto_chunk", True),
            custom_chunk_size=payload.get("custom_chunk_size"),
        )
        tools_called.append({"tool": "ingest_material", "result": ingest_result})
        authority_update["latest_material"] = ingest_result

    query = payload.get("query") or payload.get("content")
    if query:
        boundary_result = establish_knowledge_boundary(
            query=query,
            context=payload.get("context", {}),
        )
        tools_called.append({"tool": "establish_knowledge_boundary", "result": boundary_result})
        authority_update["latest_boundary"] = boundary_result

    if authority_update:
        shared_memory.write("teacher_authority_graph", _resolve_state_key(state), authority_update)

    state["current_agent"] = "pedagogical_architect"
    state["tools_to_call"] = tools_called
    state.setdefault("working_memory", {})
    state["working_memory"]["architect_last_observation"] = payload
    state["agent_decision"] = (
        "need_student_guidance"
        if state.get("event_type") in {"file_upload", "validation_request"}
        else ""
    )
    state["loop_count"] = state.get("loop_count", 0) + 1
    return state
