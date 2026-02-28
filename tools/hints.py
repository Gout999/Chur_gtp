"""
Companion tools: construct_hint and escalate_to_human.

construct_hint builds personalized hints using the student's cognitive model
and (optionally) an LLM to generate strategy-appropriate guidance.

escalate_to_human is an MVP stub that logs an escalation event, persists it
to shared memory, and returns a comforting message to the student.

PRD section 2.2.2; Phase 3 (Engineer B).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from memory.shared import shared_memory
from tools.base import tool

logger = logging.getLogger("eduguide.tools.hints")

_NS_COGNITIVE = "student_cognitive_models"
_NS_EPISODES = "interaction_episodes"
_NS_ESCALATIONS = "pending_escalations"

_STRATEGIES: List[str] = ["socratic", "decompose", "analogy", "confront"]

_ERROR_TYPE_TO_STRATEGY: Dict[str, str] = {
    "conceptual": "socratic",
    "calculation": "decompose",
    "vocabulary": "analogy",
    "misconception": "confront",
}

_STRATEGY_AUTO_SWITCH_THRESHOLD = 3


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Cognitive model helpers
# ---------------------------------------------------------------------------

def _load_cognitive_model(student_id: str) -> Dict[str, Any]:
    """Read the full cognitive model from shared memory (single read)."""
    entry = shared_memory.read(_NS_COGNITIVE, student_id)
    if entry is None:
        return {}
    return entry.get("value", {})


def _update_last_strategy(
    model: Dict[str, Any],
    student_id: str,
    concept: str,
    strategy: str,
) -> None:
    """Write the chosen strategy back so cognition tracking stays current."""
    if not model:
        return
    concepts = model.get("concepts", {})
    if concept in concepts:
        concepts[concept]["last_strategy"] = strategy
        model["updated_at"] = _utc_iso()
        shared_memory.write(_NS_COGNITIVE, student_id, model)


# ---------------------------------------------------------------------------
# Strategy selection
# ---------------------------------------------------------------------------

def _select_strategy(
    error_analysis: Dict[str, Any],
    concept_entry: Dict[str, Any],
) -> str:
    """Pick a hint strategy, auto-switching when the same one keeps failing."""
    base = _ERROR_TYPE_TO_STRATEGY.get(
        error_analysis.get("type", ""),
        "socratic",
    )

    consecutive = concept_entry.get("consecutive_errors", 0)
    last = concept_entry.get("last_strategy")

    if consecutive >= _STRATEGY_AUTO_SWITCH_THRESHOLD and last is not None:
        try:
            idx = _STRATEGIES.index(last)
        except ValueError:
            idx = 0
        base = _STRATEGIES[(idx + 1) % len(_STRATEGIES)]
        logger.info(
            "Auto-switching strategy from %s to %s (consecutive_errors=%d)",
            last, base, consecutive,
        )

    return base


# ---------------------------------------------------------------------------
# Difficulty from confidence
# ---------------------------------------------------------------------------

def _difficulty_from_confidence(confidence: float) -> float:
    """Lower student confidence -> easier hint (lower difficulty value)."""
    return round(max(0.1, min(1.0, confidence)), 2)


# ---------------------------------------------------------------------------
# LLM hint generation with template fallback
# ---------------------------------------------------------------------------

_HINT_SYSTEM_PROMPT = """\
You are a Socratic teaching assistant. Generate a hint for a student who is \
struggling with a concept. You must NEVER reveal the answer directly.

Strategy to use: {strategy}
- socratic: Ask probing questions that guide the student to discover the answer.
- analogy: Use a familiar analogy to bridge the gap.
- decompose: Break the problem into smaller, manageable steps.
- confront: Present a contradiction in the student's reasoning to provoke self-correction.

