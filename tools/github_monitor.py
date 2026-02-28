"""
GitHub monitor: search repositories relevant to student interests.
PRD §5.2, §6.4; Phase 4 (Engineer C).

- 对接 GitHub API；按兴趣关键词搜索仓库；
- 实现相关性评分（关键词匹配，与 arxiv_monitor 一致）；
- 返回 monitor_id、仓库列表、高相关数量、推荐项目等；
- 与 PRD §5.2 及 Phase 4 验收一致；
- 接口可被节点与定时任务直接调用。
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import requests

logger = logging.getLogger("eduguide.tools")

# GitHub Search API
GITHUB_SEARCH_REPOS_URL = "https://api.github.com/search/repositories"
EXA_SEARCH_URL = "https://api.exa.ai/search"
EXA_FIND_SIMILAR_URL = "https://api.exa.ai/findSimilar"


def _get_headers() -> Dict[str, str]:
    """Build request headers; use GITHUB_TOKEN from config when set."""
    try:
        from config import GITHUB_TOKEN
        token = (GITHUB_TOKEN or "").strip()
    except Exception:
        token = ""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def _get_exa_api_key() -> str:
    """读取 Exa API Key。优先 config，再读取 env。"""
    try:
        from config import EXA_API_KEY  # type: ignore

        cfg_key = (EXA_API_KEY or "").strip()
    except Exception:
        cfg_key = ""
    if cfg_key:
        return cfg_key
    env_key = (os.getenv("EXA_API_KEY") or "").strip()
    if env_key:
        return env_key
    return ""


def _exa_headers() -> Dict[str, str]:
    return {
        "x-api-key": _get_exa_api_key(),
        "Content-Type": "application/json",
    }


def _calculate_relevance_keywords(
    repo_name: str,
    repo_description: str,
    interest_keywords: List[str],
) -> float:
    """
    基于关键词匹配计算仓库与兴趣的相关性（0~1）。
    在 name 与 description 中匹配兴趣词；无 embedding 依赖，与 arxiv_monitor 一致。
    """
    if not interest_keywords:
        return 0.0
    text = f"{repo_name} {repo_description or ''}".lower()
    matches = sum(1 for term in interest_keywords if term and term.lower() in text)
    if matches == 0:
        return 0.0
    score = min(matches * 0.25, 1.0)
    if matches >= len(interest_keywords):
        score = 1.0
    return round(score, 4)


def _search_repositories(
    interest_keywords: List[str],
    min_stars: int = 100,
    language: Optional[str] = None,
    created_after_days: Optional[int] = 30,
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    调用 GitHub Search API 搜索仓库。
    使用兴趣关键词、最小 star、可选语言与创建时间过滤。
    """
    keywords = [k.strip() for k in (interest_keywords or []) if k and k.strip()]
    if not keywords:
        keywords = ["education", "learning"]
    query_parts = keywords.copy()
    query_parts.append(f"stars:>{min_stars}")
    if language:
        query_parts.append(f"language:{language}")
    if created_after_days is not None and created_after_days > 0:
        date_str = (datetime.now(timezone.utc) - timedelta(days=created_after_days)).strftime("%Y-%m-%d")
        query_parts.append(f"created:>{date_str}")
    query = " ".join(query_parts)

    params = {
        "q": query,
        "sort": "updated",
        "order": "desc",
        "per_page": min(max_results, 100),
    }
    try:
        resp = requests.get(
            GITHUB_SEARCH_REPOS_URL,
            params=params,
            headers=_get_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.warning("GitHub API error: %s", e)
        return []
    except (ValueError, KeyError) as e:
        logger.warning("GitHub API response parse error: %s", e)
        return []

    items = data.get("items", [])
    results: List[Dict[str, Any]] = []
    for repo in items:
        name = repo.get("full_name", repo.get("name", ""))
        description = repo.get("description") or ""
        relevance = _calculate_relevance_keywords(name, description, keywords)
        results.append({
            "repo": name,
            "name": name,
            "description": description,
            "url": repo.get("html_url", ""),
            "stars": repo.get("stargazers_count", 0),
            "language": repo.get("language"),
            "updated_at": repo.get("updated_at", ""),
            "relevance_score": relevance,
            "relevance": relevance,
            "source": "github",
        })
    return sorted(results, key=lambda x: x["relevance_score"], reverse=True)


def _extract_repo_name_from_url(url: str) -> str:
    if not url:
        return ""
    parts = [p for p in url.strip("/").split("/") if p]
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return url


def _search_repositories_exa(
    interest_keywords: List[str],
    max_results: int = 20,
    natural_language_query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    使用 Exa 的语义检索能力搜索 GitHub 项目（category=github）。
    """
    keywords = [k.strip() for k in (interest_keywords or []) if k and k.strip()]
    if not keywords:
        keywords = ["education", "learning"]

    query = natural_language_query or " ".join(keywords)
    payload: Dict[str, Any] = {
        "query": query,
        "category": "github",
        "numResults": min(max_results, 100),
    }
    try:
        resp = requests.post(
            EXA_SEARCH_URL,
            json=payload,
            headers=_exa_headers(),
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.warning("Exa github search error: %s", e)
        return []
    except (ValueError, KeyError) as e:
        logger.warning("Exa github response parse error: %s", e)
        return []

    raw_results = data.get("results", []) or []
    results: List[Dict[str, Any]] = []
    for item in raw_results:
        url = item.get("url", "") or ""
        name = _extract_repo_name_from_url(url)
        desc = item.get("text", "") or item.get("summary", "") or item.get("title", "") or ""
        kw_score = _calculate_relevance_keywords(name, desc, keywords)
        exa_score = float(item.get("score", 0) or 0)
        relevance = round(min(max(kw_score * 0.7 + exa_score * 0.3, 0.0), 1.0), 4)
        results.append({
            "repo": name,
            "name": name,
            "description": desc[:4000],
            "url": url,
            "stars": item.get("stars", item.get("stargazers_count", 0)) or 0,
            "language": item.get("language"),
            "updated_at": item.get("publishedDate", item.get("updatedAt", "")) or "",
            "relevance_score": relevance,
            "relevance": relevance,
            "source": "github",
        })
    return sorted(results, key=lambda x: x["relevance_score"], reverse=True)


def _expand_related_ecosystem(
    base_repo_url: str,
    interest_keywords: List[str],
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    使用 Exa findSimilar 做 GitHub 生态发现（自动发现相关项目）。
    """
    if not base_repo_url:
        return []
    payload = {
        "url": base_repo_url,
        "category": "github",
        "numResults": min(max_results, 20),
    }
    try:
        resp = requests.post(
            EXA_FIND_SIMILAR_URL,
            json=payload,
            headers=_exa_headers(),
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.warning("Exa github findSimilar error: %s", e)
        return []
    except (ValueError, KeyError) as e:
        logger.warning("Exa github findSimilar parse error: %s", e)
        return []

    out: List[Dict[str, Any]] = []
    for item in data.get("results", []) or []:
        url = item.get("url", "") or ""
        name = _extract_repo_name_from_url(url)
        desc = item.get("text", "") or item.get("summary", "") or item.get("title", "") or ""
        score = _calculate_relevance_keywords(name, desc, interest_keywords)
        out.append({
            "repo": name,
            "name": name,
            "description": desc[:4000],
            "url": url,
            "stars": item.get("stars", item.get("stargazers_count", 0)) or 0,
            "language": item.get("language"),
            "updated_at": item.get("publishedDate", item.get("updatedAt", "")) or "",
            "relevance_score": score,
            "relevance": score,
            "source": "github",
        })
    return sorted(out, key=lambda x: x["relevance_score"], reverse=True)


def _build_suggested_projects(
    top_resources: List[Dict[str, Any]],
    interest_keywords: List[str],
    max_suggestions: int = 3,
) -> List[str]:
    """根据高相关仓库生成推荐项目建议（与 PRD §5.2 一致）。"""
    if not top_resources or not interest_keywords:
        return []
    suggestions: List[str] = []
    for r in top_resources[:max_suggestions]:
        name = r.get("repo", r.get("name", ""))
        if name:
            suggestions.append(f"Explore or contribute to: {name}")
    if not suggestions and top_resources:
        first = top_resources[0].get("repo", top_resources[0].get("name", ""))
        if first:
            suggestions.append(f"Build a mini project inspired by {first}")
    return suggestions[:max_suggestions]


def monitor_github_domain(
    student_id: str,
    interest_keywords: List[str],
    max_results: int = 10,
    relevance_threshold: float = 0.7,
    min_stars: int = 100,
    language: Optional[str] = None,
    created_after_days: Optional[int] = 30,
    natural_language_query: Optional[str] = None,
    use_exa_semantic: bool = False,
) -> Dict[str, Any]:
    """
    Curiosity Catalyst 调用此工具执行 GitHub 监控（按兴趣关键词搜索仓库）。

    对接 GitHub API；按兴趣关键词搜索仓库；实现相关性评分；
    返回 monitor_id、仓库列表、高相关数量、推荐项目等；
    与 PRD §5.2 及 Phase 4 验收一致；可被节点与定时任务直接调用。

    Args:
        student_id: 学生标识。
        interest_keywords: 兴趣关键词列表（来自 interest_signals 或 payload）。
        max_results: 最多返回的仓库数量（API 请求与结果上限）。
        relevance_threshold: 高相关阈值，>= 此分数的仓库计入 high_relevance_count 并进入 top_resources。
        min_stars: 搜索时最小 star 数过滤。
        language: 可选编程语言过滤（如 "Python"）。
        created_after_days: 只考虑最近 N 天内创建的仓库；None 表示不按时间过滤。

    Returns:
        monitor_id: 本次监控任务 ID；
        student_id: 学生 ID；
        repos_detected: 本次检索到的仓库总数；
        high_relevance_count: 达到 relevance_threshold 的仓库数量；
        top_resources: 高相关仓库列表（供 briefing 使用，与 briefing 期望的 github 项格式一致）；
        suggested_projects: 推荐项目/探索建议列表。
    """
    keywords = interest_keywords or ["education", "learning"]
    exa_key = _get_exa_api_key()
    enable_exa = bool(exa_key) and (use_exa_semantic or bool(natural_language_query))
    recent_repos: List[Dict[str, Any]] = []
    if enable_exa:
        recent_repos = _search_repositories_exa(
            interest_keywords=keywords,
            max_results=max_results,
            natural_language_query=natural_language_query,
        )
    if not recent_repos:
        recent_repos = _search_repositories(
            interest_keywords=keywords,
            min_stars=min_stars,
            language=language,
            created_after_days=created_after_days,
            max_results=max_results,
        )

    # Exa 自动发现相关生态：以首个结果扩展相似仓库，做去重合并
    ecosystem: List[Dict[str, Any]] = []
    if enable_exa and recent_repos:
        ecosystem = _expand_related_ecosystem(
            base_repo_url=recent_repos[0].get("url", ""),
            interest_keywords=keywords,
            max_results=max(3, min(8, max_results // 2)),
        )
    if ecosystem:
        merged: Dict[str, Dict[str, Any]] = {}
        for row in (recent_repos + ecosystem):
            key = row.get("url") or row.get("repo") or row.get("name")
            if key and key not in merged:
                merged[key] = row
        recent_repos = sorted(
            list(merged.values()),
            key=lambda x: x.get("relevance_score", 0),
            reverse=True,
        )[:max_results]
    high_relevance = [
        r for r in recent_repos
        if r.get("relevance_score", 0) >= relevance_threshold
    ]
    top_resources = high_relevance[:10]
    if not top_resources and recent_repos:
        top_resources = recent_repos[:5]
    suggested_projects = _build_suggested_projects(top_resources, keywords)

    return {
        "monitor_id": f"github_mon_{uuid4().hex[:10]}",
        "student_id": student_id,
        "repos_detected": len(recent_repos),
        "high_relevance_count": len(high_relevance),
        "top_resources": top_resources,
        "suggested_projects": suggested_projects,
    }
