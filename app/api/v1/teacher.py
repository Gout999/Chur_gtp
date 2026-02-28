"""Teacher endpoints."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.auth import require_bearer_token
from app.services.llm_service import generate_lesson_plan_content
from app.services.ppt_generator import generate_ppt_from_lesson_plan, get_slide_count
from memory.shared import shared_memory

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".pptx", ".ppt", ".txt", ".md", ".markdown"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
UPLOAD_DIR = Path("uploads/materials")

router = APIRouter(dependencies=[Depends(require_bearer_token)])


@router.get("/profile")
def get_teacher_profile() -> dict:
    return {"id": "teacher-demo", "role": "teacher"}


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TeacherMaterialUploadResponse(BaseModel):
    material_id: str
    file_name: str
    file_size: int
    content_type: str
    status: Literal["queued"]
    stored_at: str


class TeacherMaterialStatusResponse(BaseModel):
    material_id: str
    status: str
    stored_at: str
    updated_at: Optional[str] = None


class TeacherBoundaryUpdateRequest(BaseModel):
    strictness: Literal["strict", "moderate", "permissive"]
    reason: Optional[str] = None


class TeacherBoundaryUpdateResponse(BaseModel):
    material_id: str
    strictness: Literal["strict", "moderate", "permissive"]
    updated_at: str


class ImportanceMarkItem(BaseModel):
    concept: str = Field(min_length=1)
    level: Literal["low", "medium", "high"]
    note: Optional[str] = None


class TeacherImportanceRequest(BaseModel):
    marks: List[ImportanceMarkItem] = Field(min_length=1)


class TeacherImportanceResponse(BaseModel):
    material_id: str
    marks_saved: int
    updated_at: str


class GraphNode(BaseModel):
    id: str
    label: str
    category: str = "concept"


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str = "related_to"


class TeacherKnowledgeGraphResponse(BaseModel):
    material_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class TeacherMaterialDeleteResponse(BaseModel):
    material_id: str
    deleted: bool
    deleted_at: str


class TeacherClassOverviewResponse(BaseModel):
    class_id: str
    total_students: int
    total_interactions: int
    pending_escalations: int
    at_risk_students: int


class TeacherStudentSummary(BaseModel):
    student_id: str
    class_id: Optional[str] = None
    mastery_score: float = 0.0
    latest_topic: Optional[str] = None


class TeacherClassStudentsResponse(BaseModel):
    class_id: str
    students: List[TeacherStudentSummary]


class TeacherStudentDetailResponse(BaseModel):
    student_id: str
    class_id: Optional[str] = None
    profile: Dict[str, str]
    mastery_score: float = 0.0
    latest_topic: Optional[str] = None


class TeacherStudentCognitionResponse(BaseModel):
    student_id: str
    mastery_score: float
    misconceptions: List[str]
    confidence: float


class TeacherAgentLogItem(BaseModel):
    timestamp: Optional[str] = None
    agent: str
    decision: str
    tool: Optional[str] = None


class TeacherAgentLogsResponse(BaseModel):
    student_id: str
    logs: List[TeacherAgentLogItem]


class TeacherInteractionItem(BaseModel):
    timestamp: Optional[str] = None
    topic: Optional[str] = None
    role: Optional[str] = None
    content: Optional[str] = None


class TeacherInteractionsResponse(BaseModel):
    student_id: str
    total: int
    items: List[TeacherInteractionItem]


class TeacherEscalationItem(BaseModel):
    escalation_id: str
    student_id: Optional[str] = None
    class_id: Optional[str] = None
    reason: Optional[str] = None
    severity: Optional[str] = None
    created_at: Optional[str] = None


class TeacherEscalationListResponse(BaseModel):
    escalations: List[TeacherEscalationItem]


class TeacherEscalationDetailResponse(BaseModel):
    escalation_id: str
    detail: Dict[str, Optional[str]]


class TeacherEscalationResponseRequest(BaseModel):
    teacher_id: str = Field(min_length=1)
    action: Literal["acknowledge", "guide", "intervene", "resolve"]
    message: Optional[str] = None


class TeacherEscalationResponseResult(BaseModel):
    escalation_id: str
    resolved: bool
    responded_at: str


class TeacherSendMessageRequest(BaseModel):
    teacher_id: str = Field(min_length=1)
    student_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    channel: Literal["in_app", "email", "push"] = "in_app"


class TeacherSendMessageResponse(BaseModel):
    message_id: str
    delivery_state: Literal["queued"]
    created_at: str


class TeacherConversationItem(BaseModel):
    message_id: str
    teacher_id: str
    student_id: str
    content: str
    channel: str
    created_at: str


class TeacherConversationResponse(BaseModel):
    student_id: str
    total: int
    items: List[TeacherConversationItem]


class CompanionPauseRequest(BaseModel):
    paused: bool
    reason: Optional[str] = None
    scope: Literal["global", "class"] = "global"
    class_id: Optional[str] = None


class CompanionPauseResponse(BaseModel):
    paused: bool
    scope: Literal["global", "class"]
    updated_at: str


class TeacherConfigModel(BaseModel):
    companion_strictness: Literal["gentle", "moderate", "strict"] = "moderate"
    companion_max_attempts: int = Field(default=5, ge=1, le=20)
    companion_emotion_detection: bool = True
    catalyst_enabled: bool = True
    catalyst_push_frequency: Literal["daily", "weekly"] = "daily"
    catalyst_max_daily_push: int = Field(default=3, ge=0, le=20)
    catalyst_content_review: bool = True
    architect_default_boundary: Literal["strict", "moderate", "permissive"] = "moderate"
    architect_auto_expand: bool = False
    notification_escalation_threshold: Literal["high", "medium", "any"] = "medium"
    notification_delivery: List[Literal["in_app", "email", "push"]] = Field(default_factory=lambda: ["in_app"])


class TeacherConfigResponse(BaseModel):
    teacher_id: str
    config: TeacherConfigModel


class TeacherConfigUpdateRequest(BaseModel):
    teacher_id: str = Field(min_length=1)
    config: TeacherConfigModel


class TeacherClassConfigUpdateRequest(BaseModel):
    teacher_id: str = Field(min_length=1)
    config: TeacherConfigModel


class TeacherNotificationConfigRequest(BaseModel):
    teacher_id: str = Field(min_length=1)
    notification_escalation_threshold: Literal["high", "medium", "any"]
    notification_delivery: List[Literal["in_app", "email", "push"]] = Field(min_length=1)


class LessonPlanGenerateRequest(BaseModel):
    teacher_id: str = Field(min_length=1)
    class_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    material_ids: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)


class LessonPlanSection(BaseModel):
    title: str
    duration_minutes: int
    activity: str
    teaching_method: str = ""
    expected_outcome: str = ""


class LessonPlanResponse(BaseModel):
    plan_id: str
    teacher_id: str
    class_id: str
    title: str
    objective: str
    material_ids: List[str]
    topics: List[str]
    sections: List[LessonPlanSection]
    version: int
    updated_at: str


class LessonPlanUpdateRequest(BaseModel):
    teacher_id: str = Field(min_length=1)
    title: Optional[str] = None
    objective: Optional[str] = None
    topics: Optional[List[str]] = None
    sections: Optional[List[LessonPlanSection]] = None


class LessonPlanDeleteResponse(BaseModel):
    plan_id: str
    deleted: bool
    deleted_at: str


class LessonPptGenerateRequest(BaseModel):
    teacher_id: str = Field(min_length=1)
    template: str = Field(default="lesson_default")


class LessonPptGenerateResponse(BaseModel):
    ppt_id: str
    status: str
    poll_url: str


class PptStatusResponse(BaseModel):
    ppt_id: str
    status: str
    progress: int


class PptDownloadResponse(BaseModel):
    ppt_id: str
    download_url: str


class PptPreviewResponse(BaseModel):
    ppt_id: str
    preview_images: List[str]


class LessonTemplateItem(BaseModel):
    template_id: str
    label: str
    description: str


class LessonTemplatesResponse(BaseModel):
    templates: List[LessonTemplateItem]


def _get_active_material_or_404(material_id: str) -> Dict[str, str]:
    entry = shared_memory.read("teacher_uploads", material_id)
    if not entry:
        raise HTTPException(status_code=404, detail="material_not_found")
    value = entry.get("value", {})
    if value.get("deleted"):
        raise HTTPException(status_code=404, detail="material_not_found")
    return value


def _infer_content_type(ext: str) -> str:
    return {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".ppt": "application/vnd.ms-powerpoint",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".markdown": "text/markdown",
    }.get(ext, "application/octet-stream")


@router.post("/materials/upload", response_model=TeacherMaterialUploadResponse)
async def upload_teacher_material(
    file: UploadFile = File(..., description="教材文件 (PDF/DOCX/PPT/TXT/MD)"),
    teacher_id: str = Form(..., min_length=1),
    class_id: Optional[str] = Form(None),
    source_type: str = Form("teacher_upload"),
    tags: str = Form(""),
    grade_level: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    boundary_strictness: str = Form("moderate"),
    teacher_notes: Optional[str] = Form(None),
) -> TeacherMaterialUploadResponse:
    file_name = file.filename or "unknown"
    ext = Path(file_name).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"unsupported_file_type: {ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(status_code=400, detail="file_empty")
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"file_too_large: {file_size} bytes exceeds {MAX_FILE_SIZE_BYTES} limit",
        )

    material_id = f"mat_{uuid4().hex[:12]}"
    material_dir = UPLOAD_DIR / material_id
    material_dir.mkdir(parents=True, exist_ok=True)
    saved_path = material_dir / file_name
    saved_path.write_bytes(content)

    content_type = file.content_type or _infer_content_type(ext)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    now = _utc_iso()

    shared_memory.write(
        "teacher_uploads",
        material_id,
        {
            "material_id": material_id,
            "teacher_id": teacher_id,
            "class_id": class_id,
            "file_name": file_name,
            "file_path": str(saved_path),
            "file_size": file_size,
            "source_type": source_type,
            "content_type": content_type,
            "tags": tag_list,
            "grade_level": grade_level,
            "subject": subject,
            "boundary_strictness": boundary_strictness,
            "teacher_notes": teacher_notes,
            "status": "queued",
            "created_at": now,
            "observed_by_architect": False,
        },
    )

    return TeacherMaterialUploadResponse(
        material_id=material_id,
        file_name=file_name,
        file_size=file_size,
        content_type=content_type,
        status="queued",
        stored_at=now,
    )


@router.get("/materials/{material_id}/status", response_model=TeacherMaterialStatusResponse)
def get_teacher_material_status(material_id: str) -> TeacherMaterialStatusResponse:
    entry = shared_memory.read("teacher_uploads", material_id)
    if not entry or entry.get("value", {}).get("deleted"):
        raise HTTPException(status_code=404, detail="material_not_found")
    value = entry["value"]
    return TeacherMaterialStatusResponse(
        material_id=material_id,
        status=value.get("status", "queued"),
        stored_at=value.get("created_at", entry.get("created_at", "")),
        updated_at=entry.get("updated_at"),
    )


@router.put("/materials/{material_id}/boundary", response_model=TeacherBoundaryUpdateResponse)
def update_teacher_material_boundary(
    material_id: str,
    payload: TeacherBoundaryUpdateRequest,
) -> TeacherBoundaryUpdateResponse:
    material = _get_active_material_or_404(material_id)
    now = _utc_iso()

    existing = shared_memory.read("teacher_boundary_adjustments", material_id)
    history = [] if not existing else existing.get("value", {}).get("history", [])
    history.append(
        {
            "strictness": payload.strictness,
            "reason": payload.reason,
            "updated_at": now,
        }
    )

    shared_memory.write(
        "teacher_boundary_adjustments",
        material_id,
        {
            "material_id": material_id,
            "teacher_id": material.get("teacher_id"),
            "strictness": payload.strictness,
            "reason": payload.reason,
            "history": history,
            "updated_at": now,
        },
    )
    return TeacherBoundaryUpdateResponse(
        material_id=material_id,
        strictness=payload.strictness,
        updated_at=now,
    )


@router.put("/materials/{material_id}/importance", response_model=TeacherImportanceResponse)
def update_teacher_material_importance(
    material_id: str,
    payload: TeacherImportanceRequest,
) -> TeacherImportanceResponse:
    material = _get_active_material_or_404(material_id)
    now = _utc_iso()

    marks = [mark.model_dump() for mark in payload.marks]
    shared_memory.write(
        "teacher_importance_marks",
        material_id,
        {
            "material_id": material_id,
            "teacher_id": material.get("teacher_id"),
            "marks": marks,
            "updated_at": now,
        },
    )
    return TeacherImportanceResponse(
        material_id=material_id,
        marks_saved=len(marks),
        updated_at=now,
    )


@router.get("/materials/{material_id}/knowledge-graph", response_model=TeacherKnowledgeGraphResponse)
def get_teacher_material_knowledge_graph(material_id: str) -> TeacherKnowledgeGraphResponse:
    material = _get_active_material_or_404(material_id)
    authority_entry = shared_memory.read("teacher_authority_graph", material_id)
    authority_value = authority_entry.get("value", {}) if authority_entry else {}
    latest_material = authority_value.get("latest_material", {})
    latest_boundary = authority_value.get("latest_boundary", {})

    root_label = latest_material.get("knowledge_nodes", [{}])[0].get(
        "title",
        material.get("file_name", "material"),
    )
    strictness = latest_boundary.get("scope_level", "moderate")

    nodes = [
        GraphNode(id=f"{material_id}:root", label=root_label, category="material"),
        GraphNode(id=f"{material_id}:boundary", label=f"boundary:{strictness}", category="boundary"),
    ]
    edges = [
        GraphEdge(
            source=f"{material_id}:root",
            target=f"{material_id}:boundary",
            relation="constrained_by",
        )
    ]
    return TeacherKnowledgeGraphResponse(material_id=material_id, nodes=nodes, edges=edges)


@router.delete("/materials/{material_id}", response_model=TeacherMaterialDeleteResponse)
def delete_teacher_material(material_id: str) -> TeacherMaterialDeleteResponse:
    entry = shared_memory.read("teacher_uploads", material_id)
    if not entry:
        raise HTTPException(status_code=404, detail="material_not_found")

    value = entry.get("value", {})
    if value.get("deleted"):
        return TeacherMaterialDeleteResponse(
            material_id=material_id,
            deleted=True,
            deleted_at=value.get("deleted_at", _utc_iso()),
        )

    now = _utc_iso()
    shared_memory.update(
        "teacher_uploads",
        material_id,
        {
            "deleted": True,
            "deleted_at": now,
            "status": "deleted",
        },
    )

    if shared_memory.read("teacher_boundary_adjustments", material_id):
        shared_memory.update(
            "teacher_boundary_adjustments",
            material_id,
            {"archived": True, "archived_at": now},
        )
    if shared_memory.read("teacher_importance_marks", material_id):
        shared_memory.update(
            "teacher_importance_marks",
            material_id,
            {"archived": True, "archived_at": now},
        )

    shared_memory.write(
        "teacher_audit_logs",
        f"delete:{material_id}",
        {
            "action": "delete_material",
            "material_id": material_id,
            "deleted_at": now,
        },
    )
    return TeacherMaterialDeleteResponse(material_id=material_id, deleted=True, deleted_at=now)


@router.get("/classes/{class_id}/overview", response_model=TeacherClassOverviewResponse)
def get_teacher_class_overview(class_id: str) -> TeacherClassOverviewResponse:
    episodes = shared_memory.read_all("interaction_episodes", filter_dict={"class_id": class_id}, limit=1000)
    escalations = shared_memory.read_all("pending_escalations", filter_dict={"class_id": class_id}, limit=1000)
    cognition_entries = shared_memory.read_all("student_cognitive_models", filter_dict={"class_id": class_id}, limit=1000)

    student_ids = {entry.get("value", {}).get("student_id") for entry in cognition_entries}
    student_ids.update({entry.get("value", {}).get("student_id") for entry in episodes})
    student_ids.discard(None)

    at_risk_students = 0
    for entry in cognition_entries:
        mastery = float(entry.get("value", {}).get("mastery_score", 0.0))
        if mastery < 0.4:
            at_risk_students += 1

    return TeacherClassOverviewResponse(
        class_id=class_id,
        total_students=len(student_ids),
        total_interactions=len(episodes),
        pending_escalations=len(escalations),
        at_risk_students=at_risk_students,
    )


@router.get("/classes/{class_id}/students", response_model=TeacherClassStudentsResponse)
def get_teacher_class_students(class_id: str) -> TeacherClassStudentsResponse:
    entries = shared_memory.read_all("student_cognitive_models", filter_dict={"class_id": class_id}, limit=1000)
    students = [
        TeacherStudentSummary(
            student_id=entry.get("value", {}).get("student_id", entry.get("key", "unknown-student")),
            class_id=entry.get("value", {}).get("class_id"),
            mastery_score=float(entry.get("value", {}).get("mastery_score", 0.0)),
            latest_topic=entry.get("value", {}).get("latest_topic"),
        )
        for entry in entries
    ]
    students.sort(key=lambda s: s.student_id)
    return TeacherClassStudentsResponse(class_id=class_id, students=students)


@router.get("/students/{student_id}", response_model=TeacherStudentDetailResponse)
def get_teacher_student_detail(student_id: str) -> TeacherStudentDetailResponse:
    entry = shared_memory.read("student_cognitive_models", student_id)
    value = entry.get("value", {}) if entry else {}
    return TeacherStudentDetailResponse(
        student_id=student_id,
        class_id=value.get("class_id"),
        profile={
            "display_name": value.get("display_name", student_id),
            "status": value.get("status", "active"),
        },
        mastery_score=float(value.get("mastery_score", 0.0)),
        latest_topic=value.get("latest_topic"),
    )


@router.get("/students/{student_id}/cognition", response_model=TeacherStudentCognitionResponse)
def get_teacher_student_cognition(student_id: str) -> TeacherStudentCognitionResponse:
    entry = shared_memory.read("student_cognitive_models", student_id)
    value = entry.get("value", {}) if entry else {}
    return TeacherStudentCognitionResponse(
        student_id=student_id,
        mastery_score=float(value.get("mastery_score", 0.0)),
        misconceptions=list(value.get("misconceptions", [])),
        confidence=float(value.get("confidence", 0.0)),
    )


@router.get("/students/{student_id}/agent-logs", response_model=TeacherAgentLogsResponse)
def get_teacher_student_agent_logs(student_id: str) -> TeacherAgentLogsResponse:
    episodes = shared_memory.read_all("interaction_episodes", filter_dict={"student_id": student_id}, limit=1000)
    logs: List[TeacherAgentLogItem] = []
    for episode in episodes:
        value = episode.get("value", {})
        logs.append(
            TeacherAgentLogItem(
                timestamp=value.get("timestamp"),
                agent=value.get("agent", "unknown"),
                decision=value.get("decision", ""),
                tool=value.get("tool"),
            )
        )
    logs.sort(key=lambda item: item.timestamp or "")
    return TeacherAgentLogsResponse(student_id=student_id, logs=logs)


@router.get("/students/{student_id}/interactions", response_model=TeacherInteractionsResponse)
def get_teacher_student_interactions(
    student_id: str,
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    topic: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> TeacherInteractionsResponse:
    episodes = shared_memory.read_all("interaction_episodes", filter_dict={"student_id": student_id}, limit=2000)

    filtered = []
    for episode in episodes:
        value = episode.get("value", {})
        ts = value.get("timestamp")
        if start_date and ts and ts < start_date:
            continue
        if end_date and ts and ts > end_date:
            continue
        if topic and value.get("topic") != topic:
            continue
        filtered.append(
            TeacherInteractionItem(
                timestamp=ts,
                topic=value.get("topic"),
                role=value.get("role"),
                content=value.get("content"),
            )
        )

    filtered.sort(key=lambda item: item.timestamp or "")
    sliced = filtered[:limit]
    return TeacherInteractionsResponse(student_id=student_id, total=len(filtered), items=sliced)


@router.get("/escalations", response_model=TeacherEscalationListResponse)
def get_teacher_escalations() -> TeacherEscalationListResponse:
    entries = shared_memory.read_all("pending_escalations", limit=1000)
    escalations = []
    for entry in entries:
        value = entry.get("value", {})
        if value.get("resolved"):
            continue
        escalations.append(
            TeacherEscalationItem(
                escalation_id=entry.get("key", ""),
                student_id=value.get("student_id"),
                class_id=value.get("class_id"),
                reason=value.get("reason"),
                severity=value.get("severity"),
                created_at=value.get("created_at"),
            )
        )
    escalations.sort(key=lambda item: item.created_at or "")
    return TeacherEscalationListResponse(escalations=escalations)


@router.get("/escalations/{escalation_id}", response_model=TeacherEscalationDetailResponse)
def get_teacher_escalation_detail(escalation_id: str) -> TeacherEscalationDetailResponse:
    entry = shared_memory.read("pending_escalations", escalation_id)
    if not entry:
        raise HTTPException(status_code=404, detail="escalation_not_found")
    value = entry.get("value", {})
    detail = {
        "student_id": value.get("student_id"),
        "class_id": value.get("class_id"),
        "reason": value.get("reason"),
        "severity": value.get("severity"),
        "created_at": value.get("created_at"),
        "resolved": str(bool(value.get("resolved"))),
    }
    return TeacherEscalationDetailResponse(escalation_id=escalation_id, detail=detail)


@router.post(
    "/escalations/{escalation_id}/respond",
    response_model=TeacherEscalationResponseResult,
)
def respond_teacher_escalation(
    escalation_id: str,
    payload: TeacherEscalationResponseRequest,
) -> TeacherEscalationResponseResult:
    entry = shared_memory.read("pending_escalations", escalation_id)
    if not entry:
        raise HTTPException(status_code=404, detail="escalation_not_found")

    now = _utc_iso()
    shared_memory.write(
        "teacher_escalation_responses",
        escalation_id,
        {
            "escalation_id": escalation_id,
            "teacher_id": payload.teacher_id,
            "action": payload.action,
            "message": payload.message,
            "responded_at": now,
        },
    )
    shared_memory.update(
        "pending_escalations",
        escalation_id,
        {
            "resolved": True,
            "resolved_at": now,
            "resolver_teacher_id": payload.teacher_id,
        },
    )
    return TeacherEscalationResponseResult(
        escalation_id=escalation_id,
        resolved=True,
        responded_at=now,
    )


@router.post("/messages/send", response_model=TeacherSendMessageResponse)
def teacher_send_message(payload: TeacherSendMessageRequest) -> TeacherSendMessageResponse:
    message_id = f"msg_{uuid4().hex[:12]}"
    now = _utc_iso()
    shared_memory.write(
        "teacher_student_messages",
        message_id,
        {
            "message_id": message_id,
            "teacher_id": payload.teacher_id,
            "student_id": payload.student_id,
            "content": payload.content,
            "channel": payload.channel,
            "created_at": now,
        },
    )
    return TeacherSendMessageResponse(message_id=message_id, delivery_state="queued", created_at=now)


@router.get("/messages/conversations/{student_id}", response_model=TeacherConversationResponse)
def get_teacher_conversation(student_id: str) -> TeacherConversationResponse:
    entries = shared_memory.read_all("teacher_student_messages", filter_dict={"student_id": student_id}, limit=1000)
    items = [
        TeacherConversationItem(
            message_id=entry.get("value", {}).get("message_id", entry.get("key", "")),
            teacher_id=entry.get("value", {}).get("teacher_id", ""),
            student_id=entry.get("value", {}).get("student_id", ""),
            content=entry.get("value", {}).get("content", ""),
            channel=entry.get("value", {}).get("channel", "in_app"),
            created_at=entry.get("value", {}).get("created_at", entry.get("created_at", "")),
        )
        for entry in entries
    ]
    items.sort(key=lambda item: item.created_at)
    return TeacherConversationResponse(student_id=student_id, total=len(items), items=items)


@router.put("/companion/pause", response_model=CompanionPauseResponse)
def update_companion_pause(payload: CompanionPauseRequest) -> CompanionPauseResponse:
    now = _utc_iso()
    key = "global" if payload.scope == "global" else (payload.class_id or "class:unknown")
    shared_memory.write(
        "companion_control",
        key,
        {
            "paused": payload.paused,
            "reason": payload.reason,
            "scope": payload.scope,
            "class_id": payload.class_id,
            "updated_at": now,
        },
    )
    return CompanionPauseResponse(paused=payload.paused, scope=payload.scope, updated_at=now)


def _global_config_key(teacher_id: str) -> str:
    return f"global:{teacher_id}"


def _class_config_key(teacher_id: str, class_id: str) -> str:
    return f"class:{teacher_id}:{class_id}"


def _default_config() -> TeacherConfigModel:
    return TeacherConfigModel()


@router.get("/config", response_model=TeacherConfigResponse)
def get_teacher_config(teacher_id: str = Query(default="teacher-demo")) -> TeacherConfigResponse:
    entry = shared_memory.read("teacher_configurations", _global_config_key(teacher_id))
    if not entry:
        return TeacherConfigResponse(teacher_id=teacher_id, config=_default_config())
    return TeacherConfigResponse(
        teacher_id=teacher_id,
        config=TeacherConfigModel.model_validate(entry.get("value", {}).get("config", {})),
    )


@router.put("/config", response_model=TeacherConfigResponse)
def update_teacher_config(payload: TeacherConfigUpdateRequest) -> TeacherConfigResponse:
    now = _utc_iso()
    shared_memory.write(
        "teacher_configurations",
        _global_config_key(payload.teacher_id),
        {
            "teacher_id": payload.teacher_id,
            "scope": "global",
            "config": payload.config.model_dump(),
            "updated_at": now,
        },
    )
    return TeacherConfigResponse(teacher_id=payload.teacher_id, config=payload.config)


@router.get("/classes/{class_id}/config", response_model=TeacherConfigResponse)
def get_teacher_class_config(
    class_id: str,
    teacher_id: str = Query(default="teacher-demo"),
) -> TeacherConfigResponse:
    global_entry = shared_memory.read("teacher_configurations", _global_config_key(teacher_id))
    class_entry = shared_memory.read("teacher_configurations", _class_config_key(teacher_id, class_id))

    base = _default_config().model_dump()
    if global_entry:
        base.update(global_entry.get("value", {}).get("config", {}))
    if class_entry:
        base.update(class_entry.get("value", {}).get("config", {}))

    return TeacherConfigResponse(
        teacher_id=teacher_id,
        config=TeacherConfigModel.model_validate(base),
    )


@router.put("/classes/{class_id}/config", response_model=TeacherConfigResponse)
def update_teacher_class_config(
    class_id: str,
    payload: TeacherClassConfigUpdateRequest,
) -> TeacherConfigResponse:
    now = _utc_iso()
    shared_memory.write(
        "teacher_configurations",
        _class_config_key(payload.teacher_id, class_id),
        {
            "teacher_id": payload.teacher_id,
            "scope": "class",
            "class_id": class_id,
            "config": payload.config.model_dump(),
            "updated_at": now,
        },
    )
    return TeacherConfigResponse(teacher_id=payload.teacher_id, config=payload.config)


@router.put("/config/notifications", response_model=TeacherConfigResponse)
def update_teacher_notification_config(
    payload: TeacherNotificationConfigRequest,
) -> TeacherConfigResponse:
    existing = shared_memory.read("teacher_configurations", _global_config_key(payload.teacher_id))
    merged = _default_config().model_dump()
    if existing:
        merged.update(existing.get("value", {}).get("config", {}))

    merged["notification_escalation_threshold"] = payload.notification_escalation_threshold
    merged["notification_delivery"] = payload.notification_delivery

    config = TeacherConfigModel.model_validate(merged)
    shared_memory.write(
        "teacher_configurations",
        _global_config_key(payload.teacher_id),
        {
            "teacher_id": payload.teacher_id,
            "scope": "global",
            "config": config.model_dump(),
            "updated_at": _utc_iso(),
        },
    )
    return TeacherConfigResponse(teacher_id=payload.teacher_id, config=config)


def _get_active_lesson_plan_or_404(plan_id: str) -> Dict[str, object]:
    entry = shared_memory.read("teacher_lesson_plans", plan_id)
    if not entry:
        raise HTTPException(status_code=404, detail="lesson_plan_not_found")
    value = entry.get("value", {})
    if value.get("deleted"):
        raise HTTPException(status_code=404, detail="lesson_plan_not_found")
    return value


def _build_material_context(material_ids: List[str]) -> str:
    """Read uploaded material metadata + knowledge graph from shared memory."""
    if not material_ids:
        return ""

    parts: List[str] = []
    for mid in material_ids:
        upload = shared_memory.read("teacher_uploads", mid)
        if not upload:
            continue
        val = upload.get("value", {})
        info = f"教材: {val.get('file_name', mid)}"
        if val.get("tags"):
            info += f"  标签: {', '.join(val['tags'])}"
        if val.get("subject"):
            info += f"  科目: {val['subject']}"
        if val.get("grade_level"):
            info += f"  年级: {val['grade_level']}"
        if val.get("boundary_strictness"):
            info += f"  知识边界: {val['boundary_strictness']}"
        if val.get("teacher_notes"):
            info += f"\n  教师备注: {val['teacher_notes']}"
        parts.append(info)

        authority = shared_memory.read("teacher_authority_graph", mid)
        if authority:
            auth_val = authority.get("value", {})
            material_data = auth_val.get("latest_material", {})
            nodes = material_data.get("knowledge_nodes", [])
            if nodes:
                node_titles = [n.get("title", "") for n in nodes if n.get("title")]
                parts.append(f"  知识节点: {', '.join(node_titles)}")
            boundary_data = auth_val.get("latest_boundary", {})
            if boundary_data.get("scope_level"):
                parts.append(f"  知识范围: {boundary_data['scope_level']}")

        importance = shared_memory.read("teacher_importance_marks", mid)
        if importance:
            marks = importance.get("value", {}).get("marks", [])
            if marks:
                high_marks = [m["concept"] for m in marks if m.get("level") == "high"]
                if high_marks:
                    parts.append(f"  重点概念: {', '.join(high_marks)}")

    return "\n".join(parts)


@router.post("/lesson-plans/generate", response_model=LessonPlanResponse)
def generate_lesson_plan(payload: LessonPlanGenerateRequest) -> LessonPlanResponse:
    plan_id = f"plan_{uuid4().hex[:12]}"
    now = _utc_iso()

    material_context = _build_material_context(payload.material_ids)

    sections_data = generate_lesson_plan_content(
        title=payload.title,
        objective=payload.objective,
        material_ids=payload.material_ids,
        topics=payload.topics,
        material_context=material_context,
    )

    # 转换为Pydantic模型
    sections = [
        LessonPlanSection(
            title=s.get("title", ""),
            duration_minutes=s.get("duration_minutes", 10),
            activity=s.get("activity", ""),
            teaching_method=s.get("teaching_method", ""),
            expected_outcome=s.get("expected_outcome", "")
        )
        for s in sections_data
    ]

    topics = payload.topics or [s.title for s in sections]

    shared_memory.write(
        "teacher_lesson_plans",
        plan_id,
        {
            "plan_id": plan_id,
            "teacher_id": payload.teacher_id,
            "class_id": payload.class_id,
            "title": payload.title,
            "objective": payload.objective,
            "material_ids": payload.material_ids,
            "topics": topics,
            "sections": [section.model_dump() for section in sections],
            "version": 1,
            "updated_at": now,
            "deleted": False,
            "ai_generated": True,
            "ai_model": "MiniMax-M2.5",
            "generated_at": now,
            "edited_by_teacher": False,
        },
    )
    return LessonPlanResponse(
        plan_id=plan_id,
        teacher_id=payload.teacher_id,
        class_id=payload.class_id,
        title=payload.title,
        objective=payload.objective,
        material_ids=payload.material_ids,
        topics=topics,
        sections=sections,
        version=1,
        updated_at=now,
    )


@router.get("/lesson-plans/{plan_id}", response_model=LessonPlanResponse)
def get_lesson_plan(plan_id: str) -> LessonPlanResponse:
    plan = _get_active_lesson_plan_or_404(plan_id)
    return LessonPlanResponse(
        plan_id=plan["plan_id"],
        teacher_id=plan["teacher_id"],
        class_id=plan["class_id"],
        title=plan["title"],
        objective=plan["objective"],
        material_ids=list(plan.get("material_ids", [])),
        topics=list(plan.get("topics", [])),
        sections=[LessonPlanSection.model_validate(item) for item in plan.get("sections", [])],
        version=int(plan.get("version", 1)),
        updated_at=str(plan.get("updated_at")),
    )


@router.put("/lesson-plans/{plan_id}", response_model=LessonPlanResponse)
def update_lesson_plan(plan_id: str, payload: LessonPlanUpdateRequest) -> LessonPlanResponse:
    plan = _get_active_lesson_plan_or_404(plan_id)
    now = _utc_iso()
    next_version = int(plan.get("version", 1)) + 1

    merged = {
        "title": payload.title or plan.get("title", ""),
        "objective": payload.objective or plan.get("objective", ""),
        "topics": payload.topics if payload.topics is not None else plan.get("topics", []),
        "sections": (
            [section.model_dump() for section in payload.sections]
            if payload.sections is not None
            else plan.get("sections", [])
        ),
    }

    shared_memory.update(
        "teacher_lesson_plans",
        plan_id,
        {
            **merged,
            "version": next_version,
            "updated_at": now,
            "edited_by": payload.teacher_id,
        },
    )

    updated = _get_active_lesson_plan_or_404(plan_id)
    return LessonPlanResponse(
        plan_id=updated["plan_id"],
        teacher_id=updated["teacher_id"],
        class_id=updated["class_id"],
        title=updated["title"],
        objective=updated["objective"],
        material_ids=list(updated.get("material_ids", [])),
        topics=list(updated.get("topics", [])),
        sections=[LessonPlanSection.model_validate(item) for item in updated.get("sections", [])],
        version=int(updated.get("version", next_version)),
        updated_at=str(updated.get("updated_at", now)),
    )


@router.delete("/lesson-plans/{plan_id}", response_model=LessonPlanDeleteResponse)
def delete_lesson_plan(plan_id: str) -> LessonPlanDeleteResponse:
    plan = shared_memory.read("teacher_lesson_plans", plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="lesson_plan_not_found")

    value = plan.get("value", {})
    if value.get("deleted"):
        return LessonPlanDeleteResponse(plan_id=plan_id, deleted=True, deleted_at=value.get("deleted_at", _utc_iso()))

    now = _utc_iso()
    shared_memory.update(
        "teacher_lesson_plans",
        plan_id,
        {"deleted": True, "deleted_at": now, "updated_at": now},
    )
    return LessonPlanDeleteResponse(plan_id=plan_id, deleted=True, deleted_at=now)


@router.post("/lesson-plans/{plan_id}/ppt", response_model=LessonPptGenerateResponse)
def generate_lesson_ppt(plan_id: str, payload: LessonPptGenerateRequest) -> LessonPptGenerateResponse:
    plan = _get_active_lesson_plan_or_404(plan_id)
    ppt_id = f"ppt_{uuid4().hex[:12]}"
    now = _utc_iso()

    # 生成真实PPT文件
    try:
        file_path = generate_ppt_from_lesson_plan(
            plan_data=plan,
            template=payload.template,
            ppt_id=ppt_id
        )
        status = "completed"
        progress = 100
        slide_count = get_slide_count(file_path)
    except Exception as e:
        # 生成失败
        file_path = ""
        status = "failed"
        progress = 0
        slide_count = 0
        print(f"PPT generation failed: {e}")

    # 生成预览图路径
    preview_images = [
        f"/output/previews/{ppt_id}/slide-{i}.png"
        for i in range(1, min(slide_count + 1, 6))
    ] if slide_count > 0 else []

    shared_memory.write(
        "generated_ppts",
        ppt_id,
        {
            "ppt_id": ppt_id,
            "plan_id": plan_id,
            "teacher_id": payload.teacher_id,
            "template": payload.template,
            "status": status,
            "progress": progress,
            "file_path": file_path,
            "slide_count": slide_count,
            "download_url": f"/api/v1/teacher/ppt/{ppt_id}/download",
            "preview_images": preview_images,
            "created_at": now,
            "updated_at": now,
            "title": plan.get("title"),
        },
    )
    if status == "failed":
        raise HTTPException(status_code=500, detail="ppt_generation_failed")

    return LessonPptGenerateResponse(
        ppt_id=ppt_id,
        status=status,
        poll_url=f"/api/v1/teacher/ppt/{ppt_id}/status",
    )


@router.get("/ppt/{ppt_id}/status", response_model=PptStatusResponse)
def get_ppt_status(ppt_id: str) -> PptStatusResponse:
    entry = shared_memory.read("generated_ppts", ppt_id)
    if not entry:
        raise HTTPException(status_code=404, detail="ppt_not_found")
    value = entry.get("value", {})
    return PptStatusResponse(
        ppt_id=ppt_id,
        status=value.get("status", "pending"),
        progress=int(value.get("progress", 0)),
    )


@router.get("/ppt/{ppt_id}/download")
def download_ppt(ppt_id: str):
    """Download generated PPT file."""
    entry = shared_memory.read("generated_ppts", ppt_id)
    if not entry:
        raise HTTPException(status_code=404, detail="ppt_not_found")

    value = entry.get("value", {})
    if value.get("status") != "completed":
        raise HTTPException(status_code=409, detail="ppt_not_ready")

    file_path = value.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="ppt_file_not_found")

    plan_title = value.get("title", "lesson_plan")
    safe_title = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in plan_title)

    return FileResponse(
        path=file_path,
        filename=f"{safe_title}_{ppt_id}.pptx",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )


@router.get("/ppt/{ppt_id}/preview", response_model=PptPreviewResponse)
def get_ppt_preview(ppt_id: str) -> PptPreviewResponse:
    entry = shared_memory.read("generated_ppts", ppt_id)
    if not entry:
        raise HTTPException(status_code=404, detail="ppt_not_found")
    value = entry.get("value", {})
    return PptPreviewResponse(
        ppt_id=ppt_id,
        preview_images=list(value.get("preview_images", [])),
    )


@router.get("/lesson-templates", response_model=LessonTemplatesResponse)
def list_lesson_templates() -> LessonTemplatesResponse:
    return LessonTemplatesResponse(
        templates=[
            LessonTemplateItem(
                template_id="lesson_default",
                label="Default Lesson",
                description="Balanced structure for most classes.",
            ),
            LessonTemplateItem(
                template_id="lesson_minimal",
                label="Minimal",
                description="Compact slide deck for short sessions.",
            ),
            LessonTemplateItem(
                template_id="lesson_colorful",
                label="Colorful",
                description="Visual-heavy template for engagement.",
            ),
        ]
    )
