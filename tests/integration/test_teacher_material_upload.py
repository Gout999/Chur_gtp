from fastapi.testclient import TestClient

from app.main import app
from memory.shared import shared_memory

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def _data(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def _upload_material(client: TestClient) -> str:
    payload = {
        "teacher_id": "teacher-001",
        "file_name": "chapter-1.pdf",
        "file_path": "/tmp/chapter-1.pdf",
        "class_id": "class-a",
        "source_type": "teacher_upload",
        "content_type": "application/pdf",
        "tags": ["algebra", "grade8"],
    }
    response = client.post("/api/v1/teacher/materials/upload", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    return _data(response)["material_id"]


def test_teacher_material_upload_persists_to_shared_memory() -> None:
    client = TestClient(app)

    material_id = _upload_material(client)
    status_response = client.get(
        f"/api/v1/teacher/materials/{material_id}/status",
        headers=AUTH_HEADERS,
    )
    data = _data(status_response)

    assert data["status"] == "queued"
    assert data["material_id"].startswith("mat_")
    assert "stored_at" in data

    memory_entry = shared_memory.read("teacher_uploads", material_id)
    assert memory_entry is not None
    assert memory_entry["value"]["teacher_id"] == "teacher-001"
    assert memory_entry["value"]["file_name"] == "chapter-1.pdf"
    assert memory_entry["value"]["status"] == "queued"


def test_teacher_material_status_unknown_returns_404() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/teacher/materials/mat_unknown/status", headers=AUTH_HEADERS)
    assert response.status_code == 404
    assert response.json()["error"]["detail"] == "material_not_found"


def test_teacher_material_boundary_update_writes_adjustment() -> None:
    client = TestClient(app)
    material_id = _upload_material(client)

    response = client.put(
        f"/api/v1/teacher/materials/{material_id}/boundary",
        json={"strictness": "strict", "reason": "exam week"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = _data(response)
    assert data["material_id"] == material_id
    assert data["strictness"] == "strict"

    entry = shared_memory.read("teacher_boundary_adjustments", material_id)
    assert entry is not None
    assert entry["value"]["strictness"] == "strict"
    assert entry["value"]["history"][-1]["reason"] == "exam week"


def test_teacher_material_importance_update_writes_marks() -> None:
    client = TestClient(app)
    material_id = _upload_material(client)

    response = client.put(
        f"/api/v1/teacher/materials/{material_id}/importance",
        json={
            "marks": [
                {"concept": "linear-equation", "level": "high", "note": "core exam point"},
                {"concept": "graphing", "level": "medium"},
            ]
        },
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = _data(response)
    assert data["material_id"] == material_id
    assert data["marks_saved"] == 2

    entry = shared_memory.read("teacher_importance_marks", material_id)
    assert entry is not None
    assert len(entry["value"]["marks"]) == 2
    assert entry["value"]["marks"][0]["concept"] == "linear-equation"


def test_teacher_material_knowledge_graph_returns_schema() -> None:
    client = TestClient(app)
    material_id = _upload_material(client)

    response = client.get(
        f"/api/v1/teacher/materials/{material_id}/knowledge-graph",
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = _data(response)

    assert data["material_id"] == material_id
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)
    assert len(data["nodes"]) >= 1


def test_teacher_material_delete_is_idempotent_and_hides_status() -> None:
    client = TestClient(app)
    material_id = _upload_material(client)

    # Seed related records to verify cleanup marking.
    client.put(
        f"/api/v1/teacher/materials/{material_id}/boundary",
        json={"strictness": "moderate"},
        headers=AUTH_HEADERS,
    )
    client.put(
        f"/api/v1/teacher/materials/{material_id}/importance",
        json={"marks": [{"concept": "fractions", "level": "low"}]},
        headers=AUTH_HEADERS,
    )

    delete_response = client.delete(f"/api/v1/teacher/materials/{material_id}", headers=AUTH_HEADERS)
    assert delete_response.status_code == 200
    assert _data(delete_response)["deleted"] is True

    second_delete = client.delete(f"/api/v1/teacher/materials/{material_id}", headers=AUTH_HEADERS)
    assert second_delete.status_code == 200
    assert _data(second_delete)["deleted"] is True

    status_response = client.get(f"/api/v1/teacher/materials/{material_id}/status", headers=AUTH_HEADERS)
    assert status_response.status_code == 404

    boundary_entry = shared_memory.read("teacher_boundary_adjustments", material_id)
    assert boundary_entry is not None
    assert boundary_entry["value"]["archived"] is True

    importance_entry = shared_memory.read("teacher_importance_marks", material_id)
    assert importance_entry is not None
    assert importance_entry["value"]["archived"] is True
