"""Contract tests verifying the Companion's shared memory interactions.

These tests ensure the Companion side of the memory collaboration contract
is honoured: correct namespaces, read/write isolation, and update semantics.

Anchored to: COMPANION_PRD §3, DEVELOPER_GUIDE §3.
"""

import pytest

from memory.shared import NAMESPACES, shared_memory

pytestmark = pytest.mark.contract

COMPANION_NAMESPACES = {
    "student_cognitive_models",
    "teacher_authority_graph",
    "interaction_episodes",
}


class TestNamespaceDeclarations:

    def test_companion_namespaces_declared(self):
        """All namespaces used by Companion must be declared in NAMESPACES."""
        for ns in COMPANION_NAMESPACES:
            assert ns in NAMESPACES, f"Namespace '{ns}' missing from NAMESPACES"


class TestReadWriteContract:

    def test_read_teacher_authority_graph(self):
        """Companion can read data written to teacher_authority_graph
        (simulating an Architect write)."""
        shared_memory.write(
            "teacher_authority_graph", "session-1",
            {"scope_level": "strict", "curriculum_topics": ["calculus"]},
        )
        entry = shared_memory.read("teacher_authority_graph", "session-1")
        assert entry is not None
        assert entry["value"]["scope_level"] == "strict"

    def test_write_student_cognitive_models(self):
        """Companion can write and re-read student_cognitive_models."""
        model = {"student_id": "s1", "concepts": {"force": {"confidence": 0.5}}}
        shared_memory.write("student_cognitive_models", "s1", model)
        entry = shared_memory.read("student_cognitive_models", "s1")
        assert entry is not None
        assert entry["value"]["concepts"]["force"]["confidence"] == 0.5

    def test_write_interaction_episodes(self):
        """Companion can write to interaction_episodes."""
        shared_memory.write(
            "interaction_episodes", "ep-1",
            {"type": "interaction", "student_id": "s1", "summary": "asked about force"},
        )
        entry = shared_memory.read("interaction_episodes", "ep-1")
        assert entry is not None
        assert entry["value"]["type"] == "interaction"


class TestIsolation:

    def test_cognitive_model_isolation(self):
        """Two different student_ids have independent cognitive models."""
        shared_memory.write(
            "student_cognitive_models", "alice",
            {"student_id": "alice", "concepts": {"math": {"confidence": 0.9}}},
        )
        shared_memory.write(
            "student_cognitive_models", "bob",
            {"student_id": "bob", "concepts": {"math": {"confidence": 0.1}}},
        )
        alice = shared_memory.read("student_cognitive_models", "alice")
        bob = shared_memory.read("student_cognitive_models", "bob")
        assert alice["value"]["concepts"]["math"]["confidence"] == 0.9
        assert bob["value"]["concepts"]["math"]["confidence"] == 0.1

    def test_read_nonexistent_returns_none(self):
        """Reading a key that doesn't exist returns None, not an exception."""
        result = shared_memory.read("student_cognitive_models", "ghost-student")
        assert result is None


class TestUpdateSemantics:

    def test_update_preserves_other_fields(self):
        """shared_memory.update() patches value without losing existing fields."""
        shared_memory.write(
            "student_cognitive_models", "s-patch",
            {"student_id": "s-patch", "concepts": {}, "extra_field": "keep_me"},
        )
        shared_memory.update(
            "student_cognitive_models", "s-patch",
            {"concepts": {"force": {"confidence": 0.5}}},
        )
        entry = shared_memory.read("student_cognitive_models", "s-patch")
        assert entry["value"]["extra_field"] == "keep_me"
        assert entry["value"]["concepts"]["force"]["confidence"] == 0.5