Respond in JSON:
{{"hint_content": "...", "follow_up_questions": ["q1", "q2"], "expected_response_type": "explanation|calculation|verification"}}
"""

_TEMPLATE_HINTS: Dict[str, str] = {
    "socratic": (
        "Let's think about this step by step. "
        "What do you already know about '{concept}'? "
        "How does that relate to what you just said: '{input_snippet}'?"
    ),
    "decompose": (
        "This is a complex question — let's break it down. "
        "First, can you tell me the definition of '{concept}'? "
        "Once we nail that, we'll tackle the next piece."
    ),
    "analogy": (
        "Imagine '{concept}' is like something from everyday life. "
        "Can you think of a real-world situation that behaves the same way? "
        "How would you explain it to a friend?"
    ),
    "confront": (
        "You said: '{input_snippet}'. "
        "But consider this: if that were true, what would happen in "
        "the following scenario? Think about whether your reasoning still holds."
    ),
}

_TEMPLATE_FOLLOWUPS: Dict[str, List[str]] = {
    "socratic": [
        "What assumption are you making about {concept}?",
        "Which part of your reasoning are you most confident about, and why?",
    ],
    "decompose": [
        "What is the first sub-step you need to solve?",
        "Can you identify which part is causing the confusion?",
    ],
    "analogy": [
        "How is {concept} similar to the analogy you picked?",
        "Where does the analogy break down?",
    ],
    "confront": [
        "Does your original answer still make sense given this contradiction?",
        "What would you change in your reasoning?",
    ],
}


def _llm_generate_hint(
    strategy: str,
    current_input: str,
    target_concept: str,
    error_analysis: Dict[str, Any],
    misconceptions: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Try generating a hint via OpenAI. Returns None on any failure."""
    try:
        from config import OPENAI_API_KEY
        if not OPENAI_API_KEY:
            return None
        from openai import OpenAI  # type: ignore[import-untyped]
    except Exception:
        return None

    relevant = [m for m in misconceptions if m.get("concept") == target_concept]
    misconception_text = "; ".join(
        m.get("pattern", "") for m in relevant[-3:]
    ) or "none recorded"

    user_msg = (
        f"Concept: {target_concept}\n"
        f"Student said: {current_input}\n"
        f"Error analysis: {json.dumps(error_analysis, ensure_ascii=False)}\n"
        f"Known misconceptions: {misconception_text}"
    )

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _HINT_SYSTEM_PROMPT.format(strategy=strategy)},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        if "hint_content" in data:
            return data
    except Exception:
        logger.warning("LLM hint generation failed; falling back to template", exc_info=True)

    return None


def _template_hint(
    strategy: str,
    current_input: str,
    target_concept: str,
) -> Dict[str, Any]:
    """Deterministic template-based hint as fallback."""
    snippet = current_input[:80]
    content = _TEMPLATE_HINTS.get(strategy, _TEMPLATE_HINTS["socratic"]).format(
        concept=target_concept,
        input_snippet=snippet,
    )
    followups = [
        q.format(concept=target_concept)
        for q in _TEMPLATE_FOLLOWUPS.get(strategy, _TEMPLATE_FOLLOWUPS["socratic"])
    ]
    return {
        "hint_content": content,
        "follow_up_questions": followups,
        "expected_response_type": "explanation",
    }


# ---------------------------------------------------------------------------
# construct_hint
# ---------------------------------------------------------------------------

