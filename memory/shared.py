"""
Shared memory contract for Agent collaboration.

This module provides:
1. ``SharedMemoryClient`` with write/read/read_all/update methods.
2. A process-local in-memory backend for development and tests.
3. ``shared_memory`` proxy used by agents for namespace-based collaboration.
"""
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


NAMESPACES: Dict[str, str] = {
    "teacher_uploads": "Teacher uploaded materials.",
    "teacher_authority_graph": "Architect-maintained knowledge authority graph.",
    "teacher_boundary_adjustments": "Teacher boundary adjustments.",
    "teacher_escalation_responses": "Teacher responses to escalations.",
    "teacher_student_messages": "Teacher-student message history.",
    "student_cognitive_models": "Companion-maintained student cognition state.",
    "interaction_episodes": "Agent interaction episodes.",
    "pending_escalations": "Escalations waiting for teacher handling.",
    "pending_validations": "Catalyst outputs waiting for Architect validation.",
    "interest_signals": "Catalyst: student interests inferred from uploaded PDF/Word; Catalyst reads for monitoring and briefing.",
    "companion_control": "Companion control instructions.",
}

# Store shape: namespace -> key -> entry payload
_STORE: Dict[str, Dict[str, Dict[str, Any]]] = {
    namespace: {} for namespace in NAMESPACES
}


def _ensure_namespace(
    store: Dict[str, Dict[str, Dict[str, Any]]],
    namespace: str,
) -> Dict[str, Dict[str, Any]]:
    if namespace not in store:
        store[namespace] = {}
    return store[namespace]


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SharedMemoryClient:
    """Simple shared memory client with namespace contract."""

    def __init__(
        self,
        redis_client: Any = None,
        db: Any = None,
        backend_store: Optional[Dict[str, Dict[str, Dict[str, Any]]]] = None,
    ):
        self.redis = redis_client
        self.db = db
        self._store = backend_store if backend_store is not None else _STORE

    def write(
        self,
        namespace: str,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> str:
        """
        Write an entry into a namespace.

        ``ttl`` is accepted for compatibility with a future Redis-backed client.
        """
        del ttl  # intentionally unused in in-memory implementation
        entry_id = f"{namespace}:{key}"
        now = _utc_iso()
        entry = {
            "entry_id": entry_id,
            "namespace": namespace,
            "key": key,
            "value": deepcopy(value),
            "created_at": now,
            "updated_at": now,
        }
        namespace_store = _ensure_namespace(self._store, namespace)
        namespace_store[key] = entry
        return entry_id

    def read(self, namespace: str, key: str) -> Optional[Dict[str, Any]]:
        """Read one entry by namespace + key."""
        namespace_store = _ensure_namespace(self._store, namespace)
        entry = namespace_store.get(key)
        return deepcopy(entry) if entry is not None else None

    def read_all(
        self,
        namespace: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Read all entries in namespace, optionally filtered by value keys."""
        namespace_store = _ensure_namespace(self._store, namespace)
        entries = list(namespace_store.values())
        results: List[Dict[str, Any]] = []
        for entry in entries:
            if filter_dict:
                if not all(entry["value"].get(k) == v for k, v in filter_dict.items()):
                    continue
            results.append(deepcopy(entry))
            if len(results) >= limit:
                break
        return results

    def update(self, namespace: str, key: str, updates: Dict[str, Any]) -> bool:
        """Patch an entry ``value`` payload in place."""
        namespace_store = _ensure_namespace(self._store, namespace)
        entry = namespace_store.get(key)
        if entry is None:
            return False
        entry["value"].update(deepcopy(updates))
        entry["updated_at"] = _utc_iso()
        return True

    def subscribe(self, namespace: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Compatibility stub for pub/sub style consumers.

        A real backend should stream updates. In this in-memory implementation we
        invoke callback with a synthetic snapshot marker.
        """
        callback({"namespace": namespace, "status": "subscription_not_supported"})


_DEFAULT_CLIENT = SharedMemoryClient()


def read(namespace: str, key: str) -> Optional[Any]:
    """Module-level helper used by legacy call sites."""
    return _DEFAULT_CLIENT.read(namespace, key)


def write(namespace: str, key: str, value: Dict[str, Any]) -> str:
    """Module-level helper used by legacy call sites."""
    return _DEFAULT_CLIENT.write(namespace, key, value)


class SharedMemoryProxy:
    """Proxy used by agents. Mirrors shared_memory.read/write contract."""

    def read(self, namespace: str, key: str) -> Optional[Any]:
        return _DEFAULT_CLIENT.read(namespace, key)

    def write(self, namespace: str, key: str, value: Dict[str, Any]) -> str:
        return _DEFAULT_CLIENT.write(namespace, key, value)

    def update(self, namespace: str, key: str, updates: Dict[str, Any]) -> bool:
        return _DEFAULT_CLIENT.update(namespace, key, updates)

    def read_all(
        self,
        namespace: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        return _DEFAULT_CLIENT.read_all(namespace, filter_dict=filter_dict, limit=limit)


shared_memory = SharedMemoryProxy()
