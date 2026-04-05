"""Todo list middleware for task tracking."""

import logging
from typing import Any

from src.execution.context import ExecutionContext
from src.execution.middlewares import BaseMiddleware, MiddlewarePhase, MiddlewareResult

logger = logging.getLogger(__name__)


class TodoListMiddleware(BaseMiddleware):
    """Middleware that tracks and updates todo items during execution.

    Integrates with the todo system to:
    - Track task progress
    - Update todo status based on agent actions
    - Provide todo context to the agent
    """

    name = "todo_list"
    priority = 40
    phases = [MiddlewarePhase.BEFORE_AGENT, MiddlewarePhase.AFTER_AGENT]

    def __init__(self, auto_update: bool = True):
        super().__init__()
        self._auto_update = auto_update

    def _extract_todo_updates(self, messages: list[Any]) -> list[dict[str, Any]]:
        """Extract todo updates from agent messages.

        Args:
            messages: Agent messages.

        Returns:
            List of todo update dictionaries.
        """
        updates = []
        for msg in messages:
            content = getattr(msg, "content", "")
            if isinstance(content, str) and "TODO:" in content.upper():
                updates.append({"source": "agent", "content": content})
        return updates

    def process(
        self,
        phase: MiddlewarePhase,
        state: dict[str, Any],
        context: ExecutionContext,
    ) -> MiddlewareResult:
        if phase == MiddlewarePhase.BEFORE_AGENT:
            return self._before_agent(state, context)
        elif phase == MiddlewarePhase.AFTER_AGENT:
            return self._after_agent(state, context)
        return MiddlewareResult()

    def _before_agent(
        self,
        state: dict[str, Any],
        context: ExecutionContext,
    ) -> MiddlewareResult:
        todo_context = state.get("todo_context", {})
        if not todo_context:
            return MiddlewareResult()

        todo_summary = self._format_todo_summary(todo_context)
        return MiddlewareResult(state_update={"todo_summary": todo_summary})

    def _after_agent(
        self,
        state: dict[str, Any],
        context: ExecutionContext,
    ) -> MiddlewareResult:
        if not self._auto_update:
            return MiddlewareResult()

        messages = state.get("messages", [])
        updates = self._extract_todo_updates(messages)

        if updates:
            logger.debug("Extracted %d todo updates", len(updates))
            return MiddlewareResult(state_update={"todo_updates": updates})

        return MiddlewareResult()

    def _format_todo_summary(self, todo_context: dict[str, Any]) -> str:
        """Format todo context into a summary string.

        Args:
            todo_context: Todo context dictionary.

        Returns:
            Formatted summary string.
        """
        items = todo_context.get("items", [])
        if not items:
            return ""

        lines = ["Current tasks:"]
        for i, item in enumerate(items[:10], 1):
            status = item.get("status", "pending")
            content = item.get("content", "")[:50]
            lines.append(f"  {i}. [{status}] {content}")

        return "\n".join(lines)
