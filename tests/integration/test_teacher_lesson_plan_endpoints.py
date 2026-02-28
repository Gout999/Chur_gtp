from fastapi.testclient import TestClient

from app.main import app

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def _data(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


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
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200
    return _data(resp)["plan_id"]


def test_lesson_plan_generate_get_update_delete_flow() -> None:
    client = TestClient(app)
    plan_id = _generate_plan(client)

    get_resp = client.get(f"/api/v1/teacher/lesson-plans/{plan_id}", headers=AUTH_HEADERS)
    assert get_resp.status_code == 200
    assert _data(get_resp)["title"] == "Algebra Intro"
    assert _data(get_resp)["version"] == 1

    update_resp = client.put(
        f"/api/v1/teacher/lesson-plans/{plan_id}",
        json={
            "teacher_id": "teacher-lp",
            "title": "Algebra Intro (Revised)",
            "objective": "Master linear equations and slope.",
        },
        headers=AUTH_HEADERS,
    )
    assert update_resp.status_code == 200
    update_data = _data(update_resp)
    assert update_data["title"] == "Algebra Intro (Revised)"
    assert update_data["version"] == 2

    delete_resp = client.delete(f"/api/v1/teacher/lesson-plans/{plan_id}", headers=AUTH_HEADERS)
    assert delete_resp.status_code == 200
    assert _data(delete_resp)["deleted"] is True

    second_delete = client.delete(f"/api/v1/teacher/lesson-plans/{plan_id}", headers=AUTH_HEADERS)
    assert second_delete.status_code == 200
    assert _data(second_delete)["deleted"] is True

    get_deleted = client.get(f"/api/v1/teacher/lesson-plans/{plan_id}", headers=AUTH_HEADERS)
    assert get_deleted.status_code == 404


def test_lesson_plan_ppt_generation_and_access_flow() -> None:
    client = TestClient(app)
    plan_id = _generate_plan(client)

    gen_ppt = client.post(
        f"/api/v1/teacher/lesson-plans/{plan_id}/ppt",
        json={"teacher_id": "teacher-lp", "template": "lesson_default"},
        headers=AUTH_HEADERS,
    )
    assert gen_ppt.status_code == 200
    gen_data = _data(gen_ppt)
    ppt_id = gen_data["ppt_id"]
    assert gen_data["status"] == "completed"

    status_resp = client.get(f"/api/v1/teacher/ppt/{ppt_id}/status", headers=AUTH_HEADERS)
    assert status_resp.status_code == 200
    status_data = _data(status_resp)
    assert status_data["status"] == "completed"
    assert status_data["progress"] == 100

    preview_resp = client.get(f"/api/v1/teacher/ppt/{ppt_id}/preview", headers=AUTH_HEADERS)
    assert preview_resp.status_code == 200
    preview_data = _data(preview_resp)
    assert len(preview_data["preview_images"]) >= 1

    download_resp = client.get(f"/api/v1/teacher/ppt/{ppt_id}/download", headers=AUTH_HEADERS)
    assert download_resp.status_code == 200
    # 验证返回的是PPT文件（二进制内容）
    assert download_resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    assert len(download_resp.content) > 1000  # PPT文件应该有一定大小
    assert download_resp.headers["content-disposition"].endswith(".pptx")


def test_lesson_template_list_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/teacher/lesson-templates", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = _data(response)
    assert len(data["templates"]) >= 3
    ids = [item["template_id"] for item in data["templates"]]
    assert "lesson_default" in ids
