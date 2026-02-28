"""Companion tool bindings."""
from tools.cognition import update_student_cognition_map
from tools.hints import construct_hint, escalate_to_human

__all__ = ["construct_hint", "escalate_to_human", "update_student_cognition_map"]
