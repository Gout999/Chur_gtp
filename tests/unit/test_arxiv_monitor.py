"""
Unit tests for tools/arxiv_monitor (Task 2).
- 返回结构符合 prompt 与节点约定；
- 相关性计算（英文关键词）；
- 默认回退为英文关键词；
- 论文条目字段完整。
"""
import pytest

from tools.arxiv_monitor import (
    _calculate_relevance_keywords,
    monitor_arxiv_domain,
)


# ---- 相关性计算：英文关键词（用户上传为英文，检索用英文）----


def test_relevance_english_keywords_match() -> None:
    """英文关键词在 title/summary 中匹配时，相关性 > 0。"""
    score = _calculate_relevance_keywords(
        "Machine Learning for Education",
        "This paper studies machine learning and deep learning in classrooms.",
        ["machine learning", "education"],
    )
    assert score > 0
    assert score <= 1.0


def test_relevance_english_keywords_full_match() -> None:
    """全部英文关键词匹配时得满分 1.0。"""
    score = _calculate_relevance_keywords(
        "Optimization and gradient descent",
        "We focus on optimization, gradient descent and convergence.",
        ["optimization", "gradient descent"],
    )
    assert score == 1.0


def test_relevance_english_keywords_no_match() -> None:
    """无匹配时相关性为 0。"""
    score = _calculate_relevance_keywords(
        "Quantum Physics",
        "We study quantum entanglement.",
        ["machine learning", "neural network"],
    )
    assert score == 0.0


def test_relevance_empty_keywords_returns_zero() -> None:
    """兴趣关键词为空时相关性为 0。"""
    score = _calculate_relevance_keywords(
        "Machine Learning",
        "About ML.",
        [],
    )
    assert score == 0.0


def test_relevance_score_in_valid_range() -> None:
    """任意英文关键词与文本，分数在 [0, 1]。"""
    score = _calculate_relevance_keywords(
        "Reinforcement Learning in Games",
        "RL and reward shaping.",
        ["reinforcement", "learning"],
    )
    assert 0 <= score <= 1


# ---- 返回结构：符合 prompt 与节点要求 ----


def test_monitor_arxiv_domain_return_shape() -> None:
    """monitor_arxiv_domain 返回必须字段且类型正确。"""
    result = monitor_arxiv_domain(
        student_id="test-student",
        interest_keywords=["machine learning"],
        check_frequency="weekly",
        relevance_threshold=0.7,
        max_results=5,
    )
    assert "monitor_id" in result
    assert result["monitor_id"].startswith("arxiv_mon_")
    assert result["student_id"] == "test-student"
    assert result["check_frequency"] == "weekly"
    assert "recent_papers" in result
    assert isinstance(result["recent_papers"], list)
    assert "high_relevance_count" in result
    assert isinstance(result["high_relevance_count"], int)
    assert result["high_relevance_count"] >= 0
    assert "top_papers" in result
    assert isinstance(result["top_papers"], list)
    assert len(result["top_papers"]) <= 10


def test_monitor_arxiv_domain_top_papers_subset_of_high_relevance() -> None:
    """top_papers 为高相关论文子集，数量不超过 high_relevance_count。"""
    result = monitor_arxiv_domain(
        student_id="s1",
        interest_keywords=["optimization", "gradient"],
        check_frequency="weekly",
        relevance_threshold=0.5,
        max_results=10,
    )
    assert len(result["top_papers"]) <= result["high_relevance_count"]
    for p in result["top_papers"]:
        assert p.get("relevance_score", 0) >= 0.5


def test_monitor_arxiv_domain_paper_entry_structure() -> None:
    """当有论文返回时，每篇包含节点/briefing 所需字段（英文检索）。"""
    result = monitor_arxiv_domain(
        student_id="s1",
        interest_keywords=["machine learning"],
        check_frequency="weekly",
        relevance_threshold=0.0,
        max_results=3,
    )
    required_keys = {"id", "title", "authors", "summary", "pdf_url", "published", "relevance_score", "source"}
    for paper in result["recent_papers"]:
        for k in required_keys:
            assert k in paper, f"paper missing key {k}"
        assert 0 <= paper["relevance_score"] <= 1
        assert paper["source"] == "arxiv"


# ---- 默认关键词为英文（无兴趣时仍用英文检索）----


def test_monitor_arxiv_domain_default_english_keywords() -> None:
    """interest_keywords 为空时使用英文默认词，不报错且返回合法结构。"""
    result = monitor_arxiv_domain(
        student_id="s1",
        interest_keywords=[],
        check_frequency="weekly",
        max_results=5,
    )
    assert "monitor_id" in result
    assert "recent_papers" in result
    assert "top_papers" in result
    assert result["student_id"] == "s1"


def test_monitor_arxiv_domain_none_keywords_uses_english_default() -> None:
    """interest_keywords 为 None 时使用英文默认，返回合法结构。"""
    result = monitor_arxiv_domain(
        student_id="s1",
        interest_keywords=None,  # type: ignore[arg-type]
        check_frequency="weekly",
        max_results=5,
    )
    assert "monitor_id" in result
    assert isinstance(result["recent_papers"], list)
    assert isinstance(result["top_papers"], list)


# ---- 与节点调用兼容：top_papers 可直接作为 content_items ----

def test_top_papers_compatible_with_node_content_items() -> None:
    """节点使用 arxiv_result.get('top_papers', []) 扩展 content_items，结构需兼容。"""
    result = monitor_arxiv_domain(
        student_id="s1",
        interest_keywords=["deep learning"],
        check_frequency="weekly",
        relevance_threshold=0.3,
        max_results=5,
    )
    content_items = result.get("top_papers", [])
    for item in content_items:
        assert "title" in item
        assert "relevance_score" in item
        assert "source" in item and item["source"] == "arxiv"
