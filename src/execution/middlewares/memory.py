"""Memory middleware for conversation persistence."""

import logging
import re
from typing import Any

from src.execution.context import ExecutionContext
from src.execution.middlewares import BaseMiddleware, MiddlewarePhase, MiddlewareResult

logger = logging.getLogger(__name__)

UPLOAD_BLOCK_RE = re.compile(r"<uploaded_files>[\s\S]*?</uploaded_files>\n*", re.IGNORECASE)


class MemoryMiddleware(BaseMiddleware):
    """Middleware that manages conversation memory.

    Filters and stores conversation history for long-term memory,
    excluding tool calls and intermediate steps.
    """

    name = "memory"
    priority = 60
    phases = [MiddlewarePhase.AFTER_AGENT]

    def __init__(self, enabled: bool = True, max_history: int = 100):
        super().__init__()
        self.enabled = enabled
        self._max_history = max_history

    def _filter_messages_for_memory(self, messages: list[Any]) -> list[Any]:
        """Filter messages for memory storage.

        Removes:
        - Tool messages
        - AI messages with tool_calls
        - Upload blocks from human messages

        Args:
            messages: All messages.

        Returns:
            Filtered messages suitable for memory.
        """
        filtered = []
        skip_next_ai = False

        for msg in messages:
            msg_type = getattr(msg, "type", None)

            if msg_type == "human":
                content = getattr(msg, "content", "")
                if isinstance(content, str) and "<uploaded_files>" in content:
                    stripped = UPLOAD_BLOCK_RE.sub("", content).strip()
                    if not stripped:
                        skip_next_ai = True
                        continue
                    if hasattr(msg, "content"):
                        msg.content = stripped
                filtered.append(msg)
                skip_next_ai = False

            elif msg_type == "ai":
                tool_calls = getattr(msg, "tool_calls", None)
                if not tool_calls:
                    if skip_next_ai:
                        skip_next_ai = False
                        continue
                    filtered.append(msg)

        return filtered

    def process(
        self,
        phase: MiddlewarePhase,
        state: dict[str, Any],
        context: ExecutionContext,
    ) -> MiddlewareResult:
        if not self.enabled:
            return MiddlewareResult()

        messages = state.get("messages", [])
        if not messages:
            return MiddlewareResult()

        filtered = self._filter_messages_for_memory(messages)

        user_msgs = [m for m in filtered if getattr(m, "type", None) == "human"]
        assistant_msgs = [m for m in filtered if getattr(m, "type", None) == "ai"]

        if not user_msgs or not assistant_msgs:
            return MiddlewareResult()

        memory_update = {
            "thread_id": context.thread_id,
            "messages": [
                {"role": "user" if m.type == "human" else "assistant", "content": str(m.content)[:1000]}
                for m in filtered[-20:]
            ],
        }

        logger.debug("Queued memory update for thread %s", context.thread_id)

        return MiddlewareResult(
            state_update={"memory_update": memory_update},
            metadata={"memory_queued": True},
        )
