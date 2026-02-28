"""
Working Memory: current in-context active memory for the active agent.
PRD §3.1 MemGPT-style hierarchy.
"""
from typing import Dict, List, Any


class WorkingMemory:
    """
    Current active memory in the agent context window.
    Agent decides what to keep here.
    """
    content: Dict[str, Any] = {}
    max_tokens: int = 8000

    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
        self.content = {
            "active_concepts": [],
            "retrieved_context": [],
            "session_goals": [],
            "pending_actions": [],
            "agent_reasoning_history": [],
        }
