"""
EduGuide agents: graph nodes for Architect, Companion, Catalyst.
graph.py imports from here. PRD §4.1.

Catalyst is imported lazily so Companion-only use (e.g. scripts/companion_chat_test.py,
_demo_companion.py) does not require the arxiv dependency.
"""
from .architect import pedagogical_architect_node
from .companion import socratic_companion_node


def __getattr__(name: str):
    if name == "curiosity_catalyst_node":
        from .catalyst import curiosity_catalyst_node
        return curiosity_catalyst_node
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "pedagogical_architect_node",
    "socratic_companion_node",
    "curiosity_catalyst_node",
]
