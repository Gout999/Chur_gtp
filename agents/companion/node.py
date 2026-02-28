"""
Socratic Companion node: 5-phase ReAct loop powered by MiniMax-M2.5.

Phase 1 — Load context (cognitive model, knowledge boundary, history)
Phase 2 — LLM reasoning via MiniMax-M2.5 (Anthropic SDK), with fallback
Phase 3 — Dispatch tools based on LLM decision
Phase 4 — Update student cognitive model (every interaction)
Phase 5 — Persist interaction and return updated state

PRD section 4.1; Phase 3 (Engineer B). graph.py imports this node.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from memory.shared import shared_memory
from prompts.companion import SOCRATIC_COMPANION_PROMPT
from tools.cognition import update_student_cognition_map
from tools.hints import construct_hint, escalate_to_human

logger = logging.getLogger("eduguide.agents.companion")

State = Dict[str, Any]

_NS_COGNITIVE = "student_cognitive_models"
_NS_EPISODES = "interaction_episodes"
_NS_AUTHORITY = "teacher_authority_graph"

_MINIMAX_MODEL = "MiniMax-M2.5"
_MAX_HISTORY_EPISODES = 10

_ESCALATION_THRESHOLD = 5
_STRATEGY_SWITCH_THRESHOLD = 3
_ALL_STRATEGIES = frozenset({"socratic", "decompose", "analogy", "confront"})

_TOOL_ACTION_MAP: Dict[str, str] = {
    "construct_hint": "hint",
    "escalate_to_human": "escalate",
}

_BOUNDARY_DECLINE = (
    "That's a great question, but it's outside what we're covering right now. "
    "Let's focus on our current topic \u2014 {curriculum_hint}"
)
_BOUNDARY_BRIDGE = (
    "Interesting connection! That relates to a topic we'll cover later. "
    "For now, let's think about how {curriculum_hint} works..."
)
_BOUNDARY_PERMISSIVE = (
    "Great curiosity! Let's explore that briefly and see how it connects "
    "back to {curriculum_hint}, which is our main focus right now."
)

_DIRECT_ANSWER_PATTERNS = (
    "the answer is",
    "the solution is",
    "the formula is",
    "the correct answer",
    "here is the answer",
    "the result is",
)

_INTEREST_PROBE_PATTERNS = (
    "what are your interests",
    "what is your interest",
    "what do you want to learn",
    "what are your hobbies",
    "what is your hobby",
    "兴趣",
    "爱好",
)

_FRUSTRATION_PATTERNS = (
    "i give up",
    "this is stupid",
    "i can't do this",
    "i cant do this",
    "i am stuck",
    "i'm stuck",
    "我放弃",
    "太难了",
    "不会做",
)

_EMOTIONAL_DISTRESS_PATTERNS = (
    "i hate myself",
    "i'm worthless",
    "i am worthless",
    "i want to disappear",
    "i want to die",
    "我很痛苦",
    "我撑不住",
    "我不想活了",
)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Phase 1: Context Loading
# ---------------------------------------------------------------------------

def _load_cognitive_model(student_id: str) -> Dict[str, Any]:
    """Read student cognitive model from shared memory (empty dict if new)."""
    entry = shared_memory.read(_NS_COGNITIVE, student_id)
    if entry is None:
        return {}
    return entry.get("value", {})


def _bootstrap_cognitive_model(
    student_id: str,
    target_concept: str,
) -> Dict[str, Any]:
    """Ensure first-turn student cognition exists with default uncertainty.

    Task 8 contract: on first interaction, initialize a default cognitive
    model and set ``uncertainty=1.0`` for the target concept.
    """
    existing_model = _load_cognitive_model(student_id)
    model = existing_model
    if not existing_model:
        now = _utc_iso()
        model = {
            "student_id": student_id,
            "concepts": {},
            "misconceptions": [],
            "learning_style_preferences": {"preferred_strategy": None},
            "created_at": now,
            "updated_at": now,
        }

    concepts = model.setdefault("concepts", {})
    changed = False

    if target_concept and target_concept not in concepts:
        concepts[target_concept] = {
            "confidence": 0.0,
            "uncertainty": 1.0,
            "consecutive_errors": 0,
            "total_attempts": 0,
            "last_strategy": None,
            "last_updated": _utc_iso(),
        }
        changed = True

    if not existing_model:
        changed = True

    if changed:
        model["updated_at"] = _utc_iso()
        shared_memory.write(_NS_COGNITIVE, student_id, model)

    return model


def _load_knowledge_boundary(state: State) -> Dict[str, Any]:
    """Load the latest knowledge boundary from teacher_authority_graph.

    Tries the session-specific key first, then falls back to "global".
    Defaults to ``scope_level="moderate"`` when no boundary exists (PRD §6).
    """
    key = state.get("session_id") or "global"
    entry = shared_memory.read(_NS_AUTHORITY, key)
    if not entry and key != "global":
        entry = shared_memory.read(_NS_AUTHORITY, "global")
    if not entry:
        logger.debug("No knowledge boundary found; defaulting to moderate scope")
        return {"scope_level": "moderate"}
    value = entry.get("value", {})
    boundary = value.get("latest_boundary", value)
    if "scope_level" not in boundary:
        boundary["scope_level"] = "moderate"
    boundary.setdefault("_loaded_at", _utc_iso())
    return boundary


def _load_interaction_history(
    student_id: str,
    limit: int = _MAX_HISTORY_EPISODES,
) -> List[Dict[str, Any]]:
    """Fetch recent interaction episodes for this student.

    Filters out cognition_snapshot entries that share the namespace but
    are not actual interaction records.
    """
    entries = shared_memory.read_all(
        _NS_EPISODES,
        filter_dict={"student_id": student_id},
        limit=limit,
    )
    raw = [e.get("value", {}) for e in entries]
    return [ep for ep in raw if ep.get("type") in ("interaction", "escalation")]


# ---------------------------------------------------------------------------
# Knowledge Boundary Helpers
# ---------------------------------------------------------------------------

def _tokenize_concept(text: str) -> set[str]:
    """Normalise a concept name into a set of lowercase tokens.

    Handles underscores, hyphens, camelCase boundaries, and common
    separators so that "newton_second_law" and "Newton's Second Law"
    produce overlapping token sets.
    """
    import re
    text = text.replace("'s", "").replace("\u2019s", "").replace("'", "")
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    text = text.lower()
    text = re.sub(r"[_\-/]", " ", text)
    tokens = set(text.split())
    tokens.discard("")
    return tokens


def _concept_matches_topic(concept: str, topic: str) -> bool:
    """Return True when *concept* is semantically close enough to *topic*.

    Uses three tiers:
    1. Substring containment (original behaviour).
    2. Token overlap — if ≥50 % of concept tokens appear in the topic
       token set (or vice-versa), consider it a match.
    3. Knowledge-node concept names (handled by the caller extracting
       concept names from ``knowledge_nodes``).
    """
    c = concept.lower()
    t = topic.lower()
    if c in t or t in c:
        return True

    c_tokens = _tokenize_concept(concept)
    t_tokens = _tokenize_concept(topic)
    if not c_tokens or not t_tokens:
        return False
    overlap = c_tokens & t_tokens
    smaller = min(len(c_tokens), len(t_tokens))
    return len(overlap) / smaller >= 0.5


def _collect_curriculum_concepts(boundary: Dict[str, Any]) -> List[str]:
    """Gather all known curriculum concept names from the boundary payload.

    Merges ``curriculum_topics`` with concept names found inside
    ``knowledge_nodes`` to give a unified list of in-scope concepts.
    """
    topics: List[str] = list(boundary.get("curriculum_topics", []))
    for node in boundary.get("knowledge_nodes", []):
        name = node.get("concept", "")
        if name and name not in topics:
            topics.append(name)
    return topics


def _is_out_of_scope(target_concept: str, boundary: Dict[str, Any]) -> bool:
    """Check whether *target_concept* falls outside the curriculum boundary.

    Returns False (in-scope) when there is no boundary data, no concept to
    check, or the concept token-matches any known curriculum topic.
    """
    all_topics = _collect_curriculum_concepts(boundary)
    if not all_topics or not target_concept:
        return False
    return not any(
        _concept_matches_topic(target_concept, topic)
        for topic in all_topics
    )


def _find_closest_topic(
    target_concept: str,
    boundary: Dict[str, Any],
) -> str:
    """Return the curriculum topic with the highest token overlap to *target_concept*.

    Falls back to the first topic or a generic label.
    """
    all_topics = _collect_curriculum_concepts(boundary)
    if not all_topics:
        return "the current topic"

    if not target_concept:
        return all_topics[0]

    concept_tokens = _tokenize_concept(target_concept)
    best, best_score = all_topics[0], 0.0
    for topic in all_topics:
        t_tokens = _tokenize_concept(topic)
        if not t_tokens:
            continue
        overlap = len(concept_tokens & t_tokens)
        score = overlap / max(len(concept_tokens), len(t_tokens))
        if score > best_score:
            best, best_score = topic, score
    return best


def _boundary_response(
    scope_level: str,
    boundary: Dict[str, Any],
    target_concept: str = "",
) -> str:
    """Generate a boundary response for out-of-scope questions.

    Supports all three scope levels defined in COMPANION_LOGIC_FLOW:
    - strict   → decline
    - moderate → bridge
    - permissive → tie-back (allow exploration but redirect)
    """
    curriculum_hint = _find_closest_topic(target_concept, boundary)

    if scope_level == "strict":
        return _BOUNDARY_DECLINE.format(curriculum_hint=curriculum_hint)
    if scope_level == "moderate":
        return _BOUNDARY_BRIDGE.format(curriculum_hint=curriculum_hint)
    return _BOUNDARY_PERMISSIVE.format(curriculum_hint=curriculum_hint)


_SCOPE_PROBE_KEYWORDS: Dict[str, List[str]] = {
    "quantum": ["quantum", "量子"],
    "relativity": ["relativity", "相对论"],
    "thermodynamics": ["thermodynamics", "热力学"],
    "electromagnetism": ["electromagnetism", "electromagnetic", "电磁"],
    "optics": ["optics", "光学"],
    "chemistry": ["chemistry", "chemical", "化学"],
    "biology": ["biology", "biological", "生物"],
    "calculus": ["calculus", "微积分"],
    "statistics": ["statistics", "统计"],
    "programming": ["programming", "编程", "coding"],
}


def _detect_out_of_scope_topic(
    student_input: str,
    boundary: Dict[str, Any],
) -> Optional[str]:
    """Try to identify an out-of-scope topic mentioned in the student's text.

    Scans known broad-domain keywords against the input and checks whether
    each match is covered by the curriculum.  Returns the first detected
    out-of-scope topic name, or None if everything appears in-scope.

    This is a lightweight heuristic (no LLM call) used only as a safety net
    when the caller has no explicit ``target_concept``.
    """
    text_lower = student_input.lower()
    all_topics = _collect_curriculum_concepts(boundary)
    if not all_topics:
        return None

    for topic_key, keywords in _SCOPE_PROBE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            if not any(
                _concept_matches_topic(topic_key, t) for t in all_topics
            ):
                return topic_key
    return None


def _contains_direct_answer(text: str) -> bool:
    text_lower = text.lower()
    return any(p in text_lower for p in _DIRECT_ANSWER_PATTERNS)


def _contains_interest_probe(text: str) -> bool:
    text_lower = text.lower()
    return any(p in text_lower for p in _INTEREST_PROBE_PATTERNS)


def _detect_emotional_signal(student_input: str) -> Optional[str]:
    text_lower = student_input.lower()
    if any(p in text_lower for p in _EMOTIONAL_DISTRESS_PATTERNS):
        return "emotional_distress"
    if any(p in text_lower for p in _FRUSTRATION_PATTERNS):
        return "frustration"
    return None


# ---------------------------------------------------------------------------
# Working Memory Assembly
# ---------------------------------------------------------------------------

def _assemble_working_memory(
    student_input: str,
    cog_model: Dict[str, Any],
    boundary: Dict[str, Any],
    history: List[Dict[str, Any]],
    payload: Dict[str, Any],
    *,
    session_tracker: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """Format loaded context into a concise user message for the LLM."""
    sections: List[str] = []

    sections.append(f"## Student Input\n{student_input}")

    if cog_model:
        concepts = cog_model.get("concepts", {})
        if concepts:
            lines = []
            for name, data in concepts.items():
                conf = data.get("confidence", 0.0)
                errors = data.get("consecutive_errors", 0)
                strat = data.get("last_strategy", "none")
                lines.append(
                    f"- {name}: confidence={conf:.2f}, "
                    f"consecutive_errors={errors}, last_strategy={strat}"
                )
            sections.append("## Student Cognitive Model\n" + "\n".join(lines))

        misconceptions = cog_model.get("misconceptions", [])
        if misconceptions:
            recent = misconceptions[-5:]
            lines = [
                f"- {m.get('pattern', 'unknown')} (concept: {m.get('concept', '?')})"
                for m in recent
            ]
            sections.append("## Known Misconceptions\n" + "\n".join(lines))
    else:
        sections.append(
            "## Student Cognitive Model\n"
            "New student \u2014 no prior cognitive model available."
        )

    scope_level = boundary.get("scope_level", "moderate")
    curriculum_nodes = boundary.get("related_curriculum_nodes", [])
    boundary_text = f"Scope level: {scope_level}"
    if curriculum_nodes:
        boundary_text += (
            f"\nCurriculum nodes: {', '.join(str(n) for n in curriculum_nodes)}"
        )
    sections.append(f"## Knowledge Boundary\n{boundary_text}")

    if session_tracker:
        lines = []
        for concept, data in session_tracker.items():
            errs = data.get("consecutive_errors", 0)
            tried = data.get("strategies_tried", [])
            last = data.get("last_strategy", "none")
            lines.append(
                f"- {concept}: session_errors={errs}, "
                f"strategies_tried=[{', '.join(tried)}], last_strategy={last}"
            )
        if lines:
            sections.append(
                "## Session Error Tracker (this session)\n" + "\n".join(lines)
            )

    if history:
        lines = []
        for ep in history[-5:]:
            ep_type = ep.get("type", "interaction")
            ts = ep.get("timestamp", "?")
            if ep_type == "interaction":
                lines.append(
                    f"- [{ts}] Student: {str(ep.get('student_input', ''))[:80]} | "
                    f"Response: {str(ep.get('response', ''))[:80]}"
                )
            elif ep_type == "escalation":
                lines.append(f"- [{ts}] ESCALATION: {ep.get('reason', '?')}")
        if lines:
            sections.append("## Recent Interaction History\n" + "\n".join(lines))

    target_concept = payload.get("target_concept", "")
    if target_concept:
        sections.append(f"## Current Target Concept\n{target_concept}")

    student_id = payload.get("student_id", "unknown")
    sections.append(f"## Student ID\n{student_id}")

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Phase 2: LLM Reasoning via MiniMax-M2.5 (Anthropic SDK)
# ---------------------------------------------------------------------------

_TOOL_SCHEMAS = [
    {
        "name": "construct_hint",
        "description": (
            "Build a personalized hint for the student based on their error "
            "patterns and cognitive model. The tool handles strategy selection "
            "(socratic / analogy / decompose / confront) and auto-switching "
            "when the same strategy fails repeatedly."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Unique student identifier",
                },
                "current_input": {
                    "type": "string",
                    "description": "What the student said or asked",
                },
                "target_concept": {
                    "type": "string",
                    "description": "The concept being discussed or tested",
                },
                "error_analysis": {
                    "type": "object",
                    "description": (
                        "Analysis of the student's error, with 'type' being one "
                        "of: conceptual, calculation, vocabulary, misconception"
                    ),
                    "properties": {
                        "type": {"type": "string"},
                        "description": {"type": "string"},
                    },
                },
            },
            "required": ["student_id", "current_input", "target_concept"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Request human teacher intervention. Use when the student is "
            "frustrated, has failed >= 5 times consecutively, shows emotional "
            "distress, or the question is entirely beyond system capability."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Unique student identifier",
                },
                "reason": {
                    "type": "string",
                    "enum": [
                        "frustration",
                        "repeated_failure",
                        "out_of_scope",
                        "emotional_distress",
                    ],
                    "description": "Why escalation is needed",
                },
                "context_summary": {
                    "type": "string",
                    "description": "Brief situation description for the teacher",
                },
                "urgency": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "How urgently the teacher is needed",
                },
            },
            "required": ["student_id", "reason", "context_summary"],
        },
    },
]

_anthropic_client = None


def _get_anthropic_client():
    """Lazily initialise and return a shared Anthropic client instance."""
    global _anthropic_client
    if _anthropic_client is None:
        from config import MINIMAX_API_KEY, MINIMAX_BASE_URL
        import anthropic  # type: ignore[import-untyped]
        _anthropic_client = anthropic.Anthropic(
            api_key=MINIMAX_API_KEY,
            base_url=MINIMAX_BASE_URL,
        )
    return _anthropic_client


def _llm_reason(
    student_input: str,
    cog_model: Dict[str, Any],
    boundary: Dict[str, Any],
    history: List[Dict[str, Any]],
    payload: Dict[str, Any],
    *,
    session_tracker: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Call MiniMax-M2.5 via Anthropic SDK to reason about the student's input
    and decide which tool to call.

    Returns a decision dict on success, or None on any failure (which triggers
    the deterministic fallback in the main node).
    """
    try:
        from config import MINIMAX_API_KEY
        if not MINIMAX_API_KEY:
            return None
    except Exception:
        return None

    context_msg = _assemble_working_memory(
        student_input, cog_model, boundary, history, payload,
        session_tracker=session_tracker or {},
    )

    try:
        client = _get_anthropic_client()
        response = client.messages.create(
            model=_MINIMAX_MODEL,
            max_tokens=1024,
            system=SOCRATIC_COMPANION_PROMPT,
            tools=_TOOL_SCHEMAS,
            messages=[{"role": "user", "content": context_msg}],
        )
    except Exception:
        logger.warning(
            "MiniMax LLM call failed; falling back to deterministic",
            exc_info=True,
        )
        return None

    reasoning_parts: List[str] = []
    tool_use_blocks: List[Any] = []
    text_response = ""

    for block in response.content:
        block_type = getattr(block, "type", None)
        if block_type == "thinking":
            reasoning_parts.append(getattr(block, "thinking", ""))
        elif block_type == "tool_use":
            tool_use_blocks.append(block)
        elif block_type == "text":
            text_response = getattr(block, "text", "")
            reasoning_parts.append(text_response)

    reasoning = "\n".join(filter(None, reasoning_parts))

    if tool_use_blocks:
        escalate_block = next(
            (b for b in tool_use_blocks if b.name == "escalate_to_human"),
            None,
        )
        hint_block = next(
            (b for b in tool_use_blocks if b.name == "construct_hint"),
            None,
        )
        primary_block = escalate_block or hint_block or tool_use_blocks[0]

        action = _TOOL_ACTION_MAP.get(primary_block.name)
        if action is None:
            logger.warning(
                "LLM called unrecognised tool %s; treating as direct_response",
                primary_block.name,
            )
            return {
                "action": "direct_response",
                "reasoning": reasoning,
                "tool_params": {},
                "response_text": text_response,
            }

        return {
            "action": action,
            "reasoning": reasoning,
            "tool_params": primary_block.input,
            "response_text": text_response,
        }

    return {
        "action": "direct_response",
        "reasoning": reasoning,
        "tool_params": {},
        "response_text": text_response,
    }


