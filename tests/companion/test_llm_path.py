"""Mock-based tests for the LLM reasoning path in companion node.

These tests patch the Anthropic client to verify _llm_reason handles
various response shapes correctly: tool_use blocks, text-only, multiple
tools, unknown tool names, and API exceptions.

Anchored to: Issue 1 (tool mapping), Issue 3 (LLM path coverage),
             Issue 8 (multi-tool handling).
"""

import types
from unittest.mock import MagicMock, patch

import pytest

from agents.companion.node import _llm_reason, _TOOL_ACTION_MAP

pytestmark = pytest.mark.unit


def _make_block(block_type, **attrs):
    """Build a lightweight object mimicking an Anthropic content block."""
    return types.SimpleNamespace(type=block_type, **attrs)


def _make_response(*blocks):
    """Build a fake Anthropic messages.create() return value."""
    return types.SimpleNamespace(content=list(blocks))


_DUMMY_COG = {"concepts": {}, "misconceptions": []}
_DUMMY_BOUNDARY = {"scope_level": "moderate"}
_DUMMY_PAYLOAD = {"student_id": "s1", "target_concept": "force"}


def _patch_key_and_client(client_mock):
    """Return a combined context manager that patches both the API key check
    and the Anthropic client factory."""
    return (
        patch("config.MINIMAX_API_KEY", "fake-key"),
        patch("agents.companion.node._get_anthropic_client", return_value=client_mock),
    )


class TestToolUseMapping:
    """Issue 1: tool name -> action mapping must be explicit, not binary."""

    def test_construct_hint_maps_to_hint(self):
        client = MagicMock()
        client.messages.create.return_value = _make_response(
            _make_block("tool_use", name="construct_hint", input={
                "student_id": "s1", "current_input": "hi", "target_concept": "force",
            }),
        )

        p_key, p_client = _patch_key_and_client(client)
        with p_key, p_client:
            result = _llm_reason("hi", _DUMMY_COG, _DUMMY_BOUNDARY, [], _DUMMY_PAYLOAD)

        assert result is not None
        assert result["action"] == "hint"

    def test_escalate_maps_to_escalate(self):
        client = MagicMock()
        client.messages.create.return_value = _make_response(
            _make_block("tool_use", name="escalate_to_human", input={
                "student_id": "s1", "reason": "frustration",
                "context_summary": "stuck",
            }),
        )

        p_key, p_client = _patch_key_and_client(client)
        with p_key, p_client:
            result = _llm_reason("help", _DUMMY_COG, _DUMMY_BOUNDARY, [], _DUMMY_PAYLOAD)

        assert result is not None
        assert result["action"] == "escalate"

    def test_unknown_tool_falls_through_to_direct_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_response(
            _make_block("text", text="I will update cognition"),
            _make_block("tool_use", name="update_student_cognition_map", input={}),
        )

        p_key, p_client = _patch_key_and_client(client)
        with p_key, p_client:
            result = _llm_reason("ok", _DUMMY_COG, _DUMMY_BOUNDARY, [], _DUMMY_PAYLOAD)

        assert result is not None
        assert result["action"] == "direct_response"


class TestMultipleToolUseBlocks:
    """Issue 8: when LLM returns multiple tool_use blocks, escalation wins."""

    def test_escalation_prioritised_over_hint(self):
        client = MagicMock()
        client.messages.create.return_value = _make_response(
            _make_block("tool_use", name="construct_hint", input={
                "student_id": "s1", "current_input": "x", "target_concept": "y",
            }),
            _make_block("tool_use", name="escalate_to_human", input={
                "student_id": "s1", "reason": "frustration",
                "context_summary": "upset",
            }),
        )

        p_key, p_client = _patch_key_and_client(client)
        with p_key, p_client:
            result = _llm_reason(
                "I give up", _DUMMY_COG, _DUMMY_BOUNDARY, [], _DUMMY_PAYLOAD,
            )

        assert result is not None
        assert result["action"] == "escalate"

    def test_hint_used_when_no_escalation(self):
        client = MagicMock()
        client.messages.create.return_value = _make_response(
            _make_block("tool_use", name="construct_hint", input={
                "student_id": "s1", "current_input": "x", "target_concept": "y",
            }),
            _make_block("tool_use", name="construct_hint", input={
                "student_id": "s1", "current_input": "z", "target_concept": "w",
            }),
        )

        p_key, p_client = _patch_key_and_client(client)
        with p_key, p_client:
            result = _llm_reason(
                "try again", _DUMMY_COG, _DUMMY_BOUNDARY, [], _DUMMY_PAYLOAD,
            )

        assert result is not None
        assert result["action"] == "hint"


class TestTextOnlyResponse:

    def test_text_only_returns_direct_response(self):
        client = MagicMock()
        client.messages.create.return_value = _make_response(
            _make_block("text", text="Let me think about this."),
        )

        p_key, p_client = _patch_key_and_client(client)
        with p_key, p_client:
            result = _llm_reason("hm", _DUMMY_COG, _DUMMY_BOUNDARY, [], _DUMMY_PAYLOAD)

        assert result is not None
        assert result["action"] == "direct_response"
        assert result["response_text"] == "Let me think about this."


class TestThinkingBlock:

    def test_thinking_captured_in_reasoning(self):
        client = MagicMock()
        client.messages.create.return_value = _make_response(
            _make_block("thinking", thinking="Student seems confused about momentum"),
            _make_block("tool_use", name="construct_hint", input={
                "student_id": "s1", "current_input": "x", "target_concept": "momentum",
            }),
        )

        p_key, p_client = _patch_key_and_client(client)
        with p_key, p_client:
            result = _llm_reason("what?", _DUMMY_COG, _DUMMY_BOUNDARY, [], _DUMMY_PAYLOAD)

        assert result is not None
        assert "confused about momentum" in result["reasoning"]


class TestAPIFailure:

    def test_api_exception_returns_none(self):
        client = MagicMock()
        client.messages.create.side_effect = RuntimeError("connection timeout")

        p_key, p_client = _patch_key_and_client(client)
        with p_key, p_client:
            result = _llm_reason(
                "hello", _DUMMY_COG, _DUMMY_BOUNDARY, [], _DUMMY_PAYLOAD,
            )

        assert result is None

    def test_missing_api_key_returns_none(self):
        with patch("config.MINIMAX_API_KEY", ""):
            result = _llm_reason(
                "hello", _DUMMY_COG, _DUMMY_BOUNDARY, [], _DUMMY_PAYLOAD,
            )

        assert result is None


class TestToolActionMapCompleteness:
    """Verify _TOOL_ACTION_MAP covers exactly the tools in _TOOL_SCHEMAS."""

    def test_all_schema_tools_have_actions(self):
        from agents.companion.node import _TOOL_SCHEMAS
        schema_names = {s["name"] for s in _TOOL_SCHEMAS}
        mapped_names = set(_TOOL_ACTION_MAP.keys())
        assert schema_names == mapped_names
