"""
Unit tests for tools/github_monitor (Task 6).
- PRD §5.2、Phase 4 验收：对接 GitHub API、按兴趣关键词搜索、相关性评分；
- 返回 monitor_id、仓库列表、高相关数量、推荐项目；
- 与 briefing 的 _normalize_event(github) 及节点 content_items 兼容；
- 边界与异常：空关键词、API 失败、无死循环。
"""
from unittest.mock import patch, MagicMock

import pytest
import requests

from tools.github_monitor import (
    _build_suggested_projects,
    _calculate_relevance_keywords,
    _get_headers,
    _search_repositories,
    monitor_github_domain,
)


# ---- 相关性计算（与 arxiv_monitor 一致：关键词匹配 0~1）----


def test_relevance_keywords_match() -> None:
    """兴趣关键词在 name/description 中匹配时，相关性 > 0。"""
    score = _calculate_relevance_keywords(
        "tensorflow-models",
        "Machine learning and deep learning models for education.",
        ["machine learning", "education"],
    )
    assert score > 0
    assert score <= 1.0


def test_relevance_keywords_full_match() -> None:
    """全部兴趣关键词匹配时得 1.0。"""
    score = _calculate_relevance_keywords(
        "python-education-tools",
        "Python tools for education and learning science.",
        ["python", "education", "learning"],
    )
    assert score == 1.0


def test_relevance_keywords_no_match() -> None:
    """无匹配时相关性为 0。"""
    score = _calculate_relevance_keywords(
        "game-engine",
        "A 3D game engine in C++.",
        ["machine learning", "neural network"],
    )
    assert score == 0.0


def test_relevance_empty_keywords_returns_zero() -> None:
    """兴趣关键词为空时返回 0。"""
    score = _calculate_relevance_keywords("ml-repo", "About ML.", [])
    assert score == 0.0


def test_relevance_score_in_valid_range() -> None:
    """分数始终在 [0, 1]。"""
    score = _calculate_relevance_keywords(
        "reinforcement-learning",
        "RL and reward shaping for games.",
        ["reinforcement", "learning"],
    )
    assert 0 <= score <= 1


def test_relevance_rounds_to_four_decimals() -> None:
    """相关性保留 4 位小数。"""
    score = _calculate_relevance_keywords(
        "one-keyword-repo",
        "Only one keyword here.",
        ["one", "keyword", "repo", "extra", "five"],
    )
    assert isinstance(score, float)
    assert len(str(score).split(".")[-1]) <= 4 or score == 1.0


# ---- _get_headers：不依赖真实 config，仅验证结构 ----


def test_get_headers_has_accept() -> None:
    """请求头包含 Accept。"""
    h = _get_headers()
    assert "Accept" in h
    assert "vnd.github" in h.get("Accept", "")


def test_get_headers_returns_dict() -> None:
    """_get_headers 返回 dict，且含 Accept；有 token 时含 Authorization（依赖 config）。"""
    h = _get_headers()
    assert isinstance(h, dict)
    assert "Accept" in h


# ---- _build_suggested_projects ----


def test_build_suggested_projects_empty_input() -> None:
    """top_resources 或 interest_keywords 为空时返回空列表。"""
    assert _build_suggested_projects([], ["a"]) == []
    assert _build_suggested_projects([{"repo": "x/y"}], []) == []


def test_build_suggested_projects_from_top_resources() -> None:
    """从高相关仓库生成推荐项目文案。"""
    top = [
        {"repo": "owner/a", "name": "owner/a"},
        {"repo": "owner/b", "name": "owner/b"},
    ]
    out = _build_suggested_projects(top, ["python"], max_suggestions=3)
    assert len(out) == 2
    assert "owner/a" in out[0] and "Explore or contribute to" in out[0]
    assert "owner/b" in out[1]


def test_build_suggested_projects_fallback_single() -> None:
    """当项无 repo/name 时用首项做 fallback。"""
    top = [{"description": "no name"}, {"repo": "ok/repo"}]
    out = _build_suggested_projects(top, ["x"])
    assert len(out) <= 2
    if out:
        assert "Build a mini project inspired by" in out[0] or "ok/repo" in "".join(out)


def test_build_suggested_projects_caps_max_suggestions() -> None:
    """suggested_projects 数量不超过 max_suggestions。"""
    top = [
        {"repo": f"o/r{i}", "name": f"o/r{i}"} for i in range(5)
    ]
    out = _build_suggested_projects(top, ["k"], max_suggestions=2)
    assert len(out) == 2


# ---- _search_repositories：Mock GitHub API ----


def _mock_github_api_items(count: int, names: list[str] | None = None) -> list[dict]:
    """构造与 GitHub Search API 一致的 items 结构（供 _search_repositories 的 mock 入参）。"""
    names = names or [f"owner/repo-{i}" for i in range(count)]
    return [
        {
            "id": i,
            "full_name": name,
            "name": name.split("/")[-1],
            "description": f"Description for {name}",
            "html_url": f"https://github.com/{name}",
            "stargazers_count": 100 + i,
            "language": "Python",
            "updated_at": "2025-01-01T00:00:00Z",
        }
        for i, name in enumerate(names)
    ]


