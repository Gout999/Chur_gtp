"""
construct_hint: build personalized hint by error pattern and student profile.
PRD §2.2.2; Phase 3 – Engineer B (Companion).
"""
from typing import Dict, Any, Optional


def construct_hint(
    student_id: str,
    current_input: str,
    target_concept: str,
    error_analysis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Return hint_id, strategy, hint_content, follow_up_questions, difficulty_level, expected_response_type.
    """
    # TODO: Implement hint strategy (socratic / analogy / decompose / confront)
    return {
        "hint_id": "",
        "strategy": "socratic",
        "hint_content": "",
        "follow_up_questions": [],
        "difficulty_level": 0.5,
        "expected_response_type": "explanation",
    }
