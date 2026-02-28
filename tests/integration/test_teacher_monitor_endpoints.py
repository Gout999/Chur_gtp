from fastapi.testclient import TestClient

from app.main import app
from memory.shared import shared_memory


def _seed_monitor_data() -> None:
    shared_memory.write(
        "student_cognitive_models",
        "stu-a",
        {
            "student_id": "stu-a",
            "class_id": "class-1",
            "mastery_score": 0.3,
            "latest_topic": "algebra",
            "misconceptions": ["fractions"],
            "confidence": 0.4,
        },
    )
    shared_memory.write(
        "student_cognitive_models",
        "stu-b",
        {
            "student_id": "stu-b",
            "class_id": "class-1",
            "mastery_score": 0.9,
            "latest_topic": "geometry",
            "misconceptions": [],
            "confidence": 0.8,
        },
    )

    shared_memory.write(
        "interaction_episodes",
        "ep-1",
        {
            "student_id": "stu-a",
            "class_id": "class-1",
            "timestamp": "2026-02-28T10:00:00Z",
            "agent": "socratic_companion",
            "decision": "ask_guiding_question",
            "tool": "construct_hint",
            "topic": "algebra",
            "role": "assistant",
            "content": "Try expanding the expression first.",
        },
    )
    shared_memory.write(
        "interaction_episodes",
        "ep-2",
        {
            "student_id": "stu-a",
            "class_id": "class-1",
            "timestamp": "2026-02-28T11:00:00Z",
            "agent": "pedagogical_architect",
            "decision": "request_validation",
            "tool": "establish_knowledge_boundary",
            "topic": "algebra",
            "role": "assistant",
            "content": "Let's validate scope before answering.",
        },
    )
    shared_memory.write(
        "interaction_episodes",
        "ep-3",
        {
            "student_id": "stu-a",
            "class_id": "class-1",
            "timestamp": "2026-02-28T12:00:00Z",
            "agent": "socratic_companion",
            "decision": "summarize",
            "tool": "construct_hint",
            "topic": "geometry",
            "role": "assistant",
            "content": "Now compare triangle properties.",
        },
    )

    shared_memory.write(
        "pending_escalations",
        "esc-1",
        {
            "class_id": "class-1",
            "student_id": "stu-a",
            "reason": "repeated confusion",
        },
    )


def test_class_overview_returns_aggregate_stats() -> None:
    _seed_monitor_data()
    client = TestClient(app)

    response = client.get("/api/v1/teacher/classes/class-1/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["class_id"] == "class-1"
    assert data["total_students"] >= 2
    assert data["total_interactions"] >= 3
    assert data["pending_escalations"] >= 1
    assert data["at_risk_students"] >= 1


def test_class_students_returns_sorted_roster() -> None:
    _seed_monitor_data()
    client = TestClient(app)

    response = client.get("/api/v1/teacher/classes/class-1/students")
    assert response.status_code == 200
    data = response.json()
    assert data["class_id"] == "class-1"
    assert len(data["students"]) >= 2
    ids = [item["student_id"] for item in data["students"]]
    assert ids == sorted(ids)


def test_student_detail_and_cognition_endpoints() -> None:
    _seed_monitor_data()
    client = TestClient(app)

    detail = client.get("/api/v1/teacher/students/stu-a")
    assert detail.status_code == 200
    detail_data = detail.json()
    assert detail_data["student_id"] == "stu-a"
    assert detail_data["mastery_score"] == 0.3

    cognition = client.get("/api/v1/teacher/students/stu-a/cognition")
    assert cognition.status_code == 200
    cognition_data = cognition.json()
    assert cognition_data["student_id"] == "stu-a"
    assert cognition_data["misconceptions"] == ["fractions"]


def test_student_agent_logs_endpoint_returns_ordered_logs() -> None:
    _seed_monitor_data()
    client = TestClient(app)

    response = client.get("/api/v1/teacher/students/stu-a/agent-logs")
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "stu-a"
    assert len(data["logs"]) >= 2
    timestamps = [item["timestamp"] for item in data["logs"] if item["timestamp"]]
    assert timestamps == sorted(timestamps)


def test_student_interactions_endpoint_supports_topic_filter() -> None:
    _seed_monitor_data()
    client = TestClient(app)

    response = client.get(
        "/api/v1/teacher/students/stu-a/interactions",
        params={"topic": "geometry"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "stu-a"
    assert data["total"] >= 1
    assert all(item["topic"] == "geometry" for item in data["items"])
