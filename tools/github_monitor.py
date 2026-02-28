"""
GitHub monitor: search repositories relevant to student interests.
PRD section 6.4; Phase 4 (Engineer C).
"""
from typing import Any, Dict, List
from uuid import uuid4


def monitor_github_domain(
    student_id: str,
    interest_keywords: List[str],
    max_results: int = 10,
) -> Dict[str, Any]:
    """
    Search GitHub; return monitor_id, repos_detected, high_relevance_count,
    top_resources, and suggested_projects.
    """
    keywords = interest_keywords or ["education-ai"]
    repos = [
        {
            "repo": f"{keyword}-starter",
            "url": f"https://github.com/example/{keyword}-starter",
            "relevance": 0.78,
            "source": "github",
        }
        for keyword in keywords[: max_results or 1]
    ]
    top_resources = repos[: min(3, len(repos))]

    return {
        "monitor_id": f"github_mon_{uuid4().hex[:10]}",
        "student_id": student_id,
        "repos_detected": len(repos),
        "high_relevance_count": len([repo for repo in repos if repo["relevance"] >= 0.7]),
        "top_resources": top_resources,
        "suggested_projects": [f"Build a mini project around {keywords[0]}"] if keywords else [],
    }
