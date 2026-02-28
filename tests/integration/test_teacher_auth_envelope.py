from fastapi.testclient import TestClient

from app.main import app


def test_teacher_endpoint_requires_bearer_auth() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/teacher/profile")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["detail"] == "Missing Authorization header"


def test_teacher_endpoint_success_uses_envelope_schema() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/teacher/profile",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == "teacher-demo"
