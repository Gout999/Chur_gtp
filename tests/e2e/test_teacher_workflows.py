from fastapi.testclient import TestClient

from app.main import app
from memory.shared import shared_memory


AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def _data(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_teacher_material_lifecycle_workflow() -> None:
    client = TestClient(app)

    upload = client.post(
        "/api/v1/teacher/materials/upload",
        files={"file": ("workflow.pdf", b"%PDF-1.4 workflow test content", "application/pdf")},
        data={
            "teacher_id": "teacher-e2e",
            "source_type": "teacher_upload",
        },
        headers=AUTH_HEADERS,
    )
    material_id = _data(upload)["material_id"]

    status = client.get(f"/api/v1/teacher/materials/{material_id}/status", headers=AUTH_HEADERS)
    assert _data(status)["status"] == "queued"

    boundary = client.put(
        f"/api/v1/teacher/materials/{material_id}/boundary",
        json={"strictness": "moderate"},
        headers=AUTH_HEADERS,
    )
    assert _data(boundary)["strictness"] == "moderate"

    importance = client.put(
        f"/api/v1/teacher/materials/{material_id}/importance",
        json={"marks": [{"concept": "core", "level": "high"}]},
        headers=AUTH_HEADERS,
    )
    assert _data(importance)["marks_saved"] == 1

    graph = client.get(
        f"/api/v1/teacher/materials/{material_id}/knowledge-graph",
        headers=AUTH_HEADERS,
    )
    assert len(_data(graph)["nodes"]) >= 1

    delete_resp = client.delete(f"/api/v1/teacher/materials/{material_id}", headers=AUTH_HEADERS)
    assert _data(delete_resp)["deleted"] is True


def test_teacher_intervention_workflow() -> None:
    client = TestClient(app)

    shared_memory.write(
        "pending_escalations",
        "esc-e2e",
        {
            "student_id": "stu-e2e",
            "class_id": "class-e2e",
            "reason": "stuck",
            "severity": "high",
            "created_at": "2026-02-28T15:00:00Z",
        },
    )

    list_resp = client.get("/api/v1/teacher/escalations", headers=AUTH_HEADERS)
    assert list_resp.status_code == 200
    ids = [item["escalation_id"] for item in _data(list_resp)["escalations"]]
    assert "esc-e2e" in ids

    response = client.post(
        "/api/v1/teacher/escalations/esc-e2e/respond",
        json={"teacher_id": "teacher-e2e", "action": "resolve", "message": "Reviewed."},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    assert _data(response)["resolved"] is True

    send = client.post(
        "/api/v1/teacher/messages/send",
        json={
            "teacher_id": "teacher-e2e",
            "student_id": "stu-e2e",
            "content": "Let's retry with a hint.",
            "channel": "in_app",
        },
        headers=AUTH_HEADERS,
    )
    assert _data(send)["delivery_state"] == "queued"

    pause = client.put(
        "/api/v1/teacher/companion/pause",
        json={"paused": True, "scope": "global", "reason": "manual intervention"},
        headers=AUTH_HEADERS,
    )
    assert _data(pause)["paused"] is True


def test_teacher_lesson_plan_and_ppt_workflow() -> None:
    client = TestClient(app)
    plan = client.post(
        "/api/v1/teacher/lesson-plans/generate",
        json={
            "teacher_id": "teacher-e2e",
            "class_id": "class-e2e",
            "title": "Workflow Lesson",
            "objective": "Validate end-to-end lesson pipeline.",
        },
        headers=AUTH_HEADERS,
    )
    plan_id = _data(plan)["plan_id"]

    updated = client.put(
        f"/api/v1/teacher/lesson-plans/{plan_id}",
        json={"teacher_id": "teacher-e2e", "title": "Workflow Lesson v2"},
        headers=AUTH_HEADERS,
    )
    assert _data(updated)["version"] >= 2

    ppt = client.post(
        f"/api/v1/teacher/lesson-plans/{plan_id}/ppt",
        json={"teacher_id": "teacher-e2e", "template": "lesson_default"},
        headers=AUTH_HEADERS,
    )
    ppt_id = _data(ppt)["ppt_id"]

    status = client.get(f"/api/v1/teacher/ppt/{ppt_id}/status", headers=AUTH_HEADERS)
    assert _data(status)["status"] == "completed"

    preview = client.get(f"/api/v1/teacher/ppt/{ppt_id}/preview", headers=AUTH_HEADERS)
    assert len(_data(preview)["preview_images"]) >= 1

    download = client.get(f"/api/v1/teacher/ppt/{ppt_id}/download", headers=AUTH_HEADERS)
    assert download.status_code == 200
    # 验证返回的是PPT文件
    assert download.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    assert len(download.content) > 1000
