"""Title middleware for automatic thread title generation."""

import logging
from typing import Any

from src.execution.context import ExecutionContext
from src.execution.middlewares import BaseMiddleware, MiddlewarePhase, MiddlewareResult
from src.llm.client import get_llm_client

logger = logging.getLogger(__name__)

TITLE_PROMPT = """Generate a short, descriptive title (max 10 words) for this conversation.

User message: {user_msg}
Assistant response: {assistant_msg}

Title:"""


class TitleMiddleware(BaseMiddleware):
    """Middleware that automatically generates thread titles.

    Generates a title after the first complete exchange
    (user message + assistant response).
    """

    name = "title"
    priority = 50
    phases = [MiddlewarePhase.AFTER_MODEL]

    def __init__(
        self,
        enabled: bool = True,
        max_words: int = 10,
        max_chars: int = 100,
        model_name: str = "gpt-3.5-turbo",
    ):
        super().__init__()
        self.enabled = enabled
        self._max_words = max_words
        self._max_chars = max_chars
        self._model_name = model_name

    def _normalize_content(self, content: Any) -> str:
        """Normalize message content to string.

        Args:
            content: Message content (str, list, or dict).

        Returns:
            Normalized string content.
        """
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [self._normalize_content(item) for item in content]
            return "\n".join(part for part in parts if part)
        if isinstance(content, dict):
            text = content.get("text", "")
            if text:
                return str(text)
            nested = content.get("content")
            if nested:
                return self._normalize_content(nested)
        return ""

    def _should_generate_title(self, state: dict[str, Any]) -> bool:
        """Check if title should be generated.

        Args:
            state: Current state.

        Returns:
            True if title generation is needed.
        """
        if not self.enabled:
            return False
        if state.get("title"):
            return False

        messages = state.get("messages", [])
        if len(messages) < 2:
            return False

        user_msgs = [m for m in messages if getattr(m, "type", None) == "human"]
        assistant_msgs = [m for m in messages if getattr(m, "type", None) == "ai"]

        return len(user_msgs) == 1 and len(assistant_msgs) >= 1

    def _generate_title(self, user_msg: str, assistant_msg: str) -> str:
        """Generate title using LLM.

        Args:
            user_msg: User message content.
            assistant_msg: Assistant message content.

        Returns:
            Generated title.
        """
        try:
            client = get_llm_client()
            prompt = TITLE_PROMPT.format(
                user_msg=user_msg[:500],
                assistant_msg=assistant_msg[:500],
            )
            response = client.chat(prompt, model=self._model_name)
            title = response.strip().strip('"\'')[: self._max_chars]
            return title if title else self._fallback_title(user_msg)
        except Exception as e:
            logger.warning("Failed to generate title: %s", e)
            return self._fallback_title(user_msg)

    def _fallback_title(self, user_msg: str) -> str:
        """Generate fallback title from user message.

        Args:
            user_msg: User message content.

        Returns:
            Fallback title.
        """
        max_chars = min(self._max_chars, 50)
        if len(user_msg) > max_chars:
            return user_msg[:max_chars].rstrip() + "..."
        return user_msg if user_msg else "New Conversation"

    def process(
        self,
        phase: MiddlewarePhase,
        state: dict[str, Any],
        context: ExecutionContext,
    ) -> MiddlewareResult:
        if not self._should_generate_title(state):
            return MiddlewareResult()

        messages = state.get("messages", [])
        user_msg = next(
            (self._normalize_content(m.content) for m in messages if getattr(m, "type", None) == "human"),
            "",
        )
        assistant_msg = next(
            (self._normalize_content(m.content) for m in messages if getattr(m, "type", None) == "ai"),
            "",
        )

        title = self._generate_title(user_msg, assistant_msg)
        logger.info("Generated thread title: %s", title)

        return MiddlewareResult(state_update={"title": title})
