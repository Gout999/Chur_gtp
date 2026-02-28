from agents.architect.node import pedagogical_architect_node


def test_architect_processes_upload() -> None:
    state = {
        "event_type": "file_upload",
        "event_payload": {
            "file_path": "test.pdf",
            "material_name": "Test Material",
        },
        "working_memory": {},
        "session_id": "test-session",
        "timestamp": "2024-01-01T00:00:00",
        "loop_count": 0,
    }

    result = pedagogical_architect_node(state)

    assert result["current_agent"] == "pedagogical_architect"
    assert result["loop_count"] == 1
    assert isinstance(result["tools_to_call"], list)
