"""
EduGuide Agent system prompts. PRD §6: architect, companion, catalyst.
"""
from .architect import PEDAGOGICAL_ARCHITECT_PROMPT
from .companion import SOCRATIC_COMPANION_PROMPT
from .catalyst import CURIOSITY_CATALYST_PROMPT

__all__ = [
    "PEDAGOGICAL_ARCHITECT_PROMPT",
    "SOCRATIC_COMPANION_PROMPT",
    "CURIOSITY_CATALYST_PROMPT",
]
