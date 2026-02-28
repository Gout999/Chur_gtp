from fastapi.testclient import TestClient

from app.main import app


def _generate_plan(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/teacher/lesson-plans/generate",
        json={
            "teacher_id": "teacher-lp",
            "class_id": "class-lp",
            "title": "Algebra Intro",
            "objective": "Understand linear equations.",
            "material_ids": ["mat_demo_1"],
            "topics": ["linear-equations", "graphing"],
        },
    )
    assert resp.status_code == 200
    return resp.json()["plan_id"]


def test_lesson_plan_generate_get_update_delete_flow() -> None:
    client = TestClient(app)
    plan_id = _generate_plan(client)

    get_resp = client.get(f"/api/v1/teacher/lesson-plans/{plan_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Algebra Intro"
    assert get_resp.json()["version"] == 1

    update_resp = client.put(
        f"/api/v1/teacher/lesson-plans/{plan_id}",
        json={
            "teacher_id": "teacher-lp",
            "title": "Algebra Intro (Revised)",
            "objective": "Master linear equations and slope.",
        },
    )
    assert update_resp.status_code == 200
    update_data = update_resp.json()
    assert update_data["title"] == "Algebra Intro (Revised)"
    assert update_data["version"] == 2

    delete_resp = client.delete(f"/api/v1/teacher/lesson-plans/{plan_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] is True

    second_delete = client.delete(f"/api/v1/teacher/lesson-plans/{plan_id}")
    assert second_delete.status_code == 200
    assert second_delete.json()["deleted"] is True

    get_deleted = client.get(f"/api/v1/teacher/lesson-plans/{plan_id}")
    assert get_deleted.status_code == 404


def test_lesson_plan_ppt_generation_and_access_flow() -> None:
    client = TestClient(app)
    plan_id = _generate_plan(client)

    gen_ppt = client.post(
        f"/api/v1/teacher/lesson-plans/{plan_id}/ppt",
        json={"teacher_id": "teacher-lp", "template": "lesson_default"},
    )
    assert gen_ppt.status_code == 200
    gen_data = gen_ppt.json()
    ppt_id = gen_data["ppt_id"]
    assert gen_data["status"] == "completed"

    status_resp = client.get(f"/api/v1/teacher/ppt/{ppt_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "completed"
    assert status_data["progress"] == 100

    preview_resp = client.get(f"/api/v1/teacher/ppt/{ppt_id}/preview")
    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()
    assert len(preview_data["preview_images"]) >= 1

    download_resp = client.get(f"/api/v1/teacher/ppt/{ppt_id}/download")
    assert download_resp.status_code == 200
    assert download_resp.json()["download_url"].endswith("/download")


def test_lesson_template_list_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/teacher/lesson-templates")
    assert response.status_code == 200
    data = response.json()
    assert len(data["templates"]) >= 3
    ids = [item["template_id"] for item in data["templates"]]
    assert "lesson_default" in ids
