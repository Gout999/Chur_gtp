from fastapi.testclient import TestClient

from app.main import app

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def _data(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def _sample_config(strictness: str = "strict", max_push: int = 2) -> dict:
    return {
        "companion_strictness": strictness,
        "companion_max_attempts": 6,
        "companion_emotion_detection": True,
        "catalyst_enabled": True,
        "catalyst_push_frequency": "weekly",
        "catalyst_max_daily_push": max_push,
        "catalyst_content_review": True,
        "architect_default_boundary": "moderate",
        "architect_auto_expand": False,
        "notification_escalation_threshold": "high",
        "notification_delivery": ["in_app", "email"],
    }


def test_get_teacher_config_returns_defaults_without_existing_data() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/teacher/config",
        params={"teacher_id": "teacher-cfg-default"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = _data(response)
    assert data["teacher_id"] == "teacher-cfg-default"
    assert data["config"]["companion_strictness"] == "moderate"
    assert data["config"]["notification_delivery"] == ["in_app"]


def test_put_and_get_teacher_global_config_roundtrip() -> None:
    client = TestClient(app)
    config = _sample_config(strictness="gentle", max_push=4)

    put_resp = client.put(
        "/api/v1/teacher/config",
        json={"teacher_id": "teacher-cfg-1", "config": config},
        headers=AUTH_HEADERS,
    )
    assert put_resp.status_code == 200
    assert _data(put_resp)["config"]["companion_strictness"] == "gentle"

    get_resp = client.get(
        "/api/v1/teacher/config",
        params={"teacher_id": "teacher-cfg-1"},
        headers=AUTH_HEADERS,
    )
    assert get_resp.status_code == 200
    assert _data(get_resp)["config"]["catalyst_max_daily_push"] == 4


def test_class_config_override_read_write() -> None:
    client = TestClient(app)
    global_config = _sample_config(strictness="moderate", max_push=3)
    class_config = _sample_config(strictness="strict", max_push=1)

    client.put(
        "/api/v1/teacher/config",
        json={"teacher_id": "teacher-cfg-2", "config": global_config},
        headers=AUTH_HEADERS,
    )
    put_class = client.put(
        "/api/v1/teacher/classes/class-cfg-1/config",
        json={"teacher_id": "teacher-cfg-2", "config": class_config},
        headers=AUTH_HEADERS,
    )
    assert put_class.status_code == 200
    assert _data(put_class)["config"]["companion_strictness"] == "strict"

    get_class = client.get(
        "/api/v1/teacher/classes/class-cfg-1/config",
        params={"teacher_id": "teacher-cfg-2"},
        headers=AUTH_HEADERS,
    )
    assert get_class.status_code == 200
    data = _data(get_class)
    assert data["config"]["companion_strictness"] == "strict"
    assert data["config"]["catalyst_max_daily_push"] == 1


def test_notification_config_endpoint_updates_notification_fields() -> None:
    client = TestClient(app)
    client.put(
        "/api/v1/teacher/config",
        json={"teacher_id": "teacher-cfg-3", "config": _sample_config()},
        headers=AUTH_HEADERS,
    )

    update_resp = client.put(
        "/api/v1/teacher/config/notifications",
        json={
            "teacher_id": "teacher-cfg-3",
            "notification_escalation_threshold": "any",
            "notification_delivery": ["push"],
        },
        headers=AUTH_HEADERS,
    )
    assert update_resp.status_code == 200
    data = _data(update_resp)
    assert data["config"]["notification_escalation_threshold"] == "any"
    assert data["config"]["notification_delivery"] == ["push"]
