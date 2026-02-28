"""
Curiosity Catalyst node: monitor arXiv/GitHub, analyze uploads, synthesize briefings.
PRD section 4.1; Phase 4 (Engineer C). graph.py imports this node.

AI integration (MINIMAX):
1. Interest signal extraction from PDF/Word text
2. Relevance scoring for new papers
3. Personalized briefing generation
4. Task orchestration (state-driven tool selection)
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from memory.shared import shared_memory
from prompts.catalyst import CURIOSITY_CATALYST_PROMPT
from tools.arxiv_monitor import monitor_arxiv_domain
from tools.briefing import synthesize_briefing
from tools.github_monitor import monitor_github_domain

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
) -> tuple[List[str], Optional[Dict[str, Any]]]:
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


def curiosity_catalyst_node(state: State) -> State:
    """
    Monitor external sources, analyze student uploads for interests,
    and prepare a personalized briefing. Uses MINIMAX for:
    - interest extraction (upload text -> interest_signals)
    - relevance scoring (papers vs interest_signals)
    - personalized briefing summary
    """
    payload = state.get("event_payload", {})
    student_id = payload.get("student_id", "unknown-student")
    event_type = state.get("event_type", "")

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
            pass  # LLM 失败时不影响后续流程

    # --- 2. 读取 interest_signals 获取监控关键词 ---
    keywords, interest_signals = _interest_keywords_and_signals(payload, student_id)
    if not keywords:
        keywords = ["learning science", "education"]

    # --- 3. 调用 arxiv_monitor（带 LLM 相关性）---
    arxiv_result = monitor_arxiv_domain(
        student_id=student_id,
        interest_keywords=keywords,
        interest_signals=interest_signals,
        use_llm_relevance=bool(interest_signals),
    )

    # --- 4. 调用 github_monitor ---
    github_result = monitor_github_domain(
        student_id=student_id,
        interest_keywords=keywords,
    )

    # --- 5. 合并内容并生成简报 ---
    content_items: List[Dict[str, Any]] = []
    content_items.extend(arxiv_result.get("top_papers", []))
    content_items.extend(github_result.get("top_resources", []))

    curriculum_context = payload.get("curriculum_context", {})

    briefing_result = synthesize_briefing(
        student_id=student_id,
        content_items=content_items,
        curriculum_context=curriculum_context,
    )

    # --- 6. 可选：用 LLM 增强简报摘要（Raw Data -> LLM -> Professional Summary）---
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

    # --- 7. 写 pending_validations（需 Architect 审核）---
    validation_key = state.get("session_id", "global")
    shared_memory.write(
        "pending_validations",
        validation_key,
        {
            "student_id": student_id,
            "briefing": briefing_result,
            "sources": {
                "arxiv": arxiv_result,
                "github": github_result,
            },
        },
    )

    # --- 8. 需要通知时写入 state["notifications"] ---
    should_notify = briefing_result.get("should_notify", bool(content_items))
    notifications = list(state.get("notifications", []))
    if should_notify:
        notifications.append(
            {
                "type": "curiosity_briefing",
                "student_id": student_id,
                "briefing_id": briefing_result.get("briefing_id", ""),
            }
        )

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
