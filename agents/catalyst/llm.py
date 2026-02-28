"""
MINIMAX LLM client for Curiosity Catalyst.
Used for: interest extraction, relevance scoring, personalized briefing, task reasoning.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from config import MINIMAX_API_KEY, MINIMAX_GROUP_ID

LOG = logging.getLogger("eduguide.catalyst.llm")

MINIMAX_BASE = "https://api.minimax.io"
CHAT_V2_PATH = "/v1/text/chatcompletion_v2"
DEFAULT_MODEL = "M2-her"


def _call_minimax(
    messages: List[Dict[str, str]],
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> Optional[str]:
    """
    Call MINIMAX chat completion API. Returns assistant content or None on error.
    """
    if not MINIMAX_API_KEY:
        LOG.warning("MINIMAX_API_KEY not set, LLM calls will be no-op")
        return None
    if requests is None:
        LOG.warning("requests not installed, LLM calls disabled")
        return None

    url = f"{MINIMAX_BASE}{CHAT_V2_PATH}"
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }
    params: Dict[str, str] = {}
    if MINIMAX_GROUP_ID:
        params["GroupId"] = MINIMAX_GROUP_ID

    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
    }

    try:
        resp = requests.post(url, headers=headers, params=params, json=body, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            return None
        msg = choices[0].get("message", {})
        return msg.get("content", "").strip()
    except Exception as e:
        LOG.warning("MINIMAX API call failed: %s", e)
        return None


def extract_interest_signals(text: str) -> Dict[str, Any]:
    """
    User Profile/Resume -> LLM -> JSON (Interest Signals).
    Extracts research_directions, tech_stack, keywords from unstructured text.
    """
    system = """You are an expert at analyzing student resumes, research papers, and self-study materials.
Extract structured interest signals. Output ONLY valid JSON, no markdown or explanation.

Output format:
{
  "keywords": ["keyword1", "keyword2", ...],
  "research_directions": ["direction1", ...],
  "tech_stack": ["tech1", ...],
  "confidence": 0.0-1.0
}
- keywords: English terms for academic search (arXiv, GitHub). 5-15 items.
- research_directions: high-level research interests.
- tech_stack: technologies, frameworks, tools mentioned.
- confidence: how confident you are in the extraction (0-1)."""

    user = f"Analyze this text and extract interest signals:\n\n{text[:8000]}"
    content = _call_minimax(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.2,
        max_tokens=1024,
    )
    if not content:
        return {"keywords": [], "research_directions": [], "tech_stack": [], "confidence": 0.0}

    try:
        # Strip markdown code blocks if present
        if "```" in content:
            for marker in ("```json", "```"):
                if marker in content:
                    content = content.split(marker)[1] if marker in content else content
        parsed = json.loads(content.strip())
        keywords = parsed.get("keywords", [])
        if isinstance(keywords, list):
            keywords = [str(k).strip() for k in keywords if k]
        return {
            "keywords": keywords[:15],
            "research_directions": parsed.get("research_directions", [])[:8],
            "tech_stack": parsed.get("tech_stack", [])[:10],
            "confidence": float(parsed.get("confidence", 0.7)),
        }
    except (json.JSONDecodeError, TypeError) as e:
        LOG.warning("Failed to parse interest signals JSON: %s", e)
        return {"keywords": [], "research_directions": [], "tech_stack": [], "confidence": 0.0}


def score_relevance(paper_abstract: str, interest_signals: Dict[str, Any]) -> float:
    """
    (Paper Abstract + Interest Signals) -> LLM -> Score (0-1).
    """
    keywords = interest_signals.get("keywords", [])[:10]
    directions = interest_signals.get("research_directions", [])[:5]
    ctx = f"Interest keywords: {', '.join(keywords)}. Directions: {', '.join(directions)}" if (keywords or directions) else "No prior interests."

    system = """You judge relevance of an academic paper to a student's interests.
