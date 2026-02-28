"""
Curiosity Catalyst node: monitor arXiv/GitHub and synthesize briefings.
PRD section 4.1; Phase 4 (Engineer C). graph.py imports this node.
"""
from typing import Any, Dict, List

from memory.shared import shared_memory
from tools.arxiv_monitor import monitor_arxiv_domain
from tools.briefing import synthesize_briefing
from tools.github_monitor import monitor_github_domain

State = Dict[str, Any]


def _interest_keywords(payload: Dict[str, Any], student_id: str) -> List[str]:
    keywords = payload.get("interest_keywords")
    if keywords:
        return keywords
    entry = shared_memory.read("interest_signals", student_id)
    if not entry:
        return []
    return entry.get("value", {}).get("keywords", [])


def curiosity_catalyst_node(state: State) -> State:
    """
    Monitor external sources and prepare a personalized briefing.
    """
    payload = state.get("event_payload", {})
    student_id = payload.get("student_id", "unknown-student")
    keywords = _interest_keywords(payload, student_id)

    arxiv_result = monitor_arxiv_domain(student_id=student_id, interest_keywords=keywords)
    github_result = monitor_github_domain(student_id=student_id, interest_keywords=keywords)

    content_items: List[Dict[str, Any]] = []
    content_items.extend(arxiv_result.get("top_papers", []))
    content_items.extend(github_result.get("top_resources", []))

    curriculum_context = payload.get("curriculum_context", {})
    briefing_result = synthesize_briefing(
        student_id=student_id,
        content_items=content_items,
        curriculum_context=curriculum_context,
    )

    validation_key = state.get("session_id", "global")
    shared_memory.write(
        "pending_validations",
        validation_key,
        {
            "student_id": student_id,
            "briefing": briefing_result,
            "sources": {
                "arxiv": arxiv_result,
                "github": github_result,
            },
        },
    )

    should_notify = bool(content_items)
    notifications = list(state.get("notifications", []))
    if should_notify:
        notifications.append(
            {
                "type": "curiosity_briefing",
                "student_id": student_id,
                "briefing_id": briefing_result.get("briefing_id", ""),
            }
        )

    state["current_agent"] = "curiosity_catalyst"
    state["tools_to_call"] = [
        {"tool": "monitor_arxiv_domain", "result": arxiv_result},
        {"tool": "monitor_github_domain", "result": github_result},
        {"tool": "synthesize_briefing", "result": briefing_result},
    ]
    state["notifications"] = notifications
    state["response_to_student"] = briefing_result.get("summary", "")
    state["agent_decision"] = "monitor_continue" if state.get("event_type") == "monitor_tick" else ""
    state["loop_count"] = state.get("loop_count", 0) + 1
    return state