# ---------------------------------------------------------------------------
# Post-LLM Guardrails (enforce Iron Rules regardless of LLM decision)
# ---------------------------------------------------------------------------

def _enforce_guardrails(
    decision: Dict[str, Any],
    student_id: str,
    student_input: str,
    target_concept: str,
    cog_model: Dict[str, Any],
    boundary: Dict[str, Any],
    is_correct: Optional[bool],
) -> Dict[str, Any]:
    """Override LLM decision when Iron Rules would be violated.

    Iron Rule 5 — boundary: if out-of-scope and scope is strict/moderate,
    the LLM must not hint; override to boundary_decline or boundary_bridge.

    Iron Rule 4 — escalation: if consecutive errors >= threshold, the LLM
    must escalate; override hint to escalate.
    """
    scope_level = boundary.get("scope_level", "moderate")
    emotional_reason = _detect_emotional_signal(student_input)

    if decision["action"] in ("hint", "direct_response") and emotional_reason:
        urgency = "high" if emotional_reason == "emotional_distress" else "medium"
        logger.info(
            "Guardrail override: detected %s signal; forcing escalation",
            emotional_reason,
        )
        return {
            "action": "escalate",
            "reasoning": (
                f"Guardrail override: {decision.get('reasoning', '')} "
                f"→ emotional escalation ({emotional_reason})"
            ),
            "tool_params": {
                "student_id": student_id,
                "reason": emotional_reason,
                "context_summary": student_input[:200],
                "urgency": urgency,
            },
            "response_text": "",
        }

    effective_concept = target_concept
    if not effective_concept:
        detected = _detect_out_of_scope_topic(student_input, boundary)
        if detected:
            effective_concept = detected

    if (
        decision["action"] in ("hint", "direct_response")
        and effective_concept
        and _is_out_of_scope(effective_concept, boundary)
    ):
        if scope_level != "permissive":
            action = (
                "boundary_decline" if scope_level == "strict"
                else "boundary_bridge"
            )
            logger.info(
                "Guardrail override: concept '%s' is out-of-scope "
                "(scope_level=%s); switching to %s",
                effective_concept, scope_level, action,
            )
            return {
                "action": action,
                "reasoning": (
                    f"Guardrail override: {decision.get('reasoning', '')} "
                    f"→ boundary {action} (scope_level={scope_level})"
                ),
                "tool_params": {},
                "response_text": _boundary_response(
                    scope_level, boundary, effective_concept,
                ),
            }
        else:
            logger.info(
                "Permissive scope: concept '%s' is out-of-scope but "
                "exploration allowed; adding curriculum tie-back",
                effective_concept,
            )
            return {
                "action": "boundary_permissive",
                "reasoning": (
                    f"Guardrail: {decision.get('reasoning', '')} "
                    f"→ permissive scope tie-back"
                ),
                "tool_params": decision.get("tool_params", {}),
                "response_text": _boundary_response(
                    scope_level, boundary, effective_concept,
                ),
            }

    if decision["action"] in ("hint", "direct_response"):
        concept_entry = cog_model.get("concepts", {}).get(target_concept, {})
        stored_errors = concept_entry.get("consecutive_errors", 0)
        effective_errors = stored_errors + (1 if is_correct is False else 0)

        if effective_errors >= _ESCALATION_THRESHOLD:
            logger.info(
                "Guardrail override: LLM chose hint but consecutive "
                "errors=%d >= %d; forcing escalation",
                effective_errors, _ESCALATION_THRESHOLD,
            )
            return {
                "action": "escalate",
                "reasoning": (
                    f"Guardrail override: {decision.get('reasoning', '')} "
                    f"→ forced escalation "
                    f"(effective_consecutive_errors={effective_errors})"
                ),
                "tool_params": {
                    "student_id": student_id,
                    "reason": "repeated_failure",
                    "context_summary": (
                        f"Student has {effective_errors} consecutive errors "
                        f"on '{target_concept}': {student_input[:200]}"
                    ),
                    "urgency": "high",
                },
                "response_text": "",
            }

    if decision["action"] == "direct_response":
        text = decision.get("response_text", "")
        if _contains_direct_answer(text) or _contains_interest_probe(text):
            logger.info(
                "Guardrail override: unsafe direct response; switching to hint"
            )
            return {
                "action": "hint",
                "reasoning": (
                    f"Guardrail override: {decision.get('reasoning', '')} "
                    "→ sanitized direct_response to hint"
                ),
                "tool_params": {
                    "student_id": student_id,
                    "current_input": student_input,
                    "target_concept": target_concept or "general",
                    "error_analysis": {},
                },
                "response_text": "",
            }

    return decision


