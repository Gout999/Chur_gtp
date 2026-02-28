"""
主动推送/定时入口：接收「新内容」事件或供定时任务调用的 HTTP 入口。

工作项 5：轮询或接收新内容事件 → 调用监控工具 → 简报 → 通知加入 notifications。
工作项 7：check-validations 入口，读取 Architect 审核结果并决定推送。
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.catalyst import check_pending_validations, run_new_content_check

router = APIRouter()


class TriggerNewContentBody(BaseModel):
    """POST /push/trigger-new-content 请求体。"""

    student_id: str = Field(..., min_length=1, description="目标学生 ID")
    interest_keywords: Optional[List[str]] = Field(None, description="兴趣关键词，不传则从 interest_signals 读取")
    curriculum_context: Optional[Dict[str, Any]] = Field(None, description="课程上下文")


class CheckValidationsBody(BaseModel):
    """POST /push/check-validations 请求体。"""

    student_id: str = Field(..., min_length=1, description="目标学生 ID")


@router.post("/trigger-new-content")
def trigger_new_content_check(body: TriggerNewContentBody) -> Dict[str, Any]:
    """
    事件驱动入口：触发一次新内容检测与简报生成。
    定时任务可周期 POST 此接口（或对多学生循环调用）；Webhook 也可在收到「新内容」事件时调用。
    """
    result = run_new_content_check(
        student_id=body.student_id.strip(),
        interest_keywords=body.interest_keywords,
        curriculum_context=body.curriculum_context,
    )
    return result


@router.post("/check-validations")
def check_validations(body: CheckValidationsBody) -> Dict[str, Any]:
    """
    审核结果检查入口：读取 Architect 已审核的 pending_validations，返回推送通知。

    定时任务可周期 POST 此接口，检查 Architect 是否已审核 Catalyst 提交的内容：
    - approved → 返回通知，调用方据此推送给学生
    - rejected → 确认标记，不推送
    - pending → 仍在等待审核
    """
    result = check_pending_validations(student_id=body.student_id.strip())
    return result
