"""Integration tests for homework marker API (image upload + MiniMax vision)."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

# Minimal 1x1 PNG (valid header + minimal IDAT)
MINI_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_homework_mark_rejects_missing_or_invalid_file() -> None:
    client = TestClient(app)
    # No file at all -> 422 from FastAPI validation
    resp = client.post(
        "/api/v1/homework/mark",
        data={"max_score": "100"},
    )
    assert resp.status_code == 422
    # File with no filename may yield 422 (validation) or 400 (our check)
    resp2 = client.post(
        "/api/v1/homework/mark",
        files={"file": ("", MINI_PNG, "image/png")},
        data={"max_score": "100"},
    )
    assert resp2.status_code in (400, 422)


def test_homework_mark_rejects_invalid_extension() -> None:
    client = TestClient(app)
    resp = client.post(
        "/api/v1/homework/mark",
        files={"file": ("homework.pdf", b"fake pdf", "application/pdf")},
        data={"max_score": "100"},
    )
    assert resp.status_code == 400
    assert "Invalid file type" in resp.json().get("detail", "")


def test_homework_mark_rejects_file_too_large() -> None:
    client = TestClient(app)
    with patch("app.api.v1.homework.MAX_HOMEWORK_IMAGE_BYTES", 10):
        resp = client.post(
            "/api/v1/homework/mark",
            files={"file": ("hw.png", MINI_PNG, "image/png")},
            data={"max_score": "100"},
        )
    assert resp.status_code == 413
    assert "too large" in resp.json().get("detail", "").lower()


def test_homework_mark_success_returns_structured_response() -> None:
    client = TestClient(app)
    mock_result = {
        "score": 85,
        "max_score": 100,
        "feedback": "Good work overall.",
        "criteria_scores": [
            {"name": "Correctness", "score": 8, "comment": "Minor errors."},
        ],
        "model_used": "MiniMax-Text-01",
    }
    with patch(
        "app.api.v1.homework.mark_homework_from_image",
        return_value=mock_result,
    ):
        resp = client.post(
            "/api/v1/homework/mark",
            files={"file": ("homework.jpg", MINI_PNG, "image/jpeg")},
            data={"max_score": "100", "subject": "Math"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 85
    assert data["max_score"] == 100
    assert data["feedback"] == "Good work overall."
    assert data["model_used"] == "MiniMax-Text-01"
    assert len(data["criteria_scores"]) == 1
    assert data["criteria_scores"][0]["name"] == "Correctness"
    assert data["criteria_scores"][0]["score"] == 8
