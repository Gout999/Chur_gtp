"""
Base tool framework: register, invoke, and log tool calls.

The module supports both styles used in this repository:
1. Direct registration via ``register_tool`` + ``execute_tool``.
2. Decorator registration via ``@tool("name")``.
"""
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict
import logging

logger = logging.getLogger("eduguide.tools")


class ToolRegistry:
    """Simple runtime registry for tool callables."""

    def __init__(self):
        self._tools: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any]) -> Callable[..., Any]:
        self._tools[name] = func
        logger.debug("Registered tool: %s", name)
        return func

    def get(self, name: str) -> Callable[..., Any]:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return self._tools[name]

    def list_tools(self) -> Dict[str, str]:
        return {name: (func.__doc__ or "") for name, func in self._tools.items()}


tool_registry = ToolRegistry()


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def register_tool(name: str, func: Callable[..., Any]) -> Callable[..., Any]:
    """Register a tool by name."""
    return tool_registry.register(name, func)


def get_tool(name: str) -> Callable[..., Any]:
    """Get a previously registered tool."""
    return tool_registry.get(name)


def list_tools() -> Dict[str, str]:
    """List registered tools and their docstrings."""
    return tool_registry.list_tools()


def log_tool_call(tool_name: str, arguments: Dict[str, Any]) -> None:
    """Structured logging hook for tool call."""
    logger.info(
        "Tool call @%s name=%s args=%s",
        _utc_iso(),
        tool_name,
        arguments,
    )


def log_tool_result(tool_name: str, result: Any) -> None:
    """Structured logging hook for tool result."""
    logger.debug(
        "Tool result @%s name=%s result=%s",
        _utc_iso(),
        tool_name,
        str(result)[:500],
    )


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Execute a registered tool with arguments."""
    tool_fn = get_tool(tool_name)
    log_tool_call(tool_name, arguments)
    result = tool_fn(**arguments)
    log_tool_result(tool_name, result)
    return result


def tool(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for registering a callable as a tool."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log_tool_call(name, {"args": args, "kwargs": kwargs})
            result = func(*args, **kwargs)
            log_tool_result(name, result)
            return result

        register_tool(name, wrapper)
        return wrapper

    return decorator
