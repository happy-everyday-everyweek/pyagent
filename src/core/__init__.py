"""
PyAgent 核心模块

提供核心功能和基础类。
"""

from collections.abc import Callable
from typing import Any


class CoreContext:
    """核心上下文"""

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._callbacks: dict[str, list[Callable]] = {}

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._trigger_callbacks(key, value)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False

    def register_callback(self, key: str, callback: Callable) -> None:
        if key not in self._callbacks:
            self._callbacks[key] = []
        self._callbacks[key].append(callback)

    def _trigger_callbacks(self, key: str, value: Any) -> None:
        for callback in self._callbacks.get(key, []):
            try:
                callback(key, value)
            except Exception:
                pass

core_context = CoreContext()

__all__ = [
    "CoreContext",
    "core_context",
]
