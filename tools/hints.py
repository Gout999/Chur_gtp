"""
construct_hint: build personalized hint by error pattern and student profile.
PRD section 2.2.2; Phase 3 (Engineer B).
"""
from typing import Any, Dict, Optional
from uuid import uuid4


def _strategy_from_error(error_analysis: Dict[str, Any]) -> str:
    if error_analysis.get("type") == "conceptual":
        return "socratic"
    if error_analysis.get("type") == "calculation":
        return "decompose"
    if error_analysis.get("type") == "vocabulary":
        return "analogy"
    return "socratic"


def construct_hint(
    student_id: str,
    current_input: str,
    target_concept: str,
    error_analysis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Return hint_id, strategy, hint_content, follow_up_questions,
    difficulty_level, expected_response_type.
    """
    analysis = error_analysis or {}
    strategy = _strategy_from_error(analysis)
    hint_content = (
        f"Before solving, explain how '{target_concept}' relates to your last step. "
        f"Then try one small revision of: '{current_input[:80]}'."
    )
    follow_up_questions = [
        f"What assumption are you making about {target_concept}?",
        "Which part are you most certain about, and why?",
    ]

    return {
        "hint_id": f"hint_{uuid4().hex[:12]}",
        "student_id": student_id,
        "strategy": strategy,
        "hint_content": hint_content,
        "follow_up_questions": follow_up_questions,
        "difficulty_level": 0.5,
        "expected_response_type": "explanation",
    }
