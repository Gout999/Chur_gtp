"""
Integration tests for tools/arxiv_monitor (Task 2).
- 真实调用 arXiv API，使用英文关键词；
- 校验返回数据可用于节点与 briefing。
"""
import pytest

from tools.arxiv_monitor import monitor_arxiv_domain


def test_arxiv_monitor_real_api_english_keywords() -> None:
    """
    使用英文关键词调用真实 arXiv API，校验：
    - 返回结构完整；
    - 论文条目含 id/title/relevance_score 等；
    - relevance_score 在 [0, 1]；
    - 关键词为英文（用户上传为 English version）。
    """
    result = monitor_arxiv_domain(
        student_id="integration-test-student",
        interest_keywords=["machine learning", "optimization"],
        check_frequency="weekly",
        relevance_threshold=0.4,
        max_results=15,
    )
    assert result["monitor_id"].startswith("arxiv_mon_")
    assert result["student_id"] == "integration-test-student"
    assert isinstance(result["recent_papers"], list)
    assert isinstance(result["high_relevance_count"], int)
    assert result["high_relevance_count"] >= 0
    assert len(result["top_papers"]) <= 10

    for paper in result["recent_papers"]:
        assert "id" in paper
        assert "title" in paper
        assert "relevance_score" in paper
        assert 0 <= paper["relevance_score"] <= 1
        assert paper["source"] == "arxiv"
        assert "summary" in paper
        assert "pdf_url" in paper

    assert len(result["top_papers"]) <= result["high_relevance_count"]


def test_arxiv_monitor_english_keywords_yield_relevant_titles() -> None:
    """
    英文关键词检索到的论文 title/summary 通常包含或接近这些词
    （arXiv 以英文为主，用户上传为英文，检索用英文）。
    """
    result = monitor_arxiv_domain(
        student_id="s1",
        interest_keywords=["reinforcement learning"],
        check_frequency="weekly",
        relevance_threshold=0.0,
        max_results=10,
    )
    if not result["recent_papers"]:
        pytest.skip("arXiv API returned no papers (network or date filter)")
    first = result["recent_papers"][0]
    text = (first.get("title", "") + " " + first.get("summary", "")).lower()
    assert "reinforcement" in text or "learning" in text or "rl" in text
