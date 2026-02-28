"""
External Memory: retrievable long-term memory (vector store).
PRD §3.1; Agent decides when to store/retrieve.
"""
from typing import Dict, Any, List


class ExternalMemory:
    """
    Long-term memory with vector retrieval (e.g. ChromaDB).
    Collections: teacher_knowledge_graph, student_cognitive_models,
    student_interest_universe, interaction_episodes.
    """
    # Placeholder until ChromaDB etc. are wired
    vector_store: Any = None
    collections: Dict[str, Dict[str, Any]] = {}

    def __init__(self):
        self.collections = {
            "teacher_knowledge_graph": {"type": "knowledge_graph"},
            "student_cognitive_models": {"type": "structured_vector", "per_student": True},
            "student_interest_universe": {"type": "hybrid_vector", "per_student": True},
            "interaction_episodes": {"type": "temporal_vector"},
        }