def _mock_search_repos_result(count: int, relevance: float = 0.8) -> list[dict]:
    """构造与 _search_repositories 返回值一致的仓库列表（供 monitor_github_domain 的 mock）。"""
    return [
        {
            "repo": f"owner/repo-{i}",
            "name": f"owner/repo-{i}",
            "description": f"Desc {i}",
            "url": f"https://github.com/owner/repo-{i}",
            "stars": 100 + i,
            "language": "Python",
            "updated_at": "2025-01-01T00:00:00Z",
            "relevance_score": relevance,
            "relevance": relevance,
            "source": "github",
        }
        for i in range(count)
    ]


@patch("tools.github_monitor.requests.get")
def test_search_repositories_success(mock_get: MagicMock) -> None:
    """API 成功时返回排序后的仓库列表，含 relevance 与 source=github。"""
    mock_get.return_value = MagicMock(
        status_code=200,
        raise_for_status=MagicMock(),
        json=MagicMock(return_value={"items": _mock_github_api_items(3)}),
    )
    repos = _search_repositories(
        interest_keywords=["python", "education"],
        min_stars=50,
        max_results=10,
    )
    assert len(repos) == 3
    for r in repos:
        assert "repo" in r and "name" in r and r["repo"] == r["name"]
        assert "url" in r and "relevance_score" in r and "relevance" in r
        assert r["source"] == "github"
        assert 0 <= r["relevance_score"] <= 1
    mock_get.assert_called_once()
    call_kw = mock_get.call_args[1]
    assert call_kw["timeout"] == 15
    assert "python" in call_kw["params"]["q"] or "education" in call_kw["params"]["q"]
    assert "stars:>50" in call_kw["params"]["q"]


@patch("tools.github_monitor.requests.get")
def test_search_repositories_api_error_returns_empty(mock_get: MagicMock) -> None:
    """API 异常（RequestException）时返回空列表，不抛异常。"""
    mock_get.side_effect = requests.RequestException("network error")
    repos = _search_repositories(interest_keywords=["ml"], max_results=5)
    assert repos == []


@patch("tools.github_monitor.requests.get")
def test_search_repositories_empty_items(mock_get: MagicMock) -> None:
    """API 返回空 items 时返回空列表。"""
    mock_get.return_value = MagicMock(
        status_code=200,
        raise_for_status=MagicMock(),
        json=MagicMock(return_value={"items": []}),
    )
    repos = _search_repositories(interest_keywords=["rare-keyword-xyz"], max_results=10)
    assert repos == []


@patch("tools.github_monitor.requests.get")
def test_search_repositories_default_keywords(mock_get: MagicMock) -> None:
    """interest_keywords 为空时使用默认 education, learning。"""
    mock_get.return_value = MagicMock(
        status_code=200,
        raise_for_status=MagicMock(),
        json=MagicMock(return_value={"items": []}),
    )
    _search_repositories(interest_keywords=[], max_results=5)
    q = mock_get.call_args[1]["params"]["q"]
    assert "education" in q or "learning" in q
    assert "stars:>" in q


@patch("tools.github_monitor.requests.get")
def test_search_repositories_per_page_capped_at_100(mock_get: MagicMock) -> None:
    """per_page 最大 100，避免 API 限制。"""
    mock_get.return_value = MagicMock(
        status_code=200,
        raise_for_status=MagicMock(),
        json=MagicMock(return_value={"items": []}),
    )
    _search_repositories(interest_keywords=["x"], max_results=200)
    assert mock_get.call_args[1]["params"]["per_page"] == 100


# ---- monitor_github_domain：返回结构与 PRD §5.2、Phase 4 ----


@patch("tools.github_monitor._search_repositories")
def test_monitor_github_domain_return_shape(mock_search: MagicMock) -> None:
    """返回必须字段且类型符合 PRD §5.2。"""
    mock_search.return_value = _mock_search_repos_result(2)

    result = monitor_github_domain(
        student_id="s1",
        interest_keywords=["python"],
        max_results=10,
    )
    assert "monitor_id" in result
    assert result["monitor_id"].startswith("github_mon_")
    assert result["student_id"] == "s1"
    assert "repos_detected" in result
    assert isinstance(result["repos_detected"], int)
    assert "high_relevance_count" in result
    assert isinstance(result["high_relevance_count"], int)
    assert "top_resources" in result
    assert isinstance(result["top_resources"], list)
    assert "suggested_projects" in result
    assert isinstance(result["suggested_projects"], list)


@patch("tools.github_monitor._search_repositories")
def test_monitor_github_domain_high_relevance_and_top_resources(mock_search: MagicMock) -> None:
    """high_relevance_count 与 top_resources 一致；top_resources 最多 10 个。"""
    items = _mock_search_repos_result(5)
    for i in range(3):
        items[i]["relevance_score"] = 0.9
        items[i]["relevance"] = 0.9
    for i in range(3, 5):
        items[i]["relevance_score"] = 0.3
        items[i]["relevance"] = 0.3
    mock_search.return_value = items

    result = monitor_github_domain(
        student_id="s1",
        interest_keywords=["python"],
        relevance_threshold=0.7,
        max_results=10,
    )
    assert result["repos_detected"] == 5
    assert result["high_relevance_count"] == 3
    assert len(result["top_resources"]) == 3
    assert len(result["top_resources"]) <= 10


