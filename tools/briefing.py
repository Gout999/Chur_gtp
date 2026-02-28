"""
synthesize_briefing: generate personalized briefing for student.
PRD §2.3.2; Phase 4 (Engineer C).

- Input: event (new paper / repo / news item) and optional curriculum_context.
- Output: should_notify, personalized_content, curriculum_bridge, complexity_level, suggested_action.
- All user-facing text is in English (student uploads and sources like arXiv/GitHub are English).
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4


def _normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize event from arxiv (paper) or github (repo) or generic news.
    Returns a unified dict with title_or_name, description, relevance, source.
    """
    source = event.get("source", "unknown")
    if source == "arxiv":
        return {
            "title_or_name": event.get("title", ""),
            "description": event.get("summary", ""),
            "relevance": event.get("relevance_score", 0.0),
            "source": source,
            "id": event.get("id", ""),
            "url": event.get("pdf_url", ""),
            "authors": event.get("authors", []),
        }
    if source == "github":
        return {
            "title_or_name": event.get("repo", event.get("name", "")),
            "description": event.get("description", ""),
            "relevance": event.get("relevance", event.get("relevance_score", 0.0)),
            "source": source,
            "id": event.get("repo", ""),
            "url": event.get("url", ""),
            "authors": [],
        }
    # Generic news or other
    return {
        "title_or_name": event.get("title", event.get("name", "New item")),
        "description": event.get("summary", event.get("description", "")),
        "relevance": event.get("relevance_score", event.get("relevance", 0.5)),
        "source": source,
        "id": event.get("id", ""),
        "url": event.get("url", ""),
        "authors": event.get("authors", []),
    }


def _build_personalized_content(
    event: Dict[str, Any],
    curriculum_topic: str,
    extra_count: int = 0,
) -> str:
    """Build English personalized summary explaining why this is relevant."""
    title = event.get("title_or_name", "This item")
    description = (event.get("description") or "").strip()
    relevance = event.get("relevance", 0)
    source = event.get("source", "source")

    if source == "arxiv":
        snippet = description[:400] + "..." if len(description) > 400 else description
        if not snippet:
            snippet = "No abstract available."
        text = (
            f"A new paper aligns with your interests: \"{title}\". "
            f"Relevance to your interests: {relevance:.0%}. "
            f"Abstract: {snippet}"
        )
    elif source == "github":
        text = (
            f"A repository matches your interests: \"{title}\". "
            f"Relevance: {relevance:.0%}. "
        )
        if description:
            text += f"Description: {description[:300]}{'...' if len(description) > 300 else ''}. "
    else:
        text = (
            f"New content: \"{title}\". "
            f"Relevance: {relevance:.0%}. "
        )
        if description:
            text += f"{description[:300]}{'...' if len(description) > 300 else ''}. "

    if extra_count > 0:
        text += f" Plus {extra_count} other relevant item(s) from this round."
    return text.strip()


def _build_curriculum_bridge(
    event: Dict[str, Any],
    curriculum_context: Optional[Dict[str, Any]],
) -> str:
    """Explain in English how this content connects to current class/curriculum."""
    if not curriculum_context:
        return (
            "This content can support your self-directed learning. "
            "When your course covers related topics, you can revisit it to deepen the connection."
        )
    topic = curriculum_context.get("topic", "")
    units = curriculum_context.get("units", curriculum_context.get("curriculum_nodes", []))
    if isinstance(units, list) and units:
        unit_names = [u.get("name", u.get("title", str(u))) for u in units[:3] if isinstance(u, dict)]
        unit_str = ", ".join(unit_names) if unit_names else "current units"
    else:
        unit_str = "current units"

    if topic:
        return (
            f"This connects to your current curriculum topic: \"{topic}\". "
            f"You can use it to reinforce {unit_str} or bring it up for discussion in class."
        )
    return (
        f"This can reinforce what you are learning in {unit_str}. "
        "Consider linking it to your notes or bringing it to class discussion."
    )


def _decide_should_notify(
    relevance: float,
    has_curriculum: bool,
    relevance_threshold: float = 0.5,
) -> bool:
    """Decide whether to notify the student (avoid over-interruption)."""
    if relevance >= 0.7:
        return True
    if relevance >= relevance_threshold and has_curriculum:
        return True
    return relevance >= relevance_threshold


