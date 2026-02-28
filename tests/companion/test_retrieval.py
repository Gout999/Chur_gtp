"""Unit tests for teacher knowledge retrieval (Companion plan §5)."""
import pytest

from memory.retrieval import retrieve_teacher_knowledge

pytestmark = pytest.mark.unit


class TestRetrieveTeacherKnowledge:
    """retrieve_teacher_knowledge returns chunks from scope and optional shared memory."""

    def test_empty_scope_returns_empty_or_minimal(self):
        chunks = retrieve_teacher_knowledge("What is force?", {}, top_k=3)
        assert isinstance(chunks, list)
        assert len(chunks) <= 3

    def test_curriculum_topics_become_chunks(self):
        scope = {"scope_level": "moderate", "curriculum_topics": ["Newton's second law", "force"]}
        chunks = retrieve_teacher_knowledge("What is force?", scope, top_k=5)
        assert len(chunks) >= 1
        assert all("content" in c and "source" in c for c in chunks)
        contents = " ".join(c["content"] for c in chunks).lower()
        assert "force" in contents or "newton" in contents

    def test_knowledge_nodes_extend_topics(self):
        scope = {
            "scope_level": "strict",
            "knowledge_nodes": [{"concept": "momentum"}, {"title": "velocity"}],
        }
        chunks = retrieve_teacher_knowledge("momentum?", scope, top_k=3)
        assert len(chunks) >= 1
        contents = " ".join(c["content"] for c in chunks).lower()
        assert "momentum" in contents

    def test_related_curriculum_nodes_used(self):
        scope = {
            "scope_level": "moderate",
            "related_curriculum_nodes": ["acceleration", "F=ma"],
        }
        chunks = retrieve_teacher_knowledge("acceleration", scope, top_k=3)
        assert len(chunks) >= 1
        contents = " ".join(c["content"] for c in chunks).lower()
        assert "acceleration" in contents or "f=ma" in contents

    def test_respects_top_k(self):
        scope = {
            "curriculum_topics": ["a", "b", "c", "d", "e", "f"],
            "knowledge_nodes": [],
        }
        chunks = retrieve_teacher_knowledge("x", scope, top_k=2)
        assert len(chunks) <= 2

    def test_query_matching_preferred(self):
        scope = {"curriculum_topics": ["force", "momentum", "energy"]}
        chunks = retrieve_teacher_knowledge("What is force?", scope, top_k=3)
        assert len(chunks) >= 1
        # First chunk(s) should be about force when it matches query
        first_content = chunks[0]["content"].lower()
        assert "force" in first_content
