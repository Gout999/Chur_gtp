"""
arXiv monitor: search and score relevance for student interests.
PRD §5.1, §6.4; Phase 4 (Engineer C).
- 对接 arXiv API；按兴趣关键词搜索近期论文；
- 相关性计算（关键词匹配；可选 LLM 语义相关性）；
- 返回 monitor_id、论文列表、高相关数量等；
- 接口可被节点与定时任务直接调用。
- 检索关键词需为英文（用户上传文件为 English version）。
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

import arxiv
import requests


logger = logging.getLogger("eduguide.tools")
EXA_SEARCH_URL = "https://api.exa.ai/search"
EXA_FIND_SIMILAR_URL = "https://api.exa.ai/findSimilar"
EXA_CONTENTS_URL = "https://api.exa.ai/contents"


def _calculate_relevance_keywords(
    paper_title: str,
    paper_summary: str,
    interest_keywords: List[str],
) -> float:
    """
    基于关键词匹配计算论文与兴趣的相关性（0~1）。
    在 title 与 summary 中匹配兴趣词，匹配越多分数越高；无 embedding 依赖。
    """
    if not interest_keywords:
        return 0.0
    text = f"{paper_title} {paper_summary}".lower()
    matches = sum(1 for term in interest_keywords if term and term.lower() in text)
    if matches == 0:
        return 0.0
    # 归一化：每个词最多贡献约 0.2，上限 1.0
    score = min(matches * 0.2, 1.0)
    # 若全部词都匹配则给满 1.0
    if matches >= len(interest_keywords):
        score = 1.0
    return round(score, 4)


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


def _extract_arxiv_id_from_url(url: str) -> str:
    if not url:
        return ""
    lowered = url.strip()
    if "/abs/" in lowered:
        return lowered.rsplit("/abs/", 1)[-1]
    if "/pdf/" in lowered:
        raw = lowered.rsplit("/pdf/", 1)[-1]
        return raw.replace(".pdf", "")
    return lowered.rsplit("/", 1)[-1]


def _to_iso_date(raw: Any) -> str:
    if not raw:
        return ""
    if isinstance(raw, str):
        return raw
    try:
        return raw.isoformat()  # datetime
    except Exception:
        return str(raw)


def _search_with_exa_keywords(
    interest_keywords: List[str],
    max_results: int,
    date_range_days: int,
) -> List[Dict[str, Any]]:
    keywords = [k.strip() for k in (interest_keywords or []) if k and k.strip()]
    if not keywords:
        keywords = ["learning science", "education"]
    query = " ".join(keywords)
    payload: Dict[str, Any] = {
        "query": query,
        "numResults": max_results,
        "category": "research paper",
        "includeDomains": ["arxiv.org"],
        "text": {"maxCharacters": 2500},
    }
    if date_range_days > 0:
        start = (datetime.now(timezone.utc) - timedelta(days=date_range_days)).date().isoformat()
        payload["startPublishedDate"] = start
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
        logger.warning("Exa arXiv keyword search error: %s", e)
        return []
    except (ValueError, KeyError) as e:
        logger.warning("Exa arXiv keyword response parse error: %s", e)
        return []
    return data.get("results", []) or []


def _find_similar_with_exa(seed_paper_url: str, max_results: int) -> List[Dict[str, Any]]:
    if not seed_paper_url:
        return []
    payload: Dict[str, Any] = {
        "url": seed_paper_url,
        "numResults": max_results,
        "includeDomains": ["arxiv.org"],
        "category": "research paper",
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
        logger.warning("Exa arXiv findSimilar error: %s", e)
        return []
    except (ValueError, KeyError) as e:
        logger.warning("Exa arXiv findSimilar parse error: %s", e)
        return []
    return data.get("results", []) or []


def _get_contents_with_exa(result_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    ids = [i for i in result_ids if i]
    if not ids:
        return {}
    try:
        resp = requests.post(
            EXA_CONTENTS_URL,
            json={"ids": ids, "text": {"maxCharacters": 5000}},
            headers=_exa_headers(),
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.warning("Exa arXiv contents error: %s", e)
        return {}
    except (ValueError, KeyError) as e:
        logger.warning("Exa arXiv contents parse error: %s", e)
        return {}

    out: Dict[str, Dict[str, Any]] = {}
    for item in data.get("results", []) or []:
        item_id = item.get("id", "")
        if item_id:
            out[item_id] = item
    return out


def _normalize_exa_arxiv_result(
    item: Dict[str, Any],
    cleaned: Optional[Dict[str, Any]],
    interest_keywords: List[str],
) -> Dict[str, Any]:
    title = item.get("title", "") or ""
    url = item.get("url", "") or ""
    summary = ""
    if cleaned:
        text_obj = cleaned.get("text", {})
        if isinstance(text_obj, dict):
            summary = text_obj.get("text", "") or ""
        elif isinstance(text_obj, str):
            summary = text_obj
    if not summary:
        summary = item.get("text", "") or item.get("summary", "") or ""
    relevance = _calculate_relevance_keywords(title, summary, interest_keywords)
    return {
        "id": _extract_arxiv_id_from_url(url),
        "title": title,
        "authors": item.get("authorNames", []) or [],
        "summary": summary,
        "pdf_url": item.get("pdfUrl", "") or "",
        "published": _to_iso_date(item.get("publishedDate")),
        "categories": item.get("categories", []) or [],
        "relevance_score": relevance,
        "source": "arxiv",
    }


class ArXivMonitor:
    """
    Curiosity Catalyst 使用此工具监控 arXiv 新论文。
    基于学生兴趣关键词搜索近期论文并计算相关性。
    """

    def __init__(self) -> None:
        self._client = arxiv.Client()

    def search_by_interests(
        self,
        interest_vector: List[str],
        max_results: int = 20,
        date_range_days: int = 7,
        seed_paper_url: Optional[str] = None,
        use_exa_semantic: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        基于学生兴趣向量搜索 arXiv 论文。

        Args:
            interest_vector: 英文关键词列表，如 ["quantum computing", "linear algebra"]（用户上传为英文，检索用英文）
            max_results: 最多向 API 请求的结果数（取回后再按日期过滤）
            date_range_days: 只保留最近 N 天内提交的论文

        Returns:
            论文列表，每项含 id, title, authors, summary, pdf_url, published, categories, relevance_score；
            按 relevance_score 降序排列。
        """
        keywords = [k.strip() for k in (interest_vector or []) if k and k.strip()]
        if not keywords:
            keywords = ["learning science", "education"]
        query = " OR ".join(keywords)
        cutoff = datetime.now(timezone.utc) - timedelta(days=date_range_days)

        # 1) 优先 Exa：支持语义检索 + 类比检索（findSimilar）+ 清洗文本（contents）
        exa_key = _get_exa_api_key()
        exa_results: List[Dict[str, Any]] = []
        if exa_key and (use_exa_semantic or seed_paper_url):
            if seed_paper_url:
                exa_results.extend(_find_similar_with_exa(seed_paper_url, max_results=max_results))
            exa_results.extend(
                _search_with_exa_keywords(
                    interest_keywords=keywords,
                    max_results=max_results,
                    date_range_days=date_range_days,
                )
            )
        if exa_results:
            dedup: Dict[str, Dict[str, Any]] = {}
            for r in exa_results:
                key = r.get("id") or r.get("url") or r.get("title")
                if key and key not in dedup:
                    dedup[key] = r
            unique_items = list(dedup.values())[:max_results]
            contents_map = _get_contents_with_exa([x.get("id", "") for x in unique_items])
            normalized = [
                _normalize_exa_arxiv_result(
                    item=x,
                    cleaned=contents_map.get(x.get("id", "")),
                    interest_keywords=interest_vector or keywords,
                )
                for x in unique_items
            ]
            return sorted(normalized, key=lambda x: x["relevance_score"], reverse=True)

        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )
        results: List[Dict[str, Any]] = []
        try:
            for paper in self._client.results(search):
                if paper.published:
                    pub = paper.published
                    if pub.tzinfo is None:
                        pub = pub.replace(tzinfo=timezone.utc)
                    if pub < cutoff:
                        continue
                relevance = _calculate_relevance_keywords(
                    paper.title,
                    paper.summary,
                    interest_vector or keywords,
                )
                results.append({
                    "id": paper.entry_id.split("/")[-1] if paper.entry_id else "",
                    "title": paper.title,
                    "authors": [str(a) for a in paper.authors],
                    "summary": paper.summary,
                    "pdf_url": paper.pdf_url or "",
                    "published": paper.published.isoformat() if paper.published else "",
                    "categories": getattr(paper, "categories", []) or [],
                    "relevance_score": relevance,
                    "source": "arxiv",
                })
        except Exception as e:
            # 网络或 API 异常时返回空列表，不抛出让调用方可降级
            results = []
            logger.warning("arXiv API error: %s", e)

        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)


