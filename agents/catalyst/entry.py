"""
图外定时/事件驱动入口：单次执行「新内容检测 → 监控 → 简报 → 通知」。

供定时任务或 HTTP/Webhook 调用，不经过 LangGraph 图，避免 Catalyst 自循环 101 次。
工作项 5：主动推送/定时入口。
工作项 7：check_pending_validations 入口，读取 Architect 审核结果并决定推送。
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agents.catalyst.node import _process_validated_entries, curiosity_catalyst_node
from memory.shared import shared_memory

LOG = logging.getLogger("eduguide.catalyst.entry")


def run_new_content_check(
    student_id: str,
    *,
    interest_keywords: Optional[List[str]] = None,
    curriculum_context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    图外单次执行：轮询/事件触发后调用监控工具 → 高相关内容经 synthesize_briefing
    → 通知加入 state["notifications"]。不经过 graph，只跑一次 Catalyst 节点。

    Args:
        student_id: 目标学生 ID。
        interest_keywords: 兴趣关键词；若为 None，节点内会从 shared_memory interest_signals 读取。
        curriculum_context: 可选课程上下文，供简报生成。
        session_id: 可选会话 ID，用于 pending_validations 等。

    Returns:
        执行后的 state 子集：含 notifications、response_to_student、tools_to_call 等，
        调用方可据此推送通知或写入等价出口。
    """
    payload: Dict[str, Any] = {"student_id": student_id}
    if interest_keywords is not None:
        payload["interest_keywords"] = interest_keywords
    if curriculum_context is not None:
        payload["curriculum_context"] = curriculum_context

    state: Dict[str, Any] = {
        "event_type": "new_content_detected",
        "event_payload": payload,
        "working_memory": {},
        "session_id": session_id or f"push-{student_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "loop_count": 0,
        "notifications": [],
    }

    out = curiosity_catalyst_node(state)

    return {
        "notifications": out.get("notifications", []),
        "response_to_student": out.get("response_to_student", ""),
        "tools_to_call": out.get("tools_to_call", []),
        "current_agent": out.get("current_agent", "curiosity_catalyst"),
        "session_id": out.get("session_id"),
    }


def check_pending_validations(student_id: str) -> Dict[str, Any]:
    """
    图外独立入口：仅检查 Architect 已审核的 pending_validations，不执行监控。

    供定时任务周期调用：
    1. 读取 pending_validations 中该学生的所有条目
    2. 对 Architect 批准的条目生成推送通知
    3. 对 Architect 拒绝的条目做确认标记
    4. 返回新增通知列表，调用方据此决定是否推送给学生

    Args:
        student_id: 目标学生 ID。

    Returns:
        notifications: Architect 批准后新生成的通知列表。
        pending_count: 仍在等待 Architect 审核的条目数。
        rejected_count: 本次确认的被拒绝条目数。
    """
    notifications: List[Dict[str, Any]] = []
    notifications = _process_validated_entries(student_id, notifications)

    entries = shared_memory.read_all("pending_validations")
    pending_count = 0
    rejected_count = 0
    for entry in entries:
        val = entry.get("value", {})
        if val.get("student_id") != student_id:
            continue
        status = val.get("status", "pending")
        if status == "pending":
            pending_count += 1
        elif status == "rejected_ack":
            rejected_count += 1

    LOG.info(
        "Validation check for %s: %d notifications, %d pending, %d rejected",
        student_id, len(notifications), pending_count, rejected_count,
    )

    return {
        "notifications": notifications,
        "pending_count": pending_count,
        "rejected_count": rejected_count,
    }
