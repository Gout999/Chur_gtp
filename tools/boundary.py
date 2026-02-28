"""
establish_knowledge_boundary: evaluate if a query is within teaching scope.
PRD section 2.1.2; Phase 2 (Engineer A).
"""
from typing import Any, Dict, List


def establish_knowledge_boundary(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return in_scope, scope_level, reasoning, recommended_response_type,
    and related_curriculum_nodes.
    """
    normalized = (query or "").strip().lower()
    out_of_scope_markers: List[str] = ["politics", "violence", "self-harm", "malware"]
    in_scope = not any(marker in normalized for marker in out_of_scope_markers)

    scope_level = "core" if in_scope and len(normalized) < 80 else "moderate"
    if not in_scope:
        scope_level = "out_of_scope"

    recommended_response_type = "guided_refusal" if not in_scope else "guided_answer"
    related_curriculum_nodes = context.get("curriculum_nodes", []) if isinstance(context, dict) else []

    return {
        "in_scope": in_scope,
        "scope_level": scope_level,
        "reasoning": (
            "Query contains restricted-topic markers."
            if not in_scope
            else "Query aligns with classroom context."
        ),
        "recommended_response_type": recommended_response_type,
        "related_curriculum_nodes": related_curriculum_nodes,
    }
