"""Clarification middleware for handling ambiguous requests."""

import logging
from typing import Any

from src.execution.context import ExecutionContext
from src.execution.middlewares import BaseMiddleware, MiddlewarePhase, MiddlewareResult

logger = logging.getLogger(__name__)

CLARIFICATION_KEYWORDS = [
    "clarify",
    "clarification",
    "unclear",
    "ambiguous",
    "specify",
    "what do you mean",
    "can you explain",
]


class ClarificationMiddleware(BaseMiddleware):
    """Middleware that handles clarification requests.

    Detects when the agent needs clarification and manages
    the clarification flow.
    """

    name = "clarification"
    priority = 80
    phases = [MiddlewarePhase.AFTER_MODEL]

    def __init__(self, enabled: bool = True, max_clarifications: int = 3):
        super().__init__()
        self.enabled = enabled
        self._max_clarifications = max_clarifications

    def _needs_clarification(self, content: str) -> bool:
        """Check if content indicates need for clarification.

        Args:
            content: Message content.

        Returns:
            True if clarification is needed.
        """
        content_lower = content.lower()
        return any(kw in content_lower for kw in CLARIFICATION_KEYWORDS)

    def _extract_clarification_question(self, content: str) -> str | None:
        """Extract clarification question from content.

        Args:
            content: Message content.

        Returns:
            Extracted question or None.
        """
        sentences = content.split("?")
        for sentence in sentences:
            if any(kw in sentence.lower() for kw in CLARIFICATION_KEYWORDS):
                return sentence.strip() + "?" if not sentence.endswith("?") else sentence.strip()
        return None

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

        last_msg = messages[-1]
        content = getattr(last_msg, "content", "")

        if not isinstance(content, str):
            return MiddlewareResult()

        if self._needs_clarification(content):
            question = self._extract_clarification_question(content)
            clarification_count = state.get("clarification_count", 0) + 1

            if clarification_count > self._max_clarifications:
                logger.warning("Max clarifications reached for thread %s", context.thread_id)
                return MiddlewareResult(
                    state_update={"clarification_count": clarification_count, "needs_clarification": False},
                    metadata={"max_clarifications_reached": True},
                )

            logger.debug("Clarification needed: %s", question)

            return MiddlewareResult(
                state_update={
                    "needs_clarification": True,
                    "clarification_question": question,
                    "clarification_count": clarification_count,
                }
            )

        return MiddlewareResult(state_update={"needs_clarification": False})
