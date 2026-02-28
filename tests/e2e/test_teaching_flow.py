from agents.architect.node import pedagogical_architect_node
from agents.catalyst.node import curiosity_catalyst_node
from agents.companion.node import socratic_companion_node


def test_complete_teaching_flow() -> None:
    state = {
        "event_type": "file_upload",
        "event_payload": {
            "file_path": "test.pdf",
            "student_id": "stu-1",
            "content": "I do not understand gradient descent",
            "target_concept": "gradient_descent",
            "interest_keywords": ["optimization", "machine learning"],
            "curriculum_context": {"topic": "optimization"},
        },
        "working_memory": {},
        "session_id": "flow-1",
        "timestamp": "2024-01-01T00:00:00",
        "loop_count": 0,
    }

    state = pedagogical_architect_node(state)
    state["event_type"] = "student_message"
    state = socratic_companion_node(state)
    state["event_type"] = "new_content_detected"
    state = curiosity_catalyst_node(state)

    assert state["current_agent"] == "curiosity_catalyst"
    assert state["loop_count"] == 3
    assert isinstance(state.get("notifications", []), list)
