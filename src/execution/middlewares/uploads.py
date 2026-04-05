"""Uploads middleware for handling file attachments."""

import logging
import re
from typing import Any

from src.execution.context import ExecutionContext
from src.execution.middlewares import BaseMiddleware, MiddlewarePhase, MiddlewareResult

logger = logging.getLogger(__name__)

UPLOAD_BLOCK_RE = re.compile(r"<uploaded_files>[\s\S]*?</uploaded_files>\n*", re.IGNORECASE)


class UploadsMiddleware(BaseMiddleware):
    """Middleware that processes file uploads in messages.

    Handles:
    - Extracting file paths from upload blocks
    - Injecting file information into context
    - Filtering upload blocks from memory
    """

    name = "uploads"
    priority = 20
    phases = [MiddlewarePhase.BEFORE_AGENT, MiddlewarePhase.BEFORE_MODEL]

    def __init__(self, max_file_size_mb: int = 100):
        super().__init__()
        self._max_file_size = max_file_size_mb * 1024 * 1024

    def _extract_uploads(self, content: str) -> list[dict[str, Any]]:
        """Extract upload information from content.

        Args:
            content: Message content to parse.

        Returns:
            List of upload metadata dictionaries.
        """
        uploads = []
        matches = UPLOAD_BLOCK_RE.findall(content)
        for match in matches:
            path_matches = re.findall(r"path:\s*([^\n]+)", match)
            for path in path_matches:
                uploads.append({"path": path.strip()})
        return uploads

    def _strip_upload_blocks(self, content: str) -> str:
        """Remove upload blocks from content.

        Args:
            content: Message content.

        Returns:
            Content with upload blocks removed.
        """
        return UPLOAD_BLOCK_RE.sub("", content).strip()

    def process(
        self,
        phase: MiddlewarePhase,
        state: dict[str, Any],
        context: ExecutionContext,
    ) -> MiddlewareResult:
        messages = state.get("messages", [])
        if not messages:
            return MiddlewareResult()

        all_uploads = []
        cleaned_messages = []

        for msg in messages:
            content = getattr(msg, "content", "")
            if isinstance(content, str) and "<uploaded_files>" in content:
                uploads = self._extract_uploads(content)
                all_uploads.extend(uploads)

                cleaned_content = self._strip_upload_blocks(content)
                if cleaned_content:
                    if hasattr(msg, "content"):
                        msg.content = cleaned_content
                    cleaned_messages.append(msg)
            else:
                cleaned_messages.append(msg)

        if all_uploads:
            context.set("uploads", all_uploads)
            logger.debug("Processed %d file uploads", len(all_uploads))

        return MiddlewareResult(
            state_update={
                "messages": cleaned_messages,
                "uploads": all_uploads,
            }
        )