# ---------------------------------------------------------------------------
# Deterministic Fallback
# ---------------------------------------------------------------------------

def _deterministic_fallback(
    student_id: str,
    student_input: str,
    target_concept: str,
    error_analysis: Dict[str, Any],
    cog_model: Dict[str, Any],
    boundary: Dict[str, Any],
    is_correct: Optional[bool],
) -> Dict[str, Any]:
    """Fallback when LLM is unavailable.

    Mirrors the three decision paths from COMPANION_LOGIC_FLOW:
      Path C — boundary check (strict -> decline, moderate -> bridge)
      Path B — escalation (>= 5 consecutive errors)
      Path A — normal hint
    """
    scope_level = boundary.get("scope_level", "moderate")

    effective_concept = target_concept
    if not effective_concept:
        detected = _detect_out_of_scope_topic(student_input, boundary)
        if detected:
            effective_concept = detected

    # Path C: knowledge boundary enforcement
    if effective_concept and _is_out_of_scope(effective_concept, boundary):
        if scope_level != "permissive":
            action = (
                "boundary_decline" if scope_level == "strict"
                else "boundary_bridge"
            )
            return {
                "action": action,
                "reasoning": (
                    f"LLM unavailable; deterministic boundary {action} "
                    f"(scope_level={scope_level})"
                ),
                "tool_params": {},
                "response_text": _boundary_response(
                    scope_level, boundary, effective_concept,
                ),
            }

    # Path B: escalation on repeated failure
    concept_entry = cog_model.get("concepts", {}).get(target_concept, {})
    stored_errors = concept_entry.get("consecutive_errors", 0)
    effective_errors = stored_errors + (1 if is_correct is False else 0)

    if effective_errors >= _ESCALATION_THRESHOLD:
        return {
            "action": "escalate",
            "reasoning": (
                f"LLM unavailable; deterministic escalation "
                f"(effective_consecutive_errors={effective_errors})"
            ),
            "tool_params": {
                "student_id": student_id,
                "reason": "repeated_failure",
                "context_summary": (
                    f"Student has {effective_errors} consecutive errors on "
                    f"'{target_concept}': {student_input[:200]}"
                ),
                "urgency": "high",
            },
            "response_text": "",
        }

    # Path A: normal hint
    enriched_analysis = dict(error_analysis)
    enriched_analysis["effective_consecutive_errors"] = effective_errors

    return {
        "action": "hint",
        "reasoning": "LLM unavailable; deterministic fallback to construct_hint",
        "tool_params": {
            "student_id": student_id,
            "current_input": student_input,
            "target_concept": target_concept,
            "error_analysis": enriched_analysis,
        },
        "response_text": "",
    }


