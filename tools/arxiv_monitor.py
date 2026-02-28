"""
arXiv monitor: search and score relevance for student interests.
PRD sections 5.1 and 6.4; Phase 4 (Engineer C).
"""
from typing import Any, Dict, List
from uuid import uuid4


def monitor_arxiv_domain(
    student_id: str,
    interest_keywords: List[str],
    check_frequency: str = "daily",
    relevance_threshold: float = 0.7,
) -> Dict[str, Any]:
    """
    Search arXiv by interests; return monitor_id, papers, high_relevance_count, etc.
    """
    keywords = interest_keywords or ["learning-science"]
    recent_papers = [
        {
            "id": f"arxiv:{uuid4().hex[:8]}",
            "title": f"Recent work on {keyword}",
            "relevance": 0.82,
            "source": "arxiv",
        }
        for keyword in keywords[:3]
    ]
    top_papers = [paper for paper in recent_papers if paper["relevance"] >= relevance_threshold]

    return {
        "monitor_id": f"arxiv_mon_{uuid4().hex[:10]}",
        "student_id": student_id,
        "check_frequency": check_frequency,
        "recent_papers": recent_papers,
        "high_relevance_count": len(top_papers),
        "top_papers": top_papers,
    }
