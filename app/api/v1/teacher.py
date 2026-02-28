"""Teacher endpoints."""
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.auth import require_bearer_token
from memory.shared import shared_memory

router = APIRouter(dependencies=[Depends(require_bearer_token)])


@router.get("/profile")
def get_teacher_profile() -> dict:
    return {"id": "teacher-demo", "role": "teacher"}


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TeacherMaterialUploadRequest(BaseModel):
    teacher_id: str = Field(min_length=1)
    file_name: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    class_id: Optional[str] = None
    source_type: Literal["teacher_upload", "reference", "supplementary"] = "teacher_upload"
    content_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class TeacherMaterialUploadResponse(BaseModel):
    material_id: str
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


@router.post("/materials/upload", response_model=TeacherMaterialUploadResponse)
def upload_teacher_material(payload: TeacherMaterialUploadRequest) -> TeacherMaterialUploadResponse:
    material_id = f"mat_{uuid4().hex[:12]}"
    now = _utc_iso()

    shared_memory.write(
        "teacher_uploads",
        material_id,
        {
            "material_id": material_id,
            "teacher_id": payload.teacher_id,
            "class_id": payload.class_id,
            "file_name": payload.file_name,
            "file_path": payload.file_path,
            "source_type": payload.source_type,
            "content_type": payload.content_type,
            "tags": payload.tags,
            "status": "queued",
            "created_at": now,
        },
    )

    return TeacherMaterialUploadResponse(
        material_id=material_id,
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


@router.post("/lesson-plans/generate", response_model=LessonPlanResponse)
def generate_lesson_plan(payload: LessonPlanGenerateRequest) -> LessonPlanResponse:
    plan_id = f"plan_{uuid4().hex[:12]}"
    now = _utc_iso()

    topics = payload.topics or ["concept-review", "guided-practice", "reflection"]
    sections = [
        LessonPlanSection(title=f"Warmup: {topics[0]}", duration_minutes=10, activity="diagnostic questions"),
        LessonPlanSection(title="Core concept", duration_minutes=20, activity="guided explanation"),
        LessonPlanSection(title="Practice", duration_minutes=20, activity="pair exercise"),
        LessonPlanSection(title="Exit ticket", duration_minutes=10, activity="quick assessment"),
    ]

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

    preview_images = [
        f"/output/previews/{ppt_id}/slide-1.png",
        f"/output/previews/{ppt_id}/slide-2.png",
    ]
    shared_memory.write(
        "generated_ppts",
        ppt_id,
        {
            "ppt_id": ppt_id,
            "plan_id": plan_id,
            "teacher_id": payload.teacher_id,
            "template": payload.template,
            "status": "completed",
            "progress": 100,
            "file_path": f"/output/ppts/{ppt_id}.pptx",
            "download_url": f"/api/v1/teacher/ppt/{ppt_id}/download",
            "preview_images": preview_images,
            "created_at": now,
            "updated_at": now,
            "title": plan.get("title"),
        },
    )
    return LessonPptGenerateResponse(
        ppt_id=ppt_id,
        status="completed",
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


@router.get("/ppt/{ppt_id}/download", response_model=PptDownloadResponse)
def get_ppt_download(ppt_id: str) -> PptDownloadResponse:
    entry = shared_memory.read("generated_ppts", ppt_id)
    if not entry:
        raise HTTPException(status_code=404, detail="ppt_not_found")
    value = entry.get("value", {})
    if value.get("status") != "completed":
        raise HTTPException(status_code=409, detail="ppt_not_ready")
    return PptDownloadResponse(ppt_id=ppt_id, download_url=value.get("download_url", ""))


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
