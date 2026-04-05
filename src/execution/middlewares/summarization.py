"""Summarization middleware for context compression."""

import logging
from typing import Any

from src.execution.context import ExecutionContext
from src.execution.middlewares import BaseMiddleware, MiddlewarePhase, MiddlewareResult

logger = logging.getLogger(__name__)


class SummarizationMiddleware(BaseMiddleware):
    """Middleware that summarizes conversation context.

    When context exceeds a threshold, this middleware:
    - Identifies older messages to summarize
    - Generates a summary using LLM
    - Replaces summarized messages with the summary
    """

    name = "summarization"
    priority = 30
    phases = [MiddlewarePhase.BEFORE_MODEL]

    def __init__(
        self,
        max_messages: int = 50,
        summary_threshold: int = 40,
        enabled: bool = True,
    ):
        super().__init__()
        self._max_messages = max_messages
        self._summary_threshold = summary_threshold
        self.enabled = enabled

    def _should_summarize(self, messages: list[Any]) -> bool:
        """Check if summarization is needed.

        Args:
            messages: Current message list.

        Returns:
            True if summarization should occur.
        """
        return len(messages) > self._summary_threshold

    def _get_messages_to_summarize(self, messages: list[Any]) -> tuple[list[Any], list[Any]]:
        """Split messages into those to summarize and those to keep.

        Args:
            messages: All messages.

        Returns:
            Tuple of (messages_to_summarize, messages_to_keep).
        """
        keep_count = self._max_messages - self._summary_threshold
        return messages[:-keep_count], messages[-keep_count:]

    def _generate_summary(self, messages: list[Any]) -> str:
        """Generate a summary of messages.

        Args:
            messages: Messages to summarize.

        Returns:
            Summary text.
        """
        content_parts = []
        for msg in messages[:20]:
            content = getattr(msg, "content", "")
            if isinstance(content, str):
                content_parts.append(content[:200])

        if not content_parts:
            return "[Previous conversation summarized]"

        return f"[Previous conversation summary: {'; '.join(content_parts[:5])}...]"

    def process(
        self,
        phase: MiddlewarePhase,
        state: dict[str, Any],
        context: ExecutionContext,
    ) -> MiddlewareResult:
        if not self.enabled:
            return MiddlewareResult()

        messages = state.get("messages", [])
        if not self._should_summarize(messages):
            return MiddlewareResult()

        to_summarize, to_keep = self._get_messages_to_summarize(messages)
        summary = self._generate_summary(to_summarize)

        summary_msg = {"role": "system", "content": summary}
        new_messages = [summary_msg] + to_keep

        logger.info(
            "Summarized %d messages, keeping %d recent messages",
            len(to_summarize),
            len(to_keep),
        )

        return MiddlewareResult(state_update={"messages": new_messages})
