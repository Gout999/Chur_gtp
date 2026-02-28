"""Unit tests for escalate_to_human tool (P0 stub).

These tests define the contract that the P0 stub MUST satisfy.  The function
does not exist yet -- tests are expected to fail (xfail) until the stub is
implemented in tools/hints.py.

Anchored to: COMPANION_PRD §5.2, COMPANION_LOGIC_FLOW Path B, prompt Iron Rule 4.
"""

import pytest

import tools.hints as _hints_mod

_HAS_ESCALATE = hasattr(_hints_mod, "escalate_to_human")
escalate_to_human = getattr(_hints_mod, "escalate_to_human", None)

_xfail_no_escalate = pytest.mark.xfail(
    not _HAS_ESCALATE,
    reason="escalate_to_human P0 stub not yet implemented in tools/hints.py",
    strict=True,
)

pytestmark = [pytest.mark.unit, _xfail_no_escalate]

REQUIRED_KEYS = {
    "escalation_id",
    "teacher_notification_sent",
    "estimated_response_time",
    "student_message",
}


class TestCallableExists:

    def test_callable_exists(self):
        assert callable(escalate_to_human)


class TestReturnSchema:

    def test_returns_required_keys(self):
        result = escalate_to_human(
            student_id="s1",
            reason="frustration",
            context_summary="Student expressed frustration",
            urgency="medium",
        )
        assert REQUIRED_KEYS.issubset(result.keys())


class TestComfortMessages:
    """Each escalation reason must produce a non-empty student-facing message."""

    @pytest.mark.parametrize("reason,urgency", [
        ("frustration", "medium"),
        ("repeated_failure", "high"),
        ("emotional_distress", "high"),
        ("out_of_scope", "low"),
    ])
    def test_reason_returns_comfort_message(self, reason, urgency):
        result = escalate_to_human(
            student_id="s1",
            reason=reason,
            context_summary=f"Testing {reason}",
            urgency=urgency,
        )
        assert isinstance(result["student_message"], str)
        assert len(result["student_message"]) > 0

    def test_different_reasons_produce_different_messages(self):
        r_frust = escalate_to_human(
            "s1", "frustration", "frustrated", "medium",
        )
        r_fail = escalate_to_human(
            "s1", "repeated_failure", "failed 5 times", "high",
        )
        assert r_frust["student_message"] != r_fail["student_message"]


class TestEscalationPersistence:

    def test_escalation_logged_to_interaction_episodes(self):
        from memory.shared import shared_memory

        escalate_to_human(
            student_id="s-log",
            reason="repeated_failure",
            context_summary="5 failures on momentum",
            urgency="high",
        )
        episodes = shared_memory.read_all("interaction_episodes")
        escalation_entries = [
            e for e in episodes
            if "escalat" in str(e["value"]).lower()
        ]
        assert len(escalation_entries) >= 1
