"""
synthesize_briefing: generate personalized briefing for student.
PRD section 6.4; Phase 4 (Engineer C).
"""
from typing import Any, Dict, List
from uuid import uuid4


def synthesize_briefing(
    student_id: str,
    content_items: List[Dict[str, Any]],
    curriculum_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Return briefing_id, summary, personalized_connections, and suggested_actions.
    """
    topic = curriculum_context.get("topic", "current curriculum")
    summary = (
        f"Found {len(content_items)} relevant updates linked to {topic}."
        if content_items
        else f"No strong matches found today for {topic}; continue monitoring."
    )
    personalized_connections = [
        {
            "content_id": item.get("id") or item.get("repo", ""),
            "connection": f"This item can reinforce {topic}.",
        }
        for item in content_items[:3]
    ]
    suggested_actions = [
        "Skim one item and write a 3-sentence reflection.",
        "Identify one concept overlap with class material.",
    ]

    return {
        "briefing_id": f"brief_{uuid4().hex[:12]}",
        "student_id": student_id,
        "summary": summary,
        "personalized_connections": personalized_connections,
        "suggested_actions": suggested_actions,
    }
