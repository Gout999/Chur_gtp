"""
E2E tests for Task 5: 主动推送/定时入口 (proactive push / scheduled entry).

Verifies the Catalyst node pipeline: monitor tools -> synthesize_briefing -> notifications.
We call curiosity_catalyst_node ONCE only to avoid graph self-loop (loop_count exit at 101).
Also verifies the graph-external entry run_new_content_check and its return shape.
"""
from __future__ import annotations

from agents.catalyst import run_new_content_check
from agents.catalyst.node import curiosity_catalyst_node


def test_task5_catalyst_node_single_run_new_content_detected() -> None:
    """
    单次调用 Catalyst 节点，event_type=new_content_detected。
    断言：节点执行一次、写 tools_to_call、可写 notifications、loop_count+1。
    不触发图内多轮，避免长时间或死循环。
    """
    state = {
        "event_type": "new_content_detected",
        "event_payload": {
            "student_id": "task5-test-student",
            "interest_keywords": ["machine learning", "education"],
            "curriculum_context": {"topic": "optimization"},
        },
        "working_memory": {},
        "session_id": "task5-session-1",
        "timestamp": "2024-01-01T12:00:00",
        "loop_count": 0,
        "notifications": [],
    }

    out = curiosity_catalyst_node(state)

    assert out["current_agent"] == "curiosity_catalyst"
    assert out.get("loop_count") == 1
    assert isinstance(out.get("notifications"), list)
    tools_to_call = out.get("tools_to_call") or []
    tool_names = [t.get("tool") for t in tools_to_call if isinstance(t, dict) and t.get("tool")]
    assert "monitor_arxiv_domain" in tool_names
    assert "monitor_github_domain" in tool_names
    assert "synthesize_briefing" in tool_names
    assert "response_to_student" in out
    assert out.get("agent_decision") == ""  # new_content_detected -> not monitor_tick


def test_task5_catalyst_node_notifications_when_should_notify() -> None:
    """
    当有内容且简报决定应通知时，notifications 应包含 curiosity_briefing 条目。
    单次调用，不循环。
    """
    state = {
        "event_type": "new_content_detected",
        "event_payload": {
            "student_id": "task5-notify-student",
            "interest_keywords": ["reinforcement learning"],
            "curriculum_context": {"topic": "ML"},
        },
        "session_id": "task5-session-2",
        "loop_count": 0,
        "notifications": [],
    }

    out = curiosity_catalyst_node(state)

    assert isinstance(out.get("notifications"), list)
    if out.get("notifications"):
        first = out["notifications"][0]
        assert first.get("type") == "curiosity_briefing"
        assert first.get("student_id") == "task5-notify-student"
        assert "briefing_id" in first or first.get("briefing_id") is not None


def test_task5_no_infinite_loop_single_invocation() -> None:
    """
    仅验证：单次调用节点后 loop_count 仅增加 1。
    若在此处循环调用节点或图，一旦发现 loop_count 异常增长立即失败。
    """
    state = {
        "event_type": "new_content_detected",
        "event_payload": {"student_id": "loop-test", "interest_keywords": ["AI"]},
        "loop_count": 0,
        "notifications": [],
    }

    out = curiosity_catalyst_node(state)

    assert out.get("loop_count") == 1, "Single invocation must increment loop_count by exactly 1"


def test_task5_run_new_content_check_entry_point() -> None:
    """
    图外入口 run_new_content_check：单次执行，返回含 notifications/tools_to_call 等。
    定时任务或 HTTP 可调用此函数触发一次新内容检测与通知。
    """
    result = run_new_content_check(
        student_id="entry-test-student",
        interest_keywords=["deep learning", "NLP"],
        curriculum_context={"topic": "ML"},
    )
    assert "notifications" in result
    assert isinstance(result["notifications"], list)
    assert result.get("current_agent") == "curiosity_catalyst"
    assert "tools_to_call" in result
    tools = result["tools_to_call"]
    assert any(t.get("tool") == "monitor_arxiv_domain" for t in tools if isinstance(t, dict))
    assert any(t.get("tool") == "synthesize_briefing" for t in tools if isinstance(t, dict))
