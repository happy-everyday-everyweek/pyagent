"""Execution context for middleware and agent execution."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionContext:
    """Context passed through middleware chain during execution.

    Contains thread information, configuration, and runtime metadata.
    """

    thread_id: str
    user_id: str | None = None
    session_id: str | None = None
    agent_name: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from context metadata.

        Args:
            key: Key to look up.
            default: Default value if key not found.

        Returns:
            Value from metadata or default.
        """
        return self.metadata.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in context metadata.

        Args:
            key: Key to set.
            value: Value to store.
        """
        self.metadata[key] = value

    @property
    def workspace_path(self) -> str | None:
        """Get workspace path for this thread."""
        return self.get("workspace_path")

    @property
    def uploads_path(self) -> str | None:
        """Get uploads path for this thread."""
        return self.get("uploads_path")

    @property
    def outputs_path(self) -> str | None:
        """Get outputs path for this thread."""
        return self.get("outputs_path")
