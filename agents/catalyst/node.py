"""
Curiosity Catalyst node: monitor arXiv/GitHub, analyze uploads, synthesize briefings.
PRD section 4.1; Phase 4 (Engineer C). graph.py imports this node.

AI integration (MINIMAX):
1. Interest signal extraction from PDF/Word text
2. Relevance scoring for new papers
3. Personalized briefing generation
4. Task orchestration (state-driven tool selection)

Shared memory integration (Task 7):
- Write interest_signals: upload → LLM extract → shared_memory
- Read interest_signals: expand monitoring keywords + personalization
- Write pending_validations: structured for Architect review
- Read pending_validations: process Architect review results → decide push
"""
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from memory.shared import shared_memory
from prompts.catalyst import CURIOSITY_CATALYST_PROMPT
from tools.arxiv_monitor import monitor_arxiv_domain
from tools.briefing import synthesize_briefing
from tools.github_monitor import monitor_github_domain

LOG = logging.getLogger("eduguide.catalyst.node")

State = Dict[str, Any]


def _get_uploaded_text(payload: Dict[str, Any]) -> Optional[str]:
    """从 payload 中提取学生上传文件的文本内容（PDF/Word 已由上游解析为文本传入）。"""
    for key in ("uploaded_file_content", "extracted_text", "file_content", "content"):
        val = payload.get(key)
        if val and isinstance(val, str) and len(val.strip()) > 50:
            return val.strip()
    file_path = payload.get("file_path")
    if file_path and isinstance(file_path, str):
        p = Path(file_path)
        if p.suffix.lower() == ".txt" and p.exists():
            try:
                return p.read_text(encoding="utf-8", errors="ignore").strip()
            except Exception:
                pass
    return None


def _interest_keywords_and_signals(
    payload: Dict[str, Any],
    student_id: str,
) -> Tuple[List[str], Optional[Dict[str, Any]]]:
    """获取 interest_keywords 和完整 interest_signals（用于 LLM 相关性）。"""
    keywords = payload.get("interest_keywords")
    if keywords and isinstance(keywords, list):
        return keywords, None

    entry = shared_memory.read("interest_signals", student_id)
    if not entry:
        return [], None

    value = entry.get("value", {})
    kw = value.get("keywords", [])
    if isinstance(kw, list):
        kw = [str(k).strip() for k in kw if k]
    return kw, value


def _expand_keywords_with_signals(
    keywords: List[str],
    signals: Optional[Dict[str, Any]],
) -> Tuple[List[str], Optional[str]]:
    """
    用 interest_signals 中的 research_directions 和 tech_stack 扩展监控关键词。

    Returns:
        expanded_keywords: 扩展后的关键词列表（去重，上限20个）
        primary_language: tech_stack 中的首选编程语言（供 GitHub 监控过滤），无则 None
    """
    if not signals:
        return keywords, None

    seen = {k.lower() for k in keywords}
    expanded = list(keywords)

    for direction in signals.get("research_directions", []):
        d = str(direction).strip()
        if d and d.lower() not in seen:
            expanded.append(d)
            seen.add(d.lower())

    for tech in signals.get("tech_stack", [])[:5]:
        t = str(tech).strip()
        if t and t.lower() not in seen:
            expanded.append(t)
            seen.add(t.lower())

    primary_language = None
    tech_stack = signals.get("tech_stack", [])
    if isinstance(tech_stack, list) and tech_stack:
        candidate = str(tech_stack[0]).strip()
        if candidate:
            primary_language = candidate

    return expanded[:20], primary_language