# ---------------------------------------------------------------------------
# Persist Interaction
# ---------------------------------------------------------------------------

def _persist_interaction(
    student_id: str,
    student_input: str,
    response_text: str,
    tools_used: List[str],
    reasoning: str,
) -> None:
    """Write a structured interaction record to interaction_episodes."""
    now = _utc_iso()
    episode_key = f"interaction:{student_id}:{uuid4().hex[:8]}"
    shared_memory.write(_NS_EPISODES, episode_key, {
        "type": "interaction",
        "student_id": student_id,
        "student_input": student_input,
        "response": response_text,
        "tools_used": tools_used,
        "reasoning": reasoning,
        "timestamp": now,
    })


# ---------------------------------------------------------------------------
# Session-level Error Tracker
# ---------------------------------------------------------------------------

def _read_session_tracker(state: State) -> Dict[str, Dict[str, Any]]:
    """Read the per-concept session error tracker from working memory.

    Returns a dict keyed by concept name, each value containing:
        consecutive_errors (int), strategies_tried (list[str]),
        last_strategy (str | None).
    """
    wm = state.get("working_memory", {})
    return dict(wm.get("session_error_tracker", {}))


def _update_session_tracker(
    tracker: Dict[str, Dict[str, Any]],
    concept: str,
    is_correct: Optional[bool],
    strategy_used: Optional[str],
) -> Dict[str, Dict[str, Any]]:
    """Return an updated copy of the session tracker after one interaction.

    * correct answer   -> reset that concept's counter and tried-strategies
    * incorrect answer -> bump counter, record strategy
    * unknown (None)   -> leave counter unchanged, still record strategy
    """
    tracker = {k: dict(v) for k, v in tracker.items()}

    if concept not in tracker:
        tracker[concept] = {
            "consecutive_errors": 0,
            "strategies_tried": [],
            "last_strategy": None,
        }

    entry = tracker[concept]

    if is_correct is True:
        entry["consecutive_errors"] = 0
        entry["strategies_tried"] = []
        entry["last_strategy"] = None
    elif is_correct is False:
        entry["consecutive_errors"] = entry.get("consecutive_errors", 0) + 1
        tried = list(entry.get("strategies_tried", []))
        if strategy_used and strategy_used not in tried:
            tried.append(strategy_used)
        entry["strategies_tried"] = tried
        entry["last_strategy"] = strategy_used
    else:
        if strategy_used:
            entry["last_strategy"] = strategy_used

    return tracker


