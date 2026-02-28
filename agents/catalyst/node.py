"""
Curiosity Catalyst node: monitor arXiv/GitHub, synthesize briefing, optional proactive notify.
PRD §4.1; Phase 4 – Engineer C. graph.py imports this.
"""
from typing import Dict, Any

State = Dict[str, Any]


def curiosity_catalyst_node(state: State) -> State:
    """
    On new_content_detected: evaluate relevance, optionally synthesize_briefing; write pending_validations for
    Architect; append to state["notifications"] when notifying student.
    """
    # TODO: Load prompt from prompts.catalyst; bind tools from tools.arxiv_monitor, tools.github_monitor, tools.briefing
    state["current_agent"] = "curiosity_catalyst"
    state["agent_decision"] = ""
    state.setdefault("notifications", [])
    return state
