"""Student endpoints."""
from typing import Any, Dict, List

from fastapi import APIRouter

from memory.shared import shared_memory

router = APIRouter()


@router.get("/{student_id}")
def get_student(student_id: str) -> dict:
    return {"student_id": student_id}


@router.get("/{student_id}/hub")
def get_student_hub(student_id: str) -> Dict[str, Any]:
    """
    Self-study Hub：返回该学生的兴趣画像与个性化推荐内容。

    读取 shared_memory 中 Catalyst 写入的 interest_signals 和
    pending_validations，组装为学生端可消费的推荐列表。
    """
    interest_entry = shared_memory.read("interest_signals", student_id)
    interest_profile: Dict[str, Any] = {}
    if interest_entry:
        value = interest_entry.get("value", {})
        interest_profile = {
            "keywords": value.get("keywords", []),
            "research_directions": value.get("research_directions", []),
            "tech_stack": value.get("tech_stack", []),
            "confidence": value.get("confidence", 0.0),
            "updated_at": value.get("updated_at", ""),
        }

    all_validations = shared_memory.read_all("pending_validations")
    recommendations: List[Dict[str, Any]] = []
    pending_count = 0
    for entry in all_validations:
        val = entry.get("value", {})
        if val.get("student_id") != student_id:
            continue
        status = val.get("status", "pending")
        briefing = val.get("briefing", {})
        sources = val.get("sources", {})

        if status in ("approved", "delivered"):
            recommendations.append({
                "briefing_id": briefing.get("briefing_id", ""),
                "summary": briefing.get("summary", ""),
                "personalized_content": briefing.get("personalized_content", ""),
                "curriculum_bridge": briefing.get("curriculum_bridge", ""),
                "suggested_action": briefing.get("suggested_action", ""),
                "complexity_level": briefing.get("complexity_level", 0.0),
                "status": status,
                "submitted_at": val.get("submitted_at", ""),
                "arxiv_papers": [
                    p for p in sources.get("arxiv", {}).get("top_papers", [])
                ],
                "github_repos": [
                    r for r in sources.get("github", {}).get("top_resources", [])
                ],
            })
        elif status == "pending":
            pending_count += 1

    recommendations.sort(key=lambda r: r.get("submitted_at", ""), reverse=True)

    return {
        "student_id": student_id,
        "interest_profile": interest_profile,
        "recommendations": recommendations,
        "pending_review_count": pending_count,
    }
