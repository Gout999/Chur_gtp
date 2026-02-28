from fastapi.testclient import TestClient

from app.main import app
from memory.shared import shared_memory


def _seed_escalation(escalation_id: str = "esc-100") -> str:
    shared_memory.write(
        "pending_escalations",
        escalation_id,
        {
            "student_id": "stu-z",
            "class_id": "class-z",
            "reason": "stuck for 20 minutes",
            "severity": "high",
            "created_at": "2026-02-28T13:00:00Z",
            "resolved": False,
        },
    )
    return escalation_id


def test_escalation_list_and_detail() -> None:
    escalation_id = _seed_escalation("esc-101")
    client = TestClient(app)

    list_resp = client.get("/api/v1/teacher/escalations")
    assert list_resp.status_code == 200
    ids = [item["escalation_id"] for item in list_resp.json()["escalations"]]
    assert escalation_id in ids

    detail_resp = client.get(f"/api/v1/teacher/escalations/{escalation_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["escalation_id"] == escalation_id
    assert detail["detail"]["student_id"] == "stu-z"


def test_escalation_response_marks_pending_resolved() -> None:
    escalation_id = _seed_escalation("esc-102")
    client = TestClient(app)

    response = client.post(
        f"/api/v1/teacher/escalations/{escalation_id}/respond",
        json={
            "teacher_id": "teacher-ops",
            "action": "resolve",
            "message": "Give the student a worked example first.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["escalation_id"] == escalation_id
    assert body["resolved"] is True

    pending = shared_memory.read("pending_escalations", escalation_id)
    assert pending is not None
    assert pending["value"]["resolved"] is True

    decision = shared_memory.read("teacher_escalation_responses", escalation_id)
    assert decision is not None
    assert decision["value"]["teacher_id"] == "teacher-ops"


def test_send_message_and_conversation() -> None:
    client = TestClient(app)
    send = client.post(
        "/api/v1/teacher/messages/send",
        json={
            "teacher_id": "teacher-ops",
            "student_id": "stu-z",
            "content": "Please retry step 2 with the formula hint.",
            "channel": "in_app",
        },
    )
    assert send.status_code == 200
    payload = send.json()
    assert payload["message_id"].startswith("msg_")
    assert payload["delivery_state"] == "queued"

    convo = client.get("/api/v1/teacher/messages/conversations/stu-z")
    assert convo.status_code == 200
    convo_data = convo.json()
    assert convo_data["student_id"] == "stu-z"
    assert convo_data["total"] >= 1
    assert any(item["content"].startswith("Please retry") for item in convo_data["items"])


def test_companion_pause_and_resume() -> None:
    client = TestClient(app)

    pause_resp = client.put(
        "/api/v1/teacher/companion/pause",
        json={"paused": True, "reason": "maintenance", "scope": "global"},
    )
    assert pause_resp.status_code == 200
    assert pause_resp.json()["paused"] is True

    resume_resp = client.put(
        "/api/v1/teacher/companion/pause",
        json={"paused": False, "reason": "ready", "scope": "global"},
    )
    assert resume_resp.status_code == 200
    assert resume_resp.json()["paused"] is False

    state = shared_memory.read("companion_control", "global")
    assert state is not None
    assert state["value"]["paused"] is False