Output ONLY a single number between 0.0 and 1.0. Nothing else.
0.0 = completely irrelevant, 1.0 = highly relevant."""

    user = f"Student interests: {ctx}\n\nPaper abstract: {paper_abstract[:1500]}\n\nRelevance score:"
    content = _call_minimax(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.1,
        max_tokens=16,
    )
    if not content:
        return 0.0
    try:
        val = float(content.strip().split()[0].replace(",", ""))
        return max(0.0, min(1.0, val))
    except (ValueError, IndexError):
        return 0.0


def score_relevance_batch(
    papers: List[Dict[str, Any]],
    interest_signals: Dict[str, Any],
    max_papers: int = 10,
) -> List[float]:
    """
    Score multiple papers in one LLM call. Returns list of scores (0-1) in same order.
    """
    if not papers or not interest_signals:
        return [0.0] * len(papers)

    keywords = interest_signals.get("keywords", [])[:10]
    directions = interest_signals.get("research_directions", [])[:5]
    ctx = f"Keywords: {', '.join(keywords)}. Directions: {', '.join(directions)}" if (keywords or directions) else "No interests."

    selected = papers[:max_papers]
    items = []
    for i, p in enumerate(selected):
        title = p.get("title", "")
        summary = (p.get("summary", ""))[:600]
        items.append(f"[{i}] {title}\n{summary}")

    system = f"""Student interests: {ctx}

For each paper [0] to [{len(selected)-1}], output its relevance score 0.0-1.0.
Format: one line per paper: "0: 0.85\\n1: 0.92\\n..." (index: score). Nothing else."""

    user = "Papers:\n" + "\n---\n".join(items) + "\n\nScores:"
    content = _call_minimax(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.1,
        max_tokens=256,
    )
    if not content:
        return [0.0] * len(selected)

    scores = [0.0] * len(selected)
    for line in content.strip().split("\n"):
        line = line.strip()
        if ":" in line:
            try:
                idx_part, score_part = line.split(":", 1)
                idx = int(idx_part.strip())
                val = float(score_part.strip().split()[0].replace(",", ""))
                if 0 <= idx < len(selected):
                    scores[idx] = max(0.0, min(1.0, val))
            except (ValueError, IndexError):
                pass
    return scores


def generate_briefing_summary(
    content_items: List[Dict[str, Any]],
    curriculum_context: Optional[Dict[str, Any]],
    system_prompt: str,
) -> str:
    """
    Raw Data -> LLM (System Prompt: catalyst) -> Professional Summary.
    """
    items_desc = []
    for i, it in enumerate(content_items[:5], 1):
        title = it.get("title", it.get("title_or_name", it.get("repo", "Item")))
        summary = it.get("summary", it.get("description", ""))[:500]
        src = it.get("source", "unknown")
        items_desc.append(f"{i}. [{src}] {title}\n   {summary}")

    topic = (curriculum_context or {}).get("topic", "current curriculum")
    user = f"""Content items to summarize:
{chr(10).join(items_desc)}

Curriculum context: {topic}

Write a brief, professional personalized summary (2-4 sentences) connecting these items to the student's interests and curriculum. English only."""

    content = _call_minimax(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user}],
        temperature=0.5,
        max_tokens=512,
    )
    return content.strip() if content else "No new relevant content found in this round."


def decide_next_action(state_summary: str, tools_available: List[str]) -> str:
    """
    Agent reasoning: given state, decide next action (which tool to call or output).
    Returns a decision keyword: "call_monitor" | "call_briefing" | "write_validation" | "notify" | "end"
    """
    system = """You are the Curiosity Catalyst. Based on current state, decide the next action.
Output ONLY one word: call_monitor, call_briefing, write_validation, notify, or end."""

    user = f"State: {state_summary[:500]}\nTools: {', '.join(tools_available)}\nNext action:"
    content = _call_minimax(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.1,
        max_tokens=32,
    )
    if not content:
        return "call_monitor"  # Default: run monitoring
    action = content.strip().lower().split()[0]
    valid = {"call_monitor", "call_briefing", "write_validation", "notify", "end"}
    return action if action in valid else "call_monitor"