def _enrich_curriculum_context(
    curriculum_context: Dict[str, Any],
    signals: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """当 curriculum_context 缺少 topic 时，用 interest_signals.research_directions 补充。"""
    if not signals or curriculum_context.get("topic"):
        return curriculum_context

    directions = signals.get("research_directions", [])
    if not directions:
        return curriculum_context

    enriched = dict(curriculum_context)
    enriched["topic"] = ", ".join(str(d) for d in directions[:3])
    return enriched


def _process_validated_entries(
    student_id: str,
    notifications: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    读取 pending_validations 中 Architect 已审核的条目。

    Architect 审核后通过 shared_memory.update 将 status 改为 "approved"/"rejected"，
    并写入 review_result。Catalyst 据此决定是否推送通知：
    - approved → 创建通知并标记为 delivered
    - rejected → 跳过，标记为 rejected_ack
    """
    entries = shared_memory.read_all("pending_validations")
    for entry in entries:
        val = entry.get("value", {})
        if val.get("student_id") != student_id:
            continue

        status = val.get("status", "pending")
        entry_key = entry.get("key", "")

        if status == "approved":
            briefing = val.get("briefing", {})
            review = val.get("review_result") or {}
            notifications.append({
                "type": "curiosity_briefing",
                "student_id": student_id,
                "briefing_id": briefing.get("briefing_id", ""),
                "summary": briefing.get("summary", ""),
                "validated": True,
                "review_notes": review.get("notes", ""),
            })
            shared_memory.update(
                "pending_validations", entry_key, {"status": "delivered"},
            )
            LOG.info("Delivered approved validation: %s", entry_key)

        elif status == "rejected":
            shared_memory.update(
                "pending_validations", entry_key, {"status": "rejected_ack"},
            )
            LOG.info("Acknowledged rejected validation: %s", entry_key)

    return notifications


def curiosity_catalyst_node(state: State) -> State:
    """
    Monitor external sources, analyze student uploads for interests,
    and prepare a personalized briefing.

    Shared memory integration:
    - Step 0: Read pending_validations for Architect-reviewed entries → push approved
    - Step 1: Analyze uploads → write interest_signals
    - Step 2: Read interest_signals → expand keywords + personalization
    - Step 7: Write pending_validations with Architect-compatible structure
    """
    payload = state.get("event_payload", {})
    student_id = payload.get("student_id", "unknown-student")
    event_type = state.get("event_type", "")

    # --- 0. 读取 Architect 已审核的 pending_validations → 推送已批准的内容 ---
    notifications = list(state.get("notifications", []))
    notifications = _process_validated_entries(student_id, notifications)

    # --- 1. 学生上传分析：提取兴趣并写入 interest_signals ---
    uploaded_text = _get_uploaded_text(payload)
    if uploaded_text:
        try:
            from agents.catalyst.llm import extract_interest_signals
            signals = extract_interest_signals(uploaded_text)
            keywords = signals.get("keywords", [])
            if keywords:
                shared_memory.write(
                    "interest_signals",
                    student_id,
                    {
                        "keywords": keywords,
                        "research_directions": signals.get("research_directions", []),
                        "tech_stack": signals.get("tech_stack", []),
                        "confidence": signals.get("confidence", 0.7),
                        "source_upload": payload.get("file_path", "upload"),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
        except Exception:
            pass

    # --- 2. 读取 interest_signals 获取监控关键词 ---
    keywords, interest_signals = _interest_keywords_and_signals(payload, student_id)
    if not keywords:
        keywords = ["learning science", "education"]

    # --- 2b. 用 interest_signals 扩展监控域（research_directions + tech_stack） ---
    expanded_keywords, primary_language = _expand_keywords_with_signals(
        keywords, interest_signals,
    )

    # --- 3. 调用 arxiv_monitor（扩展后的关键词 + LLM 相关性）---
    arxiv_result = monitor_arxiv_domain(
        student_id=student_id,
        interest_keywords=expanded_keywords,
        interest_signals=interest_signals,
        use_llm_relevance=bool(interest_signals),
    )

    # --- 4. 调用 github_monitor（扩展关键词 + tech_stack 语言过滤）---
    github_result = monitor_github_domain(
        student_id=student_id,
        interest_keywords=expanded_keywords,
        language=primary_language,
    )

    # --- 5. 合并内容并生成简报（用 research_directions 补充 curriculum_context）---
    content_items: List[Dict[str, Any]] = []
    content_items.extend(arxiv_result.get("top_papers", []))
    content_items.extend(github_result.get("top_resources", []))

    curriculum_context = payload.get("curriculum_context", {})
    curriculum_context = _enrich_curriculum_context(curriculum_context, interest_signals)

    briefing_result = synthesize_briefing(
        student_id=student_id,
        content_items=content_items,
        curriculum_context=curriculum_context,
    )

    # --- 6. 可选：LLM 增强简报摘要 ---
    if content_items:
        try:
            from agents.catalyst.llm import generate_briefing_summary
            llm_summary = generate_briefing_summary(
                content_items,
                curriculum_context,
                CURIOSITY_CATALYST_PROMPT,
            )
            if llm_summary:
                briefing_result["summary"] = llm_summary
                briefing_result["personalized_content"] = llm_summary
        except Exception:
            pass

    # --- 7. 写 pending_validations（与 Architect 约定的结构）---
    should_notify = briefing_result.get("should_notify", bool(content_items))
    if content_items:
        validation_key = f"{student_id}:{state.get('session_id', 'global')}"
        shared_memory.write(
            "pending_validations",
            validation_key,
            {
                "student_id": student_id,
                "status": "pending",
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "content_type": "curiosity_briefing",
                "briefing": briefing_result,
                "sources": {
                    "arxiv": {
                        "monitor_id": arxiv_result.get("monitor_id"),
                        "high_relevance_count": arxiv_result.get("high_relevance_count", 0),
                        "top_papers": [
                            {
                                "id": p.get("id"),
                                "title": p.get("title"),
                                "relevance_score": p.get("relevance_score"),
                            }
                            for p in arxiv_result.get("top_papers", [])[:5]
                        ],
                    },
                    "github": {
                        "monitor_id": github_result.get("monitor_id"),
                        "high_relevance_count": github_result.get("high_relevance_count", 0),
                        "top_resources": [
                            {
                                "repo": r.get("repo"),
                                "relevance_score": r.get("relevance_score"),
                            }
                            for r in github_result.get("top_resources", [])[:5]
                        ],
                    },
                },
                "review_result": None,
            },
        )

    # --- 8. 即时通知（向后兼容：未审核内容仍即时通知；已审核内容在 step 0 处理）---
    if should_notify:
        notifications.append({
            "type": "curiosity_briefing",
            "student_id": student_id,
            "briefing_id": briefing_result.get("briefing_id", ""),
            "validated": False,
        })

    state["current_agent"] = "curiosity_catalyst"
    state["tools_to_call"] = [
        {"tool": "monitor_arxiv_domain", "result": arxiv_result},
        {"tool": "monitor_github_domain", "result": github_result},
        {"tool": "synthesize_briefing", "result": briefing_result},
    ]
    state["notifications"] = notifications
    state["response_to_student"] = briefing_result.get("summary", "")
    state["agent_decision"] = (
        "monitor_continue" if event_type == "monitor_tick" else ""
    )
    state["loop_count"] = state.get("loop_count", 0) + 1
    return state
