"""
Briefing tools for Curiosity Catalyst. PRD §2.3.2; Phase 4 (Engineer C).

Functions:
- synthesize_briefing: generate personalized briefing for student.
- discover_connection: find bridges between student interests and curriculum.
- suggest_exploration_path: plan a learning journey from an interest seed.

All user-facing text is in English (student uploads and sources like arXiv/GitHub are English).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

LOG = logging.getLogger("eduguide.tools.briefing")


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


# ---------------------------------------------------------------------------
# discover_connection  (PRD §2.3.2 Tool 3 — simplified version)
# ---------------------------------------------------------------------------

def _extract_boundary_terms(boundary: Dict[str, Any]) -> List[str]:
    """Extract searchable terms from a classroom_knowledge_boundary dict."""
    terms: List[str] = []
    for key in ("nodes", "topics", "concepts", "boundaries", "curriculum_nodes"):
        val = boundary.get(key)
        if isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    terms.append(item.strip().lower())
                elif isinstance(item, dict):
                    for sub_key in ("name", "title", "concept", "topic"):
                        t = item.get(sub_key)
                        if t and isinstance(t, str):
                            terms.append(t.strip().lower())
    for key in ("topic", "subject", "domain"):
        val = boundary.get(key)
        if val and isinstance(val, str):
            terms.append(val.strip().lower())
    return [t for t in terms if t]


def _keyword_overlap_strength(
    personal_node: str,
    boundary_terms: List[str],
) -> float:
    """Compute 0.0–1.0 connection strength via token overlap."""
    if not boundary_terms:
        return 0.0
    personal_tokens = set(personal_node.lower().split())
    if not personal_tokens:
        return 0.0
    best = 0.0
    for term in boundary_terms:
        term_tokens = set(term.split())
        if not term_tokens:
            continue
        overlap = personal_tokens & term_tokens
        score = len(overlap) / max(len(personal_tokens), len(term_tokens))
        if score > best:
            best = score
    return round(min(best, 1.0), 2)


def _find_best_bridge_term(
    personal_node: str,
    boundary_terms: List[str],
) -> str:
    """Return the boundary term with the highest token overlap."""
    if not boundary_terms:
        return ""
    personal_tokens = set(personal_node.lower().split())
    best_term = boundary_terms[0]
    best_score = -1.0
    for term in boundary_terms:
        term_tokens = set(term.split())
        overlap = personal_tokens & term_tokens
        score = len(overlap) / max(len(personal_tokens), len(term_tokens), 1)
        if score > best_score:
            best_score = score
            best_term = term
    return best_term


def discover_connection(
    student_id: str,
    personal_knowledge_node: str,
    classroom_knowledge_boundary: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Actively search for bridges between a student's interest topic and the
    current curriculum.  Simplified rule-based version; optionally enhanced
    by LLM when ``agents.catalyst.llm`` is available.

    PRD §2.3.2 Tool 3.

    Args:
        student_id: Target student.
        personal_knowledge_node: A topic from the student's interest universe.
        classroom_knowledge_boundary: Curriculum / knowledge boundary from
            Architect (``teacher_authority_graph``).  Expected keys include
            any combination of ``nodes``, ``topics``, ``concepts``,
            ``boundaries``, ``topic``, ``subject``, etc.

    Returns:
        connection_id, connection_strength (0.0–1.0), bridge_concept,
        explanation, potential_learning_outcome, suggested_activity.
    """
    connection_id = f"conn_{uuid4().hex[:12]}"
    boundary_terms = _extract_boundary_terms(classroom_knowledge_boundary)

    # --- Try LLM-enhanced discovery first ---
    llm_result = _discover_connection_llm(
        student_id, personal_knowledge_node, classroom_knowledge_boundary,
    )
    if llm_result is not None:
        llm_result["connection_id"] = connection_id
        return llm_result

    # --- Fallback: rule-based keyword overlap ---
    strength = _keyword_overlap_strength(personal_knowledge_node, boundary_terms)
    bridge_term = _find_best_bridge_term(personal_knowledge_node, boundary_terms)

    if strength >= 0.3 and bridge_term:
        bridge_concept = (
            f"The overlap between \"{personal_knowledge_node}\" and "
            f"\"{bridge_term}\" in the curriculum"
        )
        explanation = (
            f"Your interest in \"{personal_knowledge_node}\" connects to the "
            f"classroom topic \"{bridge_term}\". Exploring this bridge can "
            f"deepen both your personal and academic understanding."
        )
        learning_outcome = (
            f"A richer understanding of \"{bridge_term}\" through the lens "
            f"of \"{personal_knowledge_node}\"."
        )
        activity = (
            f"Write a short comparison between \"{personal_knowledge_node}\" "
            f"and \"{bridge_term}\", highlighting shared principles."
        )
    else:
        bridge_concept = f"\"{personal_knowledge_node}\" as independent exploration"
        explanation = (
            f"No strong direct link was found between "
            f"\"{personal_knowledge_node}\" and current curriculum topics. "
            f"This can still serve as valuable self-directed exploration."
        )
        learning_outcome = (
            f"Broadened perspective from independent study of "
            f"\"{personal_knowledge_node}\"."
        )
        activity = (
            f"Prepare a brief presentation on \"{personal_knowledge_node}\" "
            f"and look for potential future curriculum tie-ins."
        )

    return {
        "connection_id": connection_id,
        "connection_strength": strength,
        "bridge_concept": bridge_concept,
        "explanation": explanation,
        "potential_learning_outcome": learning_outcome,
        "suggested_activity": activity,
    }