@tool("construct_hint")
def construct_hint(
    student_id: str,
    current_input: str,
    target_concept: str,
    error_analysis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a personalised hint based on error patterns and student profile.

    Reads the student's cognitive model to inform strategy selection and
    auto-switches strategy when the same concept has >= 3 consecutive errors
    under the same strategy.

    Returns:
        {
            "hint_id": str,
            "student_id": str,
            "strategy": "socratic" | "analogy" | "decompose" | "confront",
            "hint_content": str,
            "follow_up_questions": List[str],
            "difficulty_level": float,
            "expected_response_type": "explanation" | "calculation" | "verification"
        }
    """
    analysis = error_analysis or {}

    cog_model = _load_cognitive_model(student_id)
    concept_entry = cog_model.get("concepts", {}).get(target_concept, {})
    misconceptions = cog_model.get("misconceptions", [])

    strategy = _select_strategy(analysis, concept_entry)

    llm_result = _llm_generate_hint(
        strategy, current_input, target_concept, analysis, misconceptions,
    )
    if llm_result is not None:
        hint_content = llm_result["hint_content"]
        follow_ups = llm_result.get("follow_up_questions", [])
        resp_type = llm_result.get("expected_response_type", "explanation")
    else:
        tmpl = _template_hint(strategy, current_input, target_concept)
        hint_content = tmpl["hint_content"]
        follow_ups = tmpl["follow_up_questions"]
        resp_type = tmpl["expected_response_type"]

    confidence = concept_entry.get("confidence", 0.5)
    difficulty = _difficulty_from_confidence(confidence)

    _update_last_strategy(cog_model, student_id, target_concept, strategy)

    logger.info(
        "construct_hint student=%s concept=%s strategy=%s difficulty=%.2f",
        student_id, target_concept, strategy, difficulty,
    )

    return {
        "hint_id": f"hint_{uuid4().hex[:12]}",
        "student_id": student_id,
        "strategy": strategy,
        "hint_content": hint_content,
        "follow_up_questions": follow_ups,
        "difficulty_level": difficulty,
        "expected_response_type": resp_type,
    }


# ---------------------------------------------------------------------------
# escalate_to_human
# ---------------------------------------------------------------------------

_ESCALATION_MESSAGES: Dict[str, str] = {
    "frustration": "我理解你现在有点困惑，让我帮你联系老师来一起看看。",
    "repeated_failure": "这个问题确实有难度，我已经通知老师来帮助你了。",
    "out_of_scope": "这个问题超出了当前课程范围，我帮你记下来让老师回头解答。",
    "emotional_distress": "没关系，学习就是一步步来的，老师很快会来和你聊聊。",
}

_URGENCY_RESPONSE_TIMES: Dict[str, str] = {
    "low": "within 24 hours",
    "medium": "within a few hours",
    "high": "as soon as possible",
}


@tool("escalate_to_human")
def escalate_to_human(
    student_id: str,
    reason: str,
    context_summary: str,
    urgency: str = "medium",
) -> Dict[str, Any]:
    """
    Request human teacher intervention (MVP stub).

    Logs the escalation, persists it to shared memory for future teacher
    dashboard integration, and returns a comforting message to the student.

    Args:
        student_id: Unique student identifier.
        reason: One of "frustration", "repeated_failure", "out_of_scope",
                "emotional_distress".
        context_summary: Brief description of the situation.
        urgency: "low" | "medium" | "high".

    Returns:
        {
            "escalation_id": str,
            "teacher_notification_sent": bool,
            "estimated_response_time": str,
            "student_message": str
        }
    """
    escalation_id = f"esc_{uuid4().hex[:12]}"
    now = _utc_iso()
    student_message = _ESCALATION_MESSAGES.get(
        reason,
        "老师很快会来帮助你，请稍等。",
    )
    estimated = _URGENCY_RESPONSE_TIMES.get(urgency, "within a few hours")

    escalation_record = {
        "escalation_id": escalation_id,
        "student_id": student_id,
        "reason": reason,
        "context_summary": context_summary,
        "urgency": urgency,
        "status": "pending",
        "created_at": now,
    }

    shared_memory.write(_NS_ESCALATIONS, escalation_id, escalation_record)

    shared_memory.write(_NS_EPISODES, f"escalation:{escalation_id}", {
        "type": "escalation",
        "student_id": student_id,
        "reason": reason,
        "urgency": urgency,
        "context_summary": context_summary,
        "timestamp": now,
    })

    logger.info(
        "Escalation student=%s reason=%s urgency=%s id=%s",
        student_id, reason, urgency, escalation_id,
    )

    return {
        "escalation_id": escalation_id,
        "teacher_notification_sent": False,
        "estimated_response_time": estimated,
        "student_message": student_message,
    }