def monitor_arxiv_domain(
    student_id: str,
    interest_keywords: List[str],
    check_frequency: Literal["daily", "weekly"] = "daily",
    relevance_threshold: float = 0.7,
    max_results: int = 20,
    interest_signals: Optional[Dict[str, Any]] = None,
    use_llm_relevance: bool = True,
    seed_paper_url: Optional[str] = None,
    use_exa_semantic: bool = False,
) -> Dict[str, Any]:
    """
    Curiosity Catalyst 调用此工具执行 arXiv 监控（立即执行一次搜索）。

    按兴趣关键词搜索近期论文，计算相关性，返回 monitor_id、论文列表、高相关数量等。
    可被节点与定时任务直接 import 调用。

    Args:
        student_id: 学生标识。
        interest_keywords: 兴趣关键词列表，来自 interest_signals 或 payload；应为英文（用户上传文件为 English version，arXiv 检索使用英文）。
        check_frequency: 检查频率，用于决定取近期 1 天或 7 天的论文。
        relevance_threshold: 高相关阈值，>= 此分数的论文计入 high_relevance_count 并进入 top_papers。
        max_results: 向 arXiv 请求的最大结果数。
        interest_signals: 完整兴趣信号（含 keywords, research_directions）用于 LLM 相关性判断。
        use_llm_relevance: 若 True 且 interest_signals 提供，对论文做 LLM 语义相关性评分。

    Returns:
        monitor_id: 本次监控任务 ID；
        student_id: 学生 ID；
        check_frequency: 检查频率；
        recent_papers: 本次检索到的论文列表（含 relevance_score）；
        high_relevance_count: 达到 relevance_threshold 的论文数量；
        top_papers: 高相关论文列表（供 briefing 使用）。
    """
    date_range_days = 7 if check_frequency == "weekly" else 1
    monitor = ArXivMonitor()
    recent_papers = monitor.search_by_interests(
        interest_vector=interest_keywords or ["learning science"],
        max_results=max_results,
        date_range_days=date_range_days,
        seed_paper_url=seed_paper_url,
        use_exa_semantic=use_exa_semantic,
    )

    # 可选：LLM 语义相关性重算
    if use_llm_relevance and interest_signals and recent_papers:
        try:
            from agents.catalyst.llm import score_relevance_batch
            llm_scores = score_relevance_batch(
                recent_papers, interest_signals, max_papers=min(15, len(recent_papers))
            )
            for i, p in enumerate(recent_papers):
                if i < len(llm_scores):
                    p["relevance_score"] = round(llm_scores[i], 4)
            recent_papers = sorted(recent_papers, key=lambda x: x.get("relevance_score", 0), reverse=True)
        except Exception as e:
            logger.warning("LLM relevance fallback: %s", e)

    high_relevance = [
        p for p in recent_papers
        if p.get("relevance_score", 0) >= relevance_threshold
    ]
    top_papers = high_relevance[:10]  # 最多返回 10 篇高相关，供简报使用

    return {
        "monitor_id": f"arxiv_mon_{uuid4().hex[:10]}",
        "student_id": student_id,
        "check_frequency": check_frequency,
        "recent_papers": recent_papers,
        "high_relevance_count": len(high_relevance),
        "top_papers": top_papers,
    }
