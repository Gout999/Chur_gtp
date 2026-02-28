"""
Base tool framework: register, invoke, and log tool calls.
PRD Phase 1: tools can be registered, called, and logged.
"""
from typing import Callable, Dict, Any, List
import logging

logger = logging.getLogger("eduguide.tools")
_registry: Dict[str, Callable[..., Any]] = {}


def register_tool(name: str, func: Callable[..., Any]) -> None:
    """Register a tool by name."""
    _registry[name] = func
    logger.debug("Registered tool: %s", name)


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Execute a tool by name with given arguments; log call and result."""
    if tool_name not in _registry:
        raise ValueError(f"Unknown tool: {tool_name}")
    logger.info("Tool call: %s %s", tool_name, arguments)
    result = _registry[tool_name](**arguments)
    logger.debug("Tool result: %s", result)
    return result
