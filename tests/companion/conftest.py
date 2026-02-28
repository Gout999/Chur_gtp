"""Shared fixtures for the Companion test suite.

Provides:
- fresh_memory     -- autouse; resets the in-memory shared store before each test
- seed_authority_graph   -- factory: writes a teacher_authority_graph entry
- seed_cognitive_model   -- factory: pre-populates a student's cognitive model
- make_state             -- factory: returns a valid EduGuideState dict
- make_interaction_data  -- factory: returns an interaction_data dict
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from memory.shared import _STORE, NAMESPACES, shared_memory  # noqa: E402


# ---------------------------------------------------------------------------
# Marker registration
# ---------------------------------------------------------------------------

def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit-level tests")
    config.addinivalue_line("markers", "integration: Integration-level tests")
    config.addinivalue_line("markers", "scenario: Multi-turn scenario tests")
    config.addinivalue_line("markers", "contract: Memory contract tests")
    config.addinivalue_line("markers", "behavioral: PRD behavioral contract tests")


# ---------------------------------------------------------------------------
# Memory isolation
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def fresh_memory():
    """Reset the global in-memory store so every test starts clean."""
    for ns in list(_STORE.keys()):
        _STORE[ns].clear()
    for ns in NAMESPACES:
        _STORE.setdefault(ns, {})
    yield
    for ns in list(_STORE.keys()):
        _STORE[ns].clear()
    for ns in NAMESPACES:
        _STORE.setdefault(ns, {})


# ---------------------------------------------------------------------------
# Seed helpers (factory fixtures)
# ---------------------------------------------------------------------------

@pytest.fixture
def seed_authority_graph():
    """Return a factory that writes a teacher_authority_graph entry."""

    def _seed(
        scope_level: str = "moderate",
        session_id: str = "test-session",
        curriculum_topics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        value = {
            "scope_level": scope_level,
            "curriculum_topics": curriculum_topics or [
                "newton_second_law", "force", "momentum",
            ],
            "knowledge_nodes": [
                {"concept": "newton_second_law", "difficulty": 0.5},
                {"concept": "force", "difficulty": 0.3},
                {"concept": "momentum", "difficulty": 0.6},
            ],
            "validity_constraints": {},
            "updated_by": "pedagogical_architect",
        }
        shared_memory.write("teacher_authority_graph", session_id, value)
        return value

    return _seed


@pytest.fixture
def seed_cognitive_model():
    """Return a factory that pre-populates a student cognitive model."""

    def _seed(
        student_id: str = "stu-1",
        concepts: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        model = {
            "student_id": student_id,
            "concepts": concepts or {},
            "misconceptions": [],
            "learning_style_preferences": {"preferred_strategy": None},
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
        shared_memory.write("student_cognitive_models", student_id, model)
        return model

    return _seed


# ---------------------------------------------------------------------------
# State / data factories (factory fixtures)
# ---------------------------------------------------------------------------

@pytest.fixture
def make_state():
    """Return a factory that builds a valid EduGuideState dict."""

    def _factory(**overrides: Any) -> Dict[str, Any]:
        base: Dict[str, Any] = {
            "event_type": "student_message",
            "event_payload": {
                "student_id": "stu-test",
                "content": "I think force equals mass times velocity",
                "target_concept": "newton_second_law",
                "is_correct": False,
                "time_spent": 20.0,
                "help_requests": 0,
            },
            "current_agent": "",
            "agent_decision": "",
            "tools_to_call": [],
            "working_memory": {},
            "response_to_student": None,
            "response_to_teacher": None,
            "notifications": [],
            "session_id": "test-session",
            "timestamp": "2024-01-01T00:00:00",
            "loop_count": 0,
        }
        if "event_payload" in overrides:
            base["event_payload"].update(overrides.pop("event_payload"))
        base.update(overrides)
        return base

    return _factory


@pytest.fixture
def make_interaction_data():
    """Return a factory that builds an interaction_data dict."""

    def _factory(**overrides: Any) -> Dict[str, Any]:
        base: Dict[str, Any] = {
            "concept": "newton_second_law",
            "student_response": "force = mass * velocity",
            "is_correct": False,
            "time_spent": 20.0,
            "help_requests": 0,
        }
        base.update(overrides)
        return base

    return _factory
