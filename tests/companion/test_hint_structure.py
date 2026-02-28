"""Unit tests for hint structure: max 2 follow-ups, optional teacher chunks (Plan §1, §5)."""
import pytest

from tools.hints import _MAX_FOLLOW_UP_QUESTIONS, construct_hint

pytestmark = pytest.mark.unit


class TestHintFollowUpCap:
    """construct_hint returns at most 2 follow-up questions (Plan §1)."""

    def test_follow_ups_capped_at_two(self):
        result = construct_hint(
            student_id="cap-student",
            current_input="What is force?",
            target_concept="force",
            error_analysis=None,
        )
        follow_ups = result.get("follow_up_questions", [])
        assert isinstance(follow_ups, list)
        assert len(follow_ups) <= _MAX_FOLLOW_UP_QUESTIONS, "at most 2 follow-up questions"

    def test_accepts_teacher_knowledge_chunks_optional(self):
        result = construct_hint(
            student_id="tk-student",
            current_input="Explain F=ma",
            target_concept="Newton second law",
            error_analysis=None,
            teacher_knowledge_chunks=[
                {"content": "F=ma: force equals mass times acceleration.", "source": "teacher"},
            ],
        )
        assert "hint_content" in result
        assert len(result.get("follow_up_questions", [])) <= _MAX_FOLLOW_UP_QUESTIONS