@patch("tools.github_monitor._search_repositories")
def test_monitor_github_domain_no_high_relevance_fallback_top_five(mock_search: MagicMock) -> None:
    """当无高相关时，top_resources 取 recent_repos 前 5 个。"""
    mock_search.return_value = _mock_search_repos_result(4, relevance=0.2)

    result = monitor_github_domain(
        student_id="s1",
        interest_keywords=["xyz"],
        relevance_threshold=0.9,
        max_results=10,
    )
    assert result["high_relevance_count"] == 0
    assert len(result["top_resources"]) == 4  # 全部 4 个作为 fallback，最多 5
    assert result["repos_detected"] == 4


@patch("tools.github_monitor._search_repositories")
def test_monitor_github_domain_empty_api_returns_valid_structure(mock_search: MagicMock) -> None:
    """API 返回空时仍返回合法结构，无异常。"""
    mock_search.return_value = []
    result = monitor_github_domain(student_id="s1", interest_keywords=["nobody"])
    assert result["repos_detected"] == 0
    assert result["high_relevance_count"] == 0
    assert result["top_resources"] == []
    assert result["suggested_projects"] == []
    assert result["monitor_id"].startswith("github_mon_")


def test_monitor_github_domain_default_keywords() -> None:
    """interest_keywords 为空或 None 时使用默认，不报错。"""
    with patch("tools.github_monitor._search_repositories") as mock_search:
        mock_search.return_value = []
        r1 = monitor_github_domain(student_id="s1", interest_keywords=[])
        r2 = monitor_github_domain(student_id="s1", interest_keywords=None)  # type: ignore[arg-type]
    assert r1["monitor_id"] and r2["monitor_id"]
    assert isinstance(r1["top_resources"], list) and isinstance(r2["top_resources"], list)
    # 内部会传默认关键词给 _search_repositories
    assert mock_search.call_count == 2


# ---- 与 briefing._normalize_event(github) 及节点 content_items 兼容 ----


@patch("tools.github_monitor._search_repositories")
def test_top_resources_compatible_with_briefing_normalize(mock_search: MagicMock) -> None:
    """top_resources 每项含 repo/name, description, relevance/relevance_score, url, source=github。"""
    mock_search.return_value = _mock_search_repos_result(1)

    result = monitor_github_domain(
        student_id="s1",
        interest_keywords=["python"],
        relevance_threshold=0.5,
    )
    for item in result["top_resources"]:
        assert item.get("repo") or item.get("name")
        assert "description" in item
        assert "relevance" in item or "relevance_score" in item
        assert "url" in item
        assert item.get("source") == "github"


@patch("tools.github_monitor._search_repositories")
def test_node_content_items_extend_top_resources(mock_search: MagicMock) -> None:
    """节点用 github_result.get('top_resources', []) 扩展 content_items，键必须存在且为 list。"""
    mock_search.return_value = []
    result = monitor_github_domain(student_id="s1", interest_keywords=[])
    content_items = result.get("top_resources", [])
    assert isinstance(content_items, list)
    assert result["top_resources"] is content_items


# ---- 无死循环与边界 ----


@patch("tools.github_monitor.requests.get")
def test_search_repositories_large_items_finite_loop(mock_get: MagicMock) -> None:
    """大量 items 时单次遍历，不出现死循环。"""
    mock_get.return_value = MagicMock(
        status_code=200,
        raise_for_status=MagicMock(),
        json=MagicMock(return_value={"items": _mock_github_api_items(50)}),
    )
    repos = _search_repositories(interest_keywords=["test"], max_results=50)
    assert len(repos) == 50
    assert len(set(id(r) for r in repos)) == 50  # 无重复引用


def test_relevance_whitespace_only_keywords_ignored() -> None:
    """仅空格的“关键词”不参与匹配。"""
    score = _calculate_relevance_keywords(
        "machine learning repo",
        "About machine learning.",
        ["  ", "", "machine"],
    )
    assert score > 0  # "machine" 匹配


# ---- 与 briefing 实际归一化逻辑一致（无 KeyError）----


@patch("tools.github_monitor._search_repositories")
def test_top_resources_normalizable_by_briefing(mock_search: MagicMock) -> None:
    """top_resources 项可被 briefing._normalize_event(source=github) 安全归一化。"""
    from tools.briefing import _normalize_event

    mock_search.return_value = _mock_search_repos_result(1)
    result = monitor_github_domain(
        student_id="s1",
        interest_keywords=["python"],
        relevance_threshold=0.5,
    )
    for item in result["top_resources"]:
        normalized = _normalize_event(item)
        assert normalized.get("source") == "github"
        assert "title_or_name" in normalized
        assert "url" in normalized
        assert "relevance" in normalized
