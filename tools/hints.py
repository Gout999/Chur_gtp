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
_NON_SOCRATIC_STRATEGIES: List[str] = ["decompose", "analogy", "confront"]

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


_DIRECT_ANSWER_PATTERNS = [
    "the answer is",
    "the solution is",
    "the formula is",
    "the correct answer",
    "here is the answer",
    "the result is",
]


def _contains_direct_answer(text: str) -> bool:
    """Return True if the text appears to contain a direct answer."""
    text_lower = text.lower()
    return any(pattern in text_lower for pattern in _DIRECT_ANSWER_PATTERNS)


# ---------------------------------------------------------------------------
# Strategy selection
# ---------------------------------------------------------------------------

def _select_strategy(
    error_analysis: Dict[str, Any],
    concept_entry: Dict[str, Any],
) -> str:
    """Pick a hint strategy, auto-switching when the same one keeps failing.

    The node may inject ``effective_consecutive_errors`` into error_analysis
    to account for the current (not-yet-persisted) interaction.  This takes
    precedence over the stored ``consecutive_errors`` in the concept entry.
    """
    base = _ERROR_TYPE_TO_STRATEGY.get(
        error_analysis.get("type", ""),
        "socratic",
    )

    consecutive = error_analysis.get(
        "effective_consecutive_errors",
        concept_entry.get("consecutive_errors", 0),
    )
    last = concept_entry.get("last_strategy")

    if consecutive >= _STRATEGY_AUTO_SWITCH_THRESHOLD:
        err_type = error_analysis.get("type", "")

        # In persistent conceptual/misconception cases, prefer contradiction-
        # based guidance to break repeated incorrect mental models.
        if err_type == "misconception" or (
            err_type == "conceptual" and last == "socratic"
        ):
            if last != "confront":
                logger.info(
                    "Auto-switching strategy from %s to confront "
                    "(error_type=%s, consecutive_errors=%d)",
                    last, err_type, consecutive,
                )
            return "confront"

        if err_type == "conceptual" and last in _NON_SOCRATIC_STRATEGIES:
            idx = _NON_SOCRATIC_STRATEGIES.index(last)
            nxt = _NON_SOCRATIC_STRATEGIES[
                (idx + 1) % len(_NON_SOCRATIC_STRATEGIES)
            ]
            logger.info(
                "Auto-rotating conceptual strategy from %s to %s "
                "(consecutive_errors=%d)",
                last, nxt, consecutive,
            )
            return nxt

        if last is not None and (base == last or err_type == ""):
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

_MAX_FOLLOW_UP_QUESTIONS = 2

_HINT_SYSTEM_PROMPT = """\
You are a Socratic teaching assistant. Generate a hint for a student who is \
struggling with a concept. You must NEVER reveal the answer directly.

CRITICAL: The student should see at most 2 questions total (better experience).
- hint_content: One to three short STATEMENTS only. No question sentences here. \
  Use only declarative sentences (facts, suggestions, or framing). Do NOT put \
  any "Can you...?", "What...?", "How...?" in hint_content.
- follow_up_questions: Put ALL questions here. Use exactly 0, 1, or 2 questions \
  (no more than 2). These are the only questions the student will see.
- Prefer hint_content of 2–4 sentences so the reply feels complete and helpful.

Strategy to use: {strategy}
- socratic: Statements that frame the concept. Questions only in follow_up_questions.
- analogy: Statements about a familiar analogy or mapping. Questions only in follow_up_questions.
- decompose: Statements about the first sub-step. Questions only in follow_up_questions.
- confront: Statements about a scenario or contradiction. Questions only in follow_up_questions.

Respond in JSON:
{{"hint_content": "...", "follow_up_questions": ["q1", "q2"], "expected_response_type": "explanation|calculation|verification"}}
"""

