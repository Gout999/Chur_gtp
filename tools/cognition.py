"""
update_student_cognition_map: update student cognitive model from interaction.
PRD section 2.2.2; Phase 3 (Engineer B).
"""
from typing import Any, Dict


def update_student_cognition_map(student_id: str, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return updated_concepts, new_misconceptions, confidence_changes,
    and recommended_focus_areas.
    """
    target_concept = interaction_data.get("target_concept", "current_topic")
    error_analysis = interaction_data.get("error_analysis", {})
    misconception = error_analysis.get("misconception")

    updated_concepts = [{"concept": target_concept, "status": "practicing"}]
    new_misconceptions = [misconception] if misconception else []

    confidence_delta = -0.05 if misconception else 0.02
    confidence_changes = {target_concept: confidence_delta}

    recommended_focus_areas = [target_concept]
    if misconception:
        recommended_focus_areas.append("repair_misconception")

    return {
        "student_id": student_id,
        "updated_concepts": updated_concepts,
        "new_misconceptions": new_misconceptions,
        "confidence_changes": confidence_changes,
        "recommended_focus_areas": recommended_focus_areas,
    }
