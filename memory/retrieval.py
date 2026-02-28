"""
Teacher knowledge retrieval for Companion.

Provides retrieve_teacher_knowledge(query, scope, top_k) used in Phase 1
of the Companion node. When no vector store is wired, builds chunks from
teacher_authority_graph (boundary, latest_material) and teacher_uploads.
PRD: answer/hint content must be grounded in teacher knowledge.
"""
from __future__ import annotations

from typing import Any, Dict, List

from memory.shared import shared_memory

_NS_AUTHORITY = "teacher_authority_graph"
_NS_UPLOADS = "teacher_uploads"


def retrieve_teacher_knowledge(
    query: str,
    scope: Dict[str, Any],
    top_k: int = 5,
    *,
    state_key: str = "global",
) -> List[Dict[str, Any]]:
    """
    Retrieve teacher-authored knowledge chunks relevant to the query.

    Uses curriculum and material metadata from teacher_authority_graph;
    when no vector store is available, returns in-scope concepts and any
    stored upload snippets so hint generation can ground in them.

    Args:
        query: Student question or current input.
        scope: Knowledge boundary dict (scope_level, curriculum_topics,
               knowledge_nodes, etc.).
        top_k: Maximum number of chunks to return.
        state_key: Session key for reading authority (e.g. session_id or "global").

    Returns:
        List of {"content": str, "source": str}. May be empty.
    """
    chunks: List[Dict[str, Any]] = []
    query_lower = (query or "").lower()

    # From boundary: curriculum_topics, related_curriculum_nodes, knowledge_nodes
    topics: List[str] = list(scope.get("curriculum_topics", []))
    for node in scope.get("knowledge_nodes", []):
        name = node.get("concept") or node.get("title") or ""
        if name and name not in topics:
            topics.append(name)
    for node in scope.get("related_curriculum_nodes", []):
        name = node if isinstance(node, str) else (node.get("concept") or node.get("title") or "")
        if name and name not in topics:
            topics.append(name)

    # Prefer topics that match the query, then fill with the rest
    matching: List[Dict[str, Any]] = []
    rest: List[Dict[str, Any]] = []
    for topic in topics:
        if not topic:
            continue
        chunk = {"content": f"Curriculum concept: {topic}.", "source": "teacher_authority_graph"}
        if topic.lower() in query_lower or query_lower in topic.lower():
            matching.append(chunk)
        else:
            rest.append(chunk)
    chunks = (matching + rest)[:top_k]

    if len(chunks) < top_k:
        # Try latest_material from shared memory (Architect writes it)
        entry = shared_memory.read(_NS_AUTHORITY, state_key)
        if not entry and state_key != "global":
            entry = shared_memory.read(_NS_AUTHORITY, "global")
        if entry:
            value = entry.get("value", {})
            material = value.get("latest_material", value.get("latest_boundary", {}))
            for node in material.get("knowledge_nodes", [])[: top_k - len(chunks)]:
                title = node.get("title") or node.get("concept") or "material"
                chunks.append({
                    "content": f"Material: {title}.",
                    "source": "teacher_authority_graph",
                })
                if len(chunks) >= top_k:
                    break

    # Optional: teacher_uploads namespace for any stored text (keyed by upload id)
    if len(chunks) < top_k:
        try:
            uploads = shared_memory.read_all(_NS_UPLOADS, limit=5)
            for u in uploads:
                val = u.get("value", {})
                snippet = val.get("content") or val.get("snippet") or val.get("title") or ""
                if snippet and len(chunks) < top_k:
                    chunks.append({
                        "content": snippet[:500] if isinstance(snippet, str) else str(snippet)[:500],
                        "source": "teacher_uploads",
                    })
        except Exception:
            pass

    return chunks[:top_k]
