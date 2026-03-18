"""Simple key-value store for inter-task state."""

from typing import Any, Dict, List


class RuntimeStore:
    """Holds output keys produced by tasks between invocations."""

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def keys(self) -> List[str]:
        return list(self._store.keys())

    def all(self) -> Dict[str, Any]:
        return dict(self._store)

    def clear(self) -> None:
        self._store.clear()
