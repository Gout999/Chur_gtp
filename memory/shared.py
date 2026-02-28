"""
Shared memory read/write and namespace contract for Agent collaboration.
PRD §3.3: teacher_authority_graph (Architect write, Companion read),
interest_signals (Companion write, Catalyst read), pending_validations (Catalyst write, Architect read).
"""
from typing import Dict, Any, Optional

# In-memory placeholder; replace with real store (e.g. Redis) in Phase 1
_store: Dict[str, Dict[str, Any]] = {
    "teacher_authority_graph": {},
    "interest_signals": {},
    "pending_validations": {},
}


def read(namespace: str, key: str) -> Optional[Any]:
    """Read value for namespace + key."""
    if namespace not in _store:
        _store[namespace] = {}
    return _store[namespace].get(key)


def write(namespace: str, key: str, value: Any) -> None:
    """Write value for namespace + key."""
    if namespace not in _store:
        _store[namespace] = {}
    _store[namespace][key] = value


class SharedMemoryProxy:
    """Proxy for shared_memory.write / read used by agents."""

    def read(self, namespace: str, key: str) -> Optional[Any]:
        return read(namespace, key)

    def write(self, namespace: str, key: str, value: Any) -> None:
        write(namespace, key, value)


shared_memory = SharedMemoryProxy()