def _compute_effective_errors(
    concept: str,
    cog_model: Dict[str, Any],
    session_tracker: Dict[str, Dict[str, Any]],
    is_correct: Optional[bool],
) -> int:
    """Combine persistent and session error counts, adding 1 for a current error."""
    stored = cog_model.get("concepts", {}).get(concept, {}).get(
        "consecutive_errors", 0,
    )
    session = session_tracker.get(concept, {}).get("consecutive_errors", 0)
    base = max(stored, session)
    return base + (1 if is_correct is False else 0)


# ---------------------------------------------------------------------------
# Main Node Entry Point
# ---------------------------------------------------------------------------

def socratic_companion_node(state: State) -> State:
    """
    Socratic Companion node — 5-phase ReAct loop.

    1. Load context (cognitive model, knowledge boundary, history, session tracker)
    2. LLM reasoning via MiniMax-M2.5 (with deterministic fallback)
    3. Dispatch tools based on LLM decision (with effective-error injection)
    3b. Strategy-exhaustion check
    4. Update student cognitive model and session tracker (every interaction)
    5. Persist interaction and return updated state
    """
    payload = state.get("event_payload", {})
    student_id = payload.get("student_id", "unknown-student")
    student_input = payload.get("content", "")
    target_concept = payload.get("target_concept") or ""
    error_analysis = payload.get("error_analysis") or {}
    is_correct: Optional[bool] = payload.get("is_correct")

    # ── Phase 1: Load Context ─────────────────────────────────────────────
    cog_model = _bootstrap_cognitive_model(student_id, target_concept)
    boundary = _load_knowledge_boundary(state)
    history = _load_interaction_history(student_id)
    session_tracker = _read_session_tracker(state)

    # ── Phase 2: LLM Reasoning ────────────────────────────────────────────
    decision = _llm_reason(
        student_input, cog_model, boundary, history, payload,
        session_tracker=session_tracker,
    )
    if decision is None:
        decision = _deterministic_fallback(
            student_id, student_input, target_concept, error_analysis,
            cog_model, boundary, is_correct,
        )

    decision = _enforce_guardrails(
        decision, student_id, student_input, target_concept,
        cog_model, boundary, is_correct,
    )

    # ── Phase 3: Tool Dispatch ────────────────────────────────────────────
    tools_called: List[Dict[str, Any]] = []
    response_text = ""

    if decision["action"] == "hint":
        params = decision["tool_params"]

        effective = _compute_effective_errors(
            target_concept, cog_model, session_tracker, is_correct,
        )
        ea = dict(params.get("error_analysis", error_analysis) or {})
        ea["effective_consecutive_errors"] = effective
        params["error_analysis"] = ea

        hint_result = construct_hint(
            student_id=params.get("student_id", student_id),
            current_input=params.get("current_input", student_input),
            target_concept=params.get("target_concept", target_concept),
            error_analysis=ea,
        )
        tools_called.append({"tool": "construct_hint", "result": hint_result})

        follow_ups = hint_result.get("follow_up_questions", [])
        response_text = hint_result["hint_content"]
        if follow_ups:
            response_text += "\n\n" + "\n".join(f"- {q}" for q in follow_ups)

    elif decision["action"] == "escalate":
        params = decision["tool_params"]
        esc_result = escalate_to_human(
            student_id=params.get("student_id", student_id),
            reason=params.get("reason", "frustration"),
            context_summary=params.get(
                "context_summary", student_input[:200],
            ),
            urgency=params.get("urgency", "medium"),
        )
        tools_called.append({"tool": "escalate_to_human", "result": esc_result})
        response_text = esc_result["student_message"]

    elif decision["action"] in (
        "boundary_decline", "boundary_bridge", "boundary_permissive",
    ):
        response_text = decision.get("response_text", "")

    elif decision["action"] == "direct_response":
        response_text = decision.get("response_text", "")

    # ── Phase 3b: Strategy Exhaustion Check ────────────────────────────────
    hint_strategy: Optional[str] = None
    for tc in tools_called:
        if tc["tool"] == "construct_hint":
            hint_strategy = tc["result"].get("strategy")
            break

    if (
        is_correct is False
        and decision["action"] == "hint"
        and target_concept
    ):
        tried = list(
            session_tracker.get(target_concept, {}).get("strategies_tried", [])
        )
        if hint_strategy and hint_strategy not in tried:
            tried.append(hint_strategy)

        if _ALL_STRATEGIES.issubset(set(tried)):
            logger.info(
                "Strategy exhaustion: all %d strategies tried for '%s'; "
                "escalating",
                len(_ALL_STRATEGIES), target_concept,
            )
            esc_result = escalate_to_human(
                student_id=student_id,
                reason="repeated_failure",
                context_summary=(
                    f"All {len(_ALL_STRATEGIES)} hint strategies exhausted "
                    f"for '{target_concept}': {student_input[:200]}"
                ),
                urgency="high",
            )
            tools_called.append({
                "tool": "escalate_to_human", "result": esc_result,
            })
            response_text = esc_result["student_message"]

    # ── Phase 4: Update Cognition & Session Tracker (always) ──────────────
    cognition_concept = target_concept if target_concept else "general"

    cognition_result = update_student_cognition_map(
        student_id=student_id,
        interaction_data={
            "concept": cognition_concept,
            "student_response": student_input,
            "is_correct": is_correct,
            "time_spent": float(payload.get("time_spent", 0.0)),
            "help_requests": int(payload.get("help_requests", 0)),
            "hint_strategy": hint_strategy,
        },
    )
    tools_called.append({
        "tool": "update_student_cognition_map",
        "result": cognition_result,
    })

    session_tracker = _update_session_tracker(
        session_tracker, cognition_concept, is_correct, hint_strategy,
    )

    # ── Phase 5: Persist & Return State ───────────────────────────────────
    tool_names = [tc["tool"] for tc in tools_called]
    _persist_interaction(
        student_id=student_id,
        student_input=student_input,
        response_text=response_text,
        tools_used=tool_names,
        reasoning=decision.get("reasoning", ""),
    )

    state["current_agent"] = "socratic_companion"
    state["response_to_student"] = response_text
    state["tools_to_call"] = tools_called
    state["working_memory"] = state.get("working_memory", {})
    state["working_memory"]["cognitive_model"] = cognition_result
    state["working_memory"]["llm_reasoning"] = decision.get("reasoning", "")
    state["working_memory"]["knowledge_boundary"] = boundary
    state["working_memory"]["session_error_tracker"] = session_tracker
    state["agent_decision"] = ""
    state["loop_count"] = state.get("loop_count", 0) + 1

    logger.info(
        "Companion node completed: student=%s action=%s tools=%s",
        student_id,
        decision["action"],
        tool_names,
    )
    return state