def _estimate_complexity(event: Dict[str, Any]) -> float:
    """Estimate complexity level 0.0–1.0 from event (e.g. paper vs short news)."""
    source = event.get("source", "")
    description = (event.get("description") or "")
    if source == "arxiv":
        # Longer abstract often indicates more technical depth
        return min(0.3 + len(description) / 2000.0, 1.0)
    if source == "github":
        return min(0.4 + (len(description) / 1000.0 if description else 0.0), 1.0)
    return 0.5


def _empty_briefing(student_id: str) -> Dict[str, Any]:
    """Return a briefing when there is no new content (empty event or empty content_items)."""
    briefing_id = f"brief_{uuid4().hex[:12]}"
    msg = "No new relevant content found in this round. We will keep monitoring."
    result: Dict[str, Any] = {
        "briefing_id": briefing_id,
        "student_id": student_id,
        "should_notify": False,
        "personalized_content": msg,
        "curriculum_bridge": (
            "When new content matches your interests and curriculum, we will notify you."
        ),
        "complexity_level": 0.0,
        "suggested_action": "save_for_later",
    }
    result["summary"] = result["personalized_content"]
    return result


def _suggest_action(
    relevance: float,
    complexity: float,
    has_curriculum: bool,
) -> Literal["read_now", "save_for_later", "discuss_in_class"]:
    """Suggest one of read_now, save_for_later, discuss_in_class."""
    if relevance >= 0.8 and complexity <= 0.6:
        return "read_now"
    if has_curriculum and relevance >= 0.6:
        return "discuss_in_class"
    return "save_for_later"


def synthesize_briefing(
    student_id: str,
    event: Optional[Dict[str, Any]] = None,
    curriculum_context: Optional[Dict[str, Any]] = None,
    *,
    content_items: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Create a personalized briefing when new relevant content is detected.

    Curiosity Catalyst uses this to decide:
    - Is this worth interrupting the student?
    - How to explain the connection to their interests?
    - What curriculum bridge can be made?

    Args:
        student_id: Target student.
        event: A single new content item (paper, repo, or news). Must be provided
            unless content_items is provided for backward compatibility.
        curriculum_context: Optional. Current classroom topics from shared memory
            (e.g. topic, units, curriculum_nodes). Used for curriculum_bridge.
        content_items: Optional. List of items (e.g. top_papers + top_resources).
            If provided and event is None, the first item is used as the primary
            event and the rest are summarized in personalized_content (backward
            compatibility with catalyst node).

    Returns:
        briefing_id: Unique id for this briefing.
        should_notify: Whether to notify the student (agent decision).
        personalized_content: English summary tailored to the student.
        curriculum_bridge: English explanation of how it connects to class.
        complexity_level: Float 0.0–1.0.
        suggested_action: "read_now" | "save_for_later" | "discuss_in_class".
        summary: Alias for personalized_content (for existing node compatibility).
    """
    # Backward compatibility: allow content_items when event is not provided
    if event is None and content_items:
        items = [e for e in content_items[:10] if e]  # skip empty dicts so we don't drop valid items
        event = items[0] if items else {}
        extra_count = len(items) - 1
    else:
        if event is None:
            event = {}
        extra_count = 0

    # No content: return a neutral briefing and do not notify (avoids fake "New item" / 50% relevance)
    if not event:
        return _empty_briefing(student_id)

    normalized = _normalize_event(event)
    topic = (curriculum_context or {}).get("topic", "current curriculum")
    personalized_content = _build_personalized_content(
        normalized, topic, extra_count=extra_count
    )
    curriculum_bridge = _build_curriculum_bridge(normalized, curriculum_context)
    relevance = float(normalized.get("relevance", 0.0))
    has_curriculum = bool(curriculum_context and curriculum_context.get("topic"))
    should_notify = _decide_should_notify(relevance, has_curriculum)
    complexity_level = round(_estimate_complexity(normalized), 2)
    suggested_action = _suggest_action(
        relevance, complexity_level, has_curriculum
    )

    briefing_id = f"brief_{uuid4().hex[:12]}"

    result: Dict[str, Any] = {
        "briefing_id": briefing_id,
        "student_id": student_id,
        "should_notify": should_notify,
        "personalized_content": personalized_content,
        "curriculum_bridge": curriculum_bridge,
        "complexity_level": complexity_level,
        "suggested_action": suggested_action,
    }
    # Backward compatibility: node uses result.get("summary", "")
    result["summary"] = personalized_content
    return result