# hint_content = 陈述句 only，可稍长（2–4 句）；追问全部放在 follow_up_questions（最多 2 个）
_TEMPLATE_HINTS: Dict[str, str] = {
    "socratic": (
        "我们一步一步来想。你刚才提到「{input_snippet}」，这和「{concept}」有关。"
        "先理清你目前对它的理解，再对照一下定义或公式，会更容易发现哪里需要调整。"
    ),
    "decompose": (
        "这道题可以拆成几步来做。先搞清楚「{concept}」的定义和适用条件，"
        "再往下推会容易很多。你可以先写出第一步，再想下一步。"
    ),
    "analogy": (
        "「{concept}」可以类比成生活中的情境。"
        "想一个你熟悉的现象，和它的行为很像，用这个类比来对照你刚才的想法，会帮助理解。"
    ),
    "confront": (
        "你刚才说「{input_snippet}」。"
        "可以试想：如果这样成立，在另一种情形下会怎样？看看你的推理是否还成立。"
        "这样能帮你发现哪里需要修正。"
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
    teacher_knowledge_chunks: Optional[List[Dict[str, Any]]] = None,
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

    knowledge_block = ""
    if teacher_knowledge_chunks:
        lines = [
            f"- {c.get('content', '')} [source: {c.get('source', '')}]"
            for c in teacher_knowledge_chunks
        ]
        knowledge_block = (
            "\nBase your hint ONLY on the following teacher knowledge. "
            "Do not invent facts outside these snippets:\n"
            + "\n".join(lines)
            + "\n\n"
        )

    user_msg = (
        knowledge_block
        + f"Concept: {target_concept}\n"
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
            max_tokens=520,
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
    teacher_knowledge_chunks: Optional[List[Dict[str, Any]]] = None,
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
        teacher_knowledge_chunks=teacher_knowledge_chunks,
    )
    if llm_result is not None and not _contains_direct_answer(
        llm_result.get("hint_content", ""),
    ):
        hint_content = llm_result["hint_content"]
        raw_follow_ups = llm_result.get("follow_up_questions") or []
        if isinstance(raw_follow_ups, str):
            raw_follow_ups = [raw_follow_ups] if raw_follow_ups else []
        follow_ups = list(raw_follow_ups)[: _MAX_FOLLOW_UP_QUESTIONS]
        resp_type = llm_result.get("expected_response_type", "explanation")
    else:
        if llm_result is not None:
            logger.warning(
                "LLM hint contained a direct answer; falling back to template",
            )
        tmpl = _template_hint(strategy, current_input, target_concept)
        hint_content = tmpl["hint_content"]
        follow_ups = tmpl["follow_up_questions"][: _MAX_FOLLOW_UP_QUESTIONS]
        resp_type = tmpl["expected_response_type"]

    confidence = concept_entry.get("confidence", 0.5)
    difficulty = _difficulty_from_confidence(confidence)

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
    "frustration": (
        "这道题确实不容易，卡住很正常。"
        "我已经帮你联系老师了，老师会来和你一起看的。"
    ),
    "repeated_failure": (
        "这个问题确实有难度，你已经很努力了。"
        "我已经通知老师来帮助你了，老师很快就会来。"
    ),
    "out_of_scope": (
        "这个问题很有深度，目前课程里还没讲到。"
        "我帮你记下来了，老师回头会给你解答的。"
    ),
    "emotional_distress": (
        "没关系，学习就是一步步来的，有情绪很正常。"
        "老师很快会来和你聊聊，会帮你的。"
    ),
}

_URGENCY_RESPONSE_TIMES: Dict[str, str] = {
    "low": "within 24 hours",
    "medium": "within a few hours",
    "high": "as soon as possible",
}


_VALID_REASONS = frozenset(_ESCALATION_MESSAGES.keys())
_VALID_URGENCIES = frozenset(_URGENCY_RESPONSE_TIMES.keys())


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
    if reason not in _VALID_REASONS:
        logger.warning(
            "Invalid escalation reason '%s'; defaulting to 'frustration'",
            reason,
        )
        reason = "frustration"

    if urgency not in _VALID_URGENCIES:
        logger.warning(
            "Invalid urgency '%s'; defaulting to 'medium'",
            urgency,
        )
        urgency = "medium"

    escalation_id = f"esc_{uuid4().hex[:12]}"
    now = _utc_iso()
    student_message = _ESCALATION_MESSAGES[reason]
    estimated = _URGENCY_RESPONSE_TIMES[urgency]

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
