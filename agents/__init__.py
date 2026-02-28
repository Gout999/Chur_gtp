"""
EduGuide agents: graph nodes for Architect, Companion, Catalyst.
graph.py imports from here. PRD §4.1.
"""
from .architect import pedagogical_architect_node
from .companion import socratic_companion_node
from .catalyst import curiosity_catalyst_node

__all__ = [
    "pedagogical_architect_node",
    "socratic_companion_node",
    "curiosity_catalyst_node",
]
