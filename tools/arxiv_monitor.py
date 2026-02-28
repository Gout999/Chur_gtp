"""
arXiv monitor: search and score relevance for student interests.
PRD §5.1, §6.4; Phase 4 (Engineer C).
- 对接 arXiv API；按兴趣关键词搜索近期论文；
- 相关性计算（关键词匹配；可选 LLM 语义相关性）；
- 返回 monitor_id、论文列表、高相关数量等；
- 接口可被节点与定时任务直接调用。
- 检索关键词需为英文（用户上传文件为 English version）。
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

import arxiv


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
            import logging
            logging.getLogger("eduguide.tools").warning("arXiv API error: %s", e)

        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)


def monitor_arxiv_domain(
    student_id: str,
    interest_keywords: List[str],
    check_frequency: Literal["daily", "weekly"] = "daily",
    relevance_threshold: float = 0.7,
    max_results: int = 20,
    interest_signals: Optional[Dict[str, Any]] = None,
    use_llm_relevance: bool = True,
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
            import logging
            logging.getLogger("eduguide.tools").warning("LLM relevance fallback: %s", e)

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
