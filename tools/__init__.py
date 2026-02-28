"""
EduGuide tools: base registry and agent-specific tools.
PRD §6: base, ingest, boundary, hints, cognition, arxiv_monitor, github_monitor, briefing.
"""
from .base import register_tool, execute_tool

__all__ = ["register_tool", "execute_tool"]
