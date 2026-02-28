"""
Homework marker service: send homework image to MiniMax vision model and parse structured feedback.
Uses same endpoint as catalyst (chatcompletion_v2) with model MiniMax-Text-01 and image content.
"""
from __future__ import annotations

import json
import logging
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from config import (
    MINIMAX_API_KEY,
    MINIMAX_GROUP_ID,
    MINIMAX_HOMEWORK_VISION_MODEL,
)

LOG = logging.getLogger("eduguide.homework_marker")

MINIMAX_BASE = "https://api.minimax.io"
CHAT_V2_PATH = "/v1/text/chatcompletion_v2"

SYSTEM_PROMPT = """You are a homework marker. Grade the homework in the image and respond with ONLY valid JSON, no markdown or explanation.

Required JSON shape:
{
  "score": <number>,
  "max_score": <number>,
  "feedback": "<string: overall feedback>",
  "criteria_scores": [{"name": "<string>", "score": <number>, "comment": "<string>"}]
}

- score: points awarded (0 to max_score).
- max_score: maximum score (use the value provided by the user).
- feedback: short overall feedback for the student.
- criteria_scores: optional list of per-criterion scores and comments; omit or use [] if not applicable.

Output nothing but the JSON object."""


def mark_homework_from_image(
    image_base64: str,
    content_type: str,
    *,
    rubric: str | None = None,
    subject: str | None = None,
    max_score: int = 100,
) -> dict[str, Any]:
    """
    Send homework image to MiniMax vision model and return structured marking result.

    :param image_base64: Base64-encoded image bytes (no data URL prefix).
    :param content_type: MIME type, e.g. "image/jpeg" or "image/png".
    :param rubric: Optional marking criteria for the model.
    :param subject: Optional subject name.
    :param max_score: Maximum score (default 100).
    :return: Dict with score, max_score, feedback, criteria_scores (optional), model_used.
    :raises ValueError: If API key missing or requests not available.
    :raises RuntimeError: On API error or failed JSON parse (caller may map to 502).
    """
    if not MINIMAX_API_KEY:
        raise ValueError("MINIMAX_API_KEY not set")
    if requests is None:
        raise ValueError("requests not installed")

    mime = "image/jpeg" if content_type and "jpeg" in content_type else content_type or "image/png"
    data_url = f"data:{mime};base64,{image_base64}"

    text_parts = [
        "Grade the homework in the attached image.",
        f"Maximum score: {max_score}.",
    ]
    if subject:
        text_parts.append(f"Subject: {subject}.")
    if rubric:
        text_parts.append(f"Marking criteria: {rubric}")
    text_parts.append("Respond with only the required JSON.")
    user_text = " ".join(text_parts)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]

    url = f"{MINIMAX_BASE}{CHAT_V2_PATH}"
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }
    params: dict[str, str] = {}
    if MINIMAX_GROUP_ID:
        params["GroupId"] = MINIMAX_GROUP_ID

    body = {
        "model": MINIMAX_HOMEWORK_VISION_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_completion_tokens": 2048,
    }

    try:
        resp = requests.post(url, headers=headers, params=params, json=body, timeout=90)
        resp.raise_for_status()
    except requests.RequestException as e:
        LOG.warning("MiniMax homework marker API request failed: %s", e)
        raise RuntimeError(f"Marking service error: {e!s}") from e

    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("Marking service returned no choices")

    raw_content = (choices[0].get("message") or {}).get("content") or ""
    content = raw_content.strip()

    # Strip markdown code blocks if present
    for marker in ("```json", "```"):
        if marker in content:
            try:
                content = content.split(marker)[1]
            except IndexError:
                pass
            if "```" in content:
                content = content.split("```")[0]
            content = content.strip()
            break

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        LOG.warning("Failed to parse marking response as JSON: %s", e)
        raise RuntimeError("Marking failed: invalid response format") from e

    if not isinstance(parsed, dict):
        raise RuntimeError("Marking failed: response was not a JSON object")

    score = parsed.get("score")
    max_s = parsed.get("max_score", max_score)
    feedback = parsed.get("feedback", "")
    criteria = parsed.get("criteria_scores")
    if criteria is not None and not isinstance(criteria, list):
        criteria = None

    return {
        "score": score if isinstance(score, (int, float)) else 0,
        "max_score": int(max_s) if max_s is not None else max_score,
        "feedback": str(feedback) if feedback is not None else "",
        "criteria_scores": criteria,
        "model_used": MINIMAX_HOMEWORK_VISION_MODEL,
    }
