"""View image middleware for image processing."""

import logging
import re
from typing import Any

from src.execution.context import ExecutionContext
from src.execution.middlewares import BaseMiddleware, MiddlewarePhase, MiddlewareResult

logger = logging.getLogger(__name__)

IMAGE_PATH_RE = re.compile(r"!\[.*?\]\(([^)]+)\)")
IMAGE_FILE_RE = re.compile(r"\.(png|jpg|jpeg|gif|webp|bmp)$", re.IGNORECASE)


class ViewImageMiddleware(BaseMiddleware):
    """Middleware that processes image references in messages.

    Handles:
    - Detecting image paths in messages
    - Loading image data for multimodal models
    - Providing image context to the agent
    """

    name = "view_image"
    priority = 70
    phases = [MiddlewarePhase.BEFORE_MODEL]

    def __init__(self, enabled: bool = True, max_images: int = 10):
        super().__init__()
        self.enabled = enabled
        self._max_images = max_images

    def _extract_image_paths(self, content: str) -> list[str]:
        """Extract image paths from content.

        Args:
            content: Message content.

        Returns:
            List of image paths.
        """
        paths = []
        for match in IMAGE_PATH_RE.findall(content):
            if IMAGE_FILE_RE.search(match):
                paths.append(match)
        return paths[: self._max_images]

    def _load_image_data(self, path: str) -> dict[str, Any] | None:
        """Load image data from path.

        Args:
            path: Image file path.

        Returns:
            Image data dictionary or None if failed.
        """
        try:
            from pathlib import Path

            p = Path(path)
            if not p.exists():
                return None

            return {
                "path": str(p),
                "size": p.stat().st_size,
                "name": p.name,
            }
        except Exception as e:
            logger.warning("Failed to load image %s: %s", path, e)
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
        all_images = []

        for msg in messages:
            content = getattr(msg, "content", "")
            if isinstance(content, str):
                paths = self._extract_image_paths(content)
                for path in paths:
                    img_data = self._load_image_data(path)
                    if img_data:
                        all_images.append(img_data)

        if all_images:
            context.set("images", all_images)
            logger.debug("Processed %d images", len(all_images))

        return MiddlewareResult(state_update={"images": all_images})
