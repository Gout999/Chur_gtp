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

COMPANION_NAMESPACES_INCLUDING_RUNTIME = COMPANION_NAMESPACES | {
    "cognition_snapshots",
    "pending_escalations",
}


class TestNamespaceDeclarations:

    def test_companion_namespaces_declared(self):
        """All namespaces used by Companion must be declared in NAMESPACES."""
        for ns in COMPANION_NAMESPACES:
            assert ns in NAMESPACES, f"Namespace '{ns}' missing from NAMESPACES"

    def test_cognition_snapshots_declared(self):
        """cognition_snapshots is used by the cognition tool's archive writer
        and should be formally declared in the shared NAMESPACES dict."""
        assert "cognition_snapshots" in NAMESPACES


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


class TestCognitionSnapshotContract:
    """Tests for the cognition_snapshots namespace used by _archive_snapshot.
    The namespace is auto-created via _ensure_namespace; these tests verify
    the snapshot schema matches PRD §3.1."""

    def test_snapshot_written_with_correct_schema(self):
        """Archive snapshot must contain belief_mass, uncertainty, and
        standard identifiers."""
        from tools.cognition import update_student_cognition_map

        update_student_cognition_map("s-snap", {
            "concept": "force",
            "student_response": "F = ma",
            "is_correct": True,
            "time_spent": 10.0,
            "help_requests": 0,
        })
        entries = shared_memory.read_all("cognition_snapshots")
        assert len(entries) >= 1

        snap = entries[0]["value"]
        assert snap["type"] == "cognition_snapshot"
        assert snap["student_id"] == "s-snap"
        assert snap["concept_id"] == "force"
        assert 0.0 <= snap["belief_mass"] <= 1.0
        assert 0.0 <= snap["uncertainty"] <= 1.0
        assert snap["belief_mass"] + snap["uncertainty"] == pytest.approx(1.0, abs=0.01)


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