def _discover_connection_llm(
    student_id: str,
    personal_knowledge_node: str,
    classroom_knowledge_boundary: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Attempt LLM-powered connection discovery; return None if unavailable."""
    try:
        from agents.catalyst.llm import _call_minimax
    except Exception:
        return None

    import json as _json

    boundary_desc = ", ".join(_extract_boundary_terms(classroom_knowledge_boundary)[:15])
    if not boundary_desc:
        boundary_desc = str(classroom_knowledge_boundary)[:500]

    system = (
        "You find bridges between a student's personal interest and classroom "
        "curriculum. Output ONLY valid JSON with keys: connection_strength "
        "(float 0-1), bridge_concept (str), explanation (str), "
        "potential_learning_outcome (str), suggested_activity (str)."
    )
    user = (
        f"Student interest: {personal_knowledge_node}\n"
        f"Curriculum topics: {boundary_desc}\n\n"
        "Find the best bridge."
    )
    content = _call_minimax(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.4,
        max_tokens=512,
    )
    if not content:
        return None

    try:
        if "```" in content:
            for marker in ("```json", "```"):
                if marker in content:
                    content = content.split(marker)[1]
            if "```" in content:
                content = content.split("```")[0]
        parsed = _json.loads(content.strip())
        strength = float(parsed.get("connection_strength", 0.0))
        return {
            "connection_strength": round(max(0.0, min(1.0, strength)), 2),
            "bridge_concept": str(parsed.get("bridge_concept", "")),
            "explanation": str(parsed.get("explanation", "")),
            "potential_learning_outcome": str(parsed.get("potential_learning_outcome", "")),
            "suggested_activity": str(parsed.get("suggested_activity", "")),
        }
    except (_json.JSONDecodeError, TypeError, ValueError) as exc:
        LOG.warning("discover_connection LLM parse error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# suggest_exploration_path  (PRD §2.3.2 — simplified version)
# ---------------------------------------------------------------------------

def suggest_exploration_path(
    student_id: str,
    interest_seed: str,
    *,
    current_signals: Optional[Dict[str, Any]] = None,
    num_steps: int = 4,
) -> Dict[str, Any]:
    """
    Plan a learning journey starting from *interest_seed*.

    PRD §2.3.2 TOOLS AVAILABLE — ``suggest_exploration_path(interest_seed)``.
    Simplified version: returns a structured multi-step path.  Optionally
    enhanced by LLM when available.

    Args:
        student_id: Target student.
        interest_seed: Starting topic / keyword.
        current_signals: Optional interest_signals dict (keywords,
            research_directions, tech_stack) for context.
        num_steps: Number of steps in the exploration path (default 4).

    Returns:
        path_id, interest_seed, steps (list of dicts with title, description,
        resource_hint, difficulty), estimated_duration, difficulty_progression.
    """
    path_id = f"path_{uuid4().hex[:12]}"
    num_steps = max(2, min(num_steps, 8))

    llm_result = _suggest_path_llm(
        student_id, interest_seed, current_signals, num_steps,
    )
    if llm_result is not None:
        llm_result["path_id"] = path_id
        llm_result["interest_seed"] = interest_seed
        return llm_result

    # --- Fallback: template-based path ---
    steps = _build_template_path(interest_seed, current_signals, num_steps)
    return {
        "path_id": path_id,
        "interest_seed": interest_seed,
        "steps": steps,
        "estimated_duration": f"{num_steps * 2}-{num_steps * 4} hours",
        "difficulty_progression": "beginner → intermediate",
    }


def _build_template_path(
    seed: str,
    signals: Optional[Dict[str, Any]],
    num_steps: int,
) -> List[Dict[str, Any]]:
    """Generate a generic exploration path from templates."""
    templates = [
        {
            "title": f"Foundations of {seed}",
            "description": f"Read an introductory survey or tutorial on {seed} to build baseline understanding.",
            "resource_hint": f"Search for \"{seed} introduction\" or \"{seed} survey\" on arXiv / Google Scholar.",
            "difficulty": 0.2,
        },
        {
            "title": f"Key concepts in {seed}",
            "description": f"Identify and summarise the 3-5 core concepts that underpin {seed}.",
            "resource_hint": f"Look for a textbook chapter or review article on {seed}.",
            "difficulty": 0.35,
        },
        {
            "title": f"Hands-on exploration of {seed}",
            "description": f"Find an open-source project or dataset related to {seed} and experiment.",
            "resource_hint": f"Search GitHub for \"{seed}\" repositories with good documentation.",
            "difficulty": 0.5,
        },
        {
            "title": f"Connect {seed} to your studies",
            "description": f"Write a short note linking {seed} to your current coursework or research direction.",
            "resource_hint": "Review your recent class notes or uploaded materials for overlap.",
            "difficulty": 0.6,
        },
        {
            "title": f"Deep dive: recent advances in {seed}",
            "description": f"Read 2-3 recent papers on {seed} and note open questions.",
            "resource_hint": f"Use arXiv or Semantic Scholar to find papers from the last 12 months on {seed}.",
            "difficulty": 0.75,
        },
        {
            "title": f"Share & discuss {seed}",
            "description": f"Prepare a brief presentation or discussion outline on {seed} for class.",
            "resource_hint": "Focus on what surprised you and potential classroom applications.",
            "difficulty": 0.8,
        },
    ]

    if signals:
        directions = signals.get("research_directions", [])
        if directions:
            extra_topic = str(directions[0]).strip()
            templates.append({
                "title": f"Cross-pollinate: {seed} × {extra_topic}",
                "description": (
                    f"Explore how {seed} intersects with your research direction "
                    f"\"{extra_topic}\". Look for shared methods or complementary insights."
                ),
                "resource_hint": f"Search for \"{seed} {extra_topic}\" on Google Scholar.",
                "difficulty": 0.7,
            })

        tech = signals.get("tech_stack", [])
        if tech:
            tool_name = str(tech[0]).strip()
            templates.append({
                "title": f"Apply {tool_name} to {seed}",
                "description": (
                    f"Use {tool_name} (from your tech stack) to build a small "
                    f"prototype or analysis related to {seed}."
                ),
                "resource_hint": f"Search GitHub for \"{seed} {tool_name}\" examples.",
                "difficulty": 0.65,
            })

    templates.sort(key=lambda s: s["difficulty"])
    return templates[:num_steps]


def _suggest_path_llm(
    student_id: str,
    interest_seed: str,
    signals: Optional[Dict[str, Any]],
    num_steps: int,
) -> Optional[Dict[str, Any]]:
    """Attempt LLM-powered path generation; return None if unavailable."""
    try:
        from agents.catalyst.llm import _call_minimax
    except Exception:
        return None

    import json as _json

    ctx_parts: List[str] = []
    if signals:
        kw = signals.get("keywords", [])
        if kw:
            ctx_parts.append(f"Keywords: {', '.join(str(k) for k in kw[:10])}")
        dirs_ = signals.get("research_directions", [])
        if dirs_:
            ctx_parts.append(f"Directions: {', '.join(str(d) for d in dirs_[:5])}")
        tech = signals.get("tech_stack", [])
        if tech:
            ctx_parts.append(f"Tech: {', '.join(str(t) for t in tech[:5])}")
    context = "; ".join(ctx_parts) if ctx_parts else "No prior signals."

    system = (
        f"You plan a {num_steps}-step learning journey for a student. "
        "Output ONLY valid JSON: {\"steps\": [{\"title\": str, \"description\": str, "
        "\"resource_hint\": str, \"difficulty\": float 0-1}], "
        "\"estimated_duration\": str, \"difficulty_progression\": str}."
    )
    user = (
        f"Interest seed: {interest_seed}\n"
        f"Student context: {context}\n"
        f"Generate {num_steps} progressive steps."
    )
    content = _call_minimax(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.5,
        max_tokens=1024,
    )
    if not content:
        return None

    try:
        if "```" in content:
            for marker in ("```json", "```"):
                if marker in content:
                    content = content.split(marker)[1]
            if "```" in content:
                content = content.split("```")[0]
        parsed = _json.loads(content.strip())
        steps = parsed.get("steps", [])
        if not isinstance(steps, list) or not steps:
            return None
        clean_steps = []
        for s in steps[:num_steps]:
            clean_steps.append({
                "title": str(s.get("title", "")),
                "description": str(s.get("description", "")),
                "resource_hint": str(s.get("resource_hint", "")),
                "difficulty": round(max(0.0, min(1.0, float(s.get("difficulty", 0.5)))), 2),
            })
        return {
            "steps": clean_steps,
            "estimated_duration": str(parsed.get("estimated_duration", f"{num_steps * 2}-{num_steps * 4} hours")),
            "difficulty_progression": str(parsed.get("difficulty_progression", "beginner → intermediate")),
        }
    except (_json.JSONDecodeError, TypeError, ValueError) as exc:
        LOG.warning("suggest_exploration_path LLM parse error: %s", exc)
        return None
