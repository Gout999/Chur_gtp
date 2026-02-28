"""
update_student_cognition_map: update student cognitive model from interaction.

Uses a Dempster-Shafer inspired heuristic to update per-concept confidence
based on correctness, response speed, and help requests.  Persists the
updated model to shared memory and writes an archive snapshot.

PRD section 2.2.2; Phase 3 (Engineer B).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from memory.shared import shared_memory
from tools.base import tool

logger = logging.getLogger("eduguide.tools.cognition")

_NS_COGNITIVE = "student_cognitive_models"
_NS_EPISODES = "interaction_episodes"
_NS_SNAPSHOTS = "cognition_snapshots"

FAST_RESPONSE_THRESHOLD = 30.0  # seconds

# D-S heuristic confidence deltas
_DELTA_CORRECT_FAST = 0.20
_DELTA_CORRECT_SLOW = 0.05
_DELTA_INCORRECT = -0.15

_CONFIDENCE_FLOOR = 0.0
_CONFIDENCE_CEIL = 1.0

_LOW_CONFIDENCE_THRESHOLD = 0.4


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp(value: float, lo: float = _CONFIDENCE_FLOOR, hi: float = _CONFIDENCE_CEIL) -> float:
    return max(lo, min(hi, value))


def _empty_concept_entry() -> Dict[str, Any]:
    """Default entry for a concept the student has never interacted with."""
    return {
        "confidence": 0.0,
        "consecutive_errors": 0,
        "total_attempts": 0,
        "last_strategy": None,
        "last_updated": _utc_iso(),
    }


def _init_model(student_id: str) -> Dict[str, Any]:
    """Bootstrap a blank cognitive model for a new student."""
    now = _utc_iso()
    return {
        "student_id": student_id,
        "concepts": {},
        "misconceptions": [],
        "learning_style_preferences": {"preferred_strategy": None},
        "created_at": now,
        "updated_at": now,
    }


def _load_model(student_id: str) -> Dict[str, Any]:
    """Read existing model from shared memory, or create a blank one."""
    entry = shared_memory.read(_NS_COGNITIVE, student_id)
    if entry is not None:
        return entry.get("value", _init_model(student_id))
    return _init_model(student_id)


def _compute_delta(is_correct, time_spent: float, help_requests: int) -> float:
    """
    Dempster-Shafer inspired evidence weighting.

    Positive evidence (correct answer) strength is modulated by speed and
    independence.  Negative evidence (incorrect) applies a fixed penalty so
    misconceptions are surfaced quickly.  When ``is_correct`` is ``None``
    (correctness unknown), a neutral delta of 0.0 is returned.
    """
    if is_correct is None:
        return 0.0
    if is_correct:
        if time_spent <= FAST_RESPONSE_THRESHOLD and help_requests == 0:
            return _DELTA_CORRECT_FAST
        return _DELTA_CORRECT_SLOW
    return _DELTA_INCORRECT


_KNOWN_CONCEPT_ALIASES: Dict[str, List[str]] = {
    "force": ["momentum", "energy", "velocity", "acceleration", "weight", "mass"],
    "momentum": ["force", "energy", "velocity", "impulse"],
    "velocity": ["speed", "acceleration", "displacement"],
    "acceleration": ["velocity", "speed", "force"],
    "energy": ["force", "power", "work", "momentum"],
    "work": ["energy", "power", "force"],
    "power": ["energy", "work", "force"],
    "mass": ["weight", "force", "density"],
    "weight": ["mass", "force", "gravity"],
}


def _infer_misconception_pattern(concept: str, student_response: str) -> str:
    """
    Produce a descriptive misconception pattern by checking whether the
    student's response mentions a commonly confused sibling concept.

    Falls back to ``incorrect_on_{concept}`` when no specific confusion is
    detected.
    """
    response_lower = student_response.lower()
    concept_lower = concept.lower()

    for base, siblings in _KNOWN_CONCEPT_ALIASES.items():
        if base in concept_lower:
            for sibling in siblings:
                if sibling in response_lower and sibling not in concept_lower:
                    return f"confuses_{concept}_and_{sibling}"

    tokens = set(response_lower.split())
    for base, siblings in _KNOWN_CONCEPT_ALIASES.items():
        for sibling in siblings:
            if sibling in tokens and sibling not in concept_lower and base in concept_lower:
                return f"confuses_{concept}_and_{sibling}"

    return f"incorrect_on_{concept}"


def _detect_misconception(
    concept: str,
    student_response: str,
    is_correct: bool,
) -> Dict[str, Any] | None:
    """Return a misconception record when the student answered incorrectly."""
    if is_correct:
        return None
    return {
        "concept": concept,
        "student_response": student_response,
        "pattern": _infer_misconception_pattern(concept, student_response),
        "timestamp": _utc_iso(),
    }


def _persist_model(student_id: str, model: Dict[str, Any]) -> None:
    """Write the updated cognitive model back to shared memory."""
    shared_memory.write(_NS_COGNITIVE, student_id, model)


def _archive_snapshot(
    student_id: str,
    concept: str,
    concept_data: Dict[str, Any],
) -> None:
    """Write a snapshot for the updated concept (PRD §3.1 cognition_snapshots)."""
    now = _utc_iso()
    confidence = concept_data.get("confidence", 0.0)
    snapshot_key = f"{student_id}:{concept}:{now}"
    shared_memory.write(_NS_SNAPSHOTS, snapshot_key, {
        "type": "cognition_snapshot",
        "student_id": student_id,
        "concept_id": concept,
        "belief_mass": confidence,
        "uncertainty": round(1.0 - confidence, 4),
        "last_updated": now,
    })


@tool("update_student_cognition_map")
def update_student_cognition_map(
    student_id: str,
    interaction_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update a student's cognitive model after an interaction using D-S
    heuristic belief updating.

    Args:
        student_id: Unique student identifier.
        interaction_data: {
            "concept": str,
            "student_response": str,
            "is_correct": bool,
            "time_spent": float,   # seconds
            "help_requests": int
        }

    Returns:
        {
            "updated_concepts": List[str],
            "new_misconceptions": List[Dict],
            "confidence_changes": Dict[str, float],
            "recommended_focus_areas": List[str]
        }
    """
    concept: str = interaction_data.get("concept", "unknown_concept")
    student_response: str = interaction_data.get("student_response", "")
    is_correct = interaction_data.get("is_correct")  # None when unknown
    time_spent: float = float(interaction_data.get("time_spent", 0.0))
    help_requests: int = int(interaction_data.get("help_requests", 0))
    hint_strategy: str | None = interaction_data.get("hint_strategy")

    model = _load_model(student_id)
    concepts: Dict[str, Any] = model.setdefault("concepts", {})
    misconceptions: List[Dict[str, Any]] = model.setdefault("misconceptions", [])

    if concept not in concepts:
        concepts[concept] = _empty_concept_entry()

    entry = concepts[concept]
    old_confidence = entry["confidence"]

    delta = _compute_delta(is_correct, time_spent, help_requests)
    new_confidence = _clamp(old_confidence + delta)
    entry["confidence"] = new_confidence
    entry["total_attempts"] = entry.get("total_attempts", 0) + 1
    entry["last_updated"] = _utc_iso()

    if hint_strategy is not None:
        entry["last_strategy"] = hint_strategy

    if is_correct is True:
        entry["consecutive_errors"] = 0
    elif is_correct is False:
        entry["consecutive_errors"] = entry.get("consecutive_errors", 0) + 1

    new_misconceptions: List[Dict[str, Any]] = []
    if is_correct is False:
        misconception = _detect_misconception(concept, student_response, is_correct)
        if misconception is not None:
            misconceptions.append(misconception)
            new_misconceptions.append(misconception)

    if is_correct and (time_spent > FAST_RESPONSE_THRESHOLD or help_requests > 0):
        prefs = model.setdefault("learning_style_preferences", {})
        prefs["shaky_concepts"] = list(
            set(prefs.get("shaky_concepts", [])) | {concept}
        )

    model["updated_at"] = _utc_iso()

    _persist_model(student_id, model)
    _archive_snapshot(student_id, concept, entry)

    confidence_changes: Dict[str, float] = {
        concept: round(delta, 4),
    }

    recommended_focus: List[str] = []
    for c_name, c_data in concepts.items():
        if c_data.get("confidence", 0.0) < _LOW_CONFIDENCE_THRESHOLD:
            recommended_focus.append(c_name)
    if is_correct is False and concept not in recommended_focus:
        recommended_focus.append(concept)

    logger.info(
        "Cognition update student=%s concept=%s correct=%s delta=%.2f conf=%.2f→%.2f",
        student_id, concept, is_correct, delta, old_confidence, new_confidence,
    )

    return {
        "updated_concepts": [concept],
        "new_misconceptions": new_misconceptions,
        "confidence_changes": confidence_changes,
        "recommended_focus_areas": recommended_focus,
    }
