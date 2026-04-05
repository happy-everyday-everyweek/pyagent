"""Thread data middleware for managing per-thread directories."""

import logging
from pathlib import Path
from typing import Any

from src.execution.context import ExecutionContext
from src.execution.middlewares import BaseMiddleware, MiddlewarePhase, MiddlewareResult

logger = logging.getLogger(__name__)


class ThreadDataMiddleware(BaseMiddleware):
    """Middleware that creates and manages thread-specific directories.

    Creates the following directory structure:
    - {base_dir}/threads/{thread_id}/workspace
    - {base_dir}/threads/{thread_id}/uploads
    - {base_dir}/threads/{thread_id}/outputs

    This provides isolated working directories for each thread.
    """

    name = "thread_data"
    priority = 10
    phases = [MiddlewarePhase.BEFORE_AGENT]

    def __init__(self, base_dir: str | None = None, lazy_init: bool = True):
        super().__init__()
        self._base_dir = Path(base_dir) if base_dir else Path("data/threads")
        self._lazy_init = lazy_init

    def _get_thread_paths(self, thread_id: str) -> dict[str, str]:
        """Get paths for thread directories.

        Args:
            thread_id: Thread identifier.

        Returns:
            Dictionary with workspace, uploads, and outputs paths.
        """
        thread_dir = self._base_dir / thread_id
        return {
            "workspace_path": str(thread_dir / "workspace"),
            "uploads_path": str(thread_dir / "uploads"),
            "outputs_path": str(thread_dir / "outputs"),
        }

    def _create_thread_directories(self, thread_id: str) -> dict[str, str]:
        """Create thread directories.

        Args:
            thread_id: Thread identifier.

        Returns:
            Dictionary with created directory paths.
        """
        paths = self._get_thread_paths(thread_id)
        for path in paths.values():
            Path(path).mkdir(parents=True, exist_ok=True)
        logger.debug("Created thread directories for %s", thread_id)
        return paths

    def process(
        self,
        phase: MiddlewarePhase,
        state: dict[str, Any],
        context: ExecutionContext,
    ) -> MiddlewareResult:
        if not context.thread_id:
            return MiddlewareResult(error="Thread ID is required")

        if self._lazy_init:
            paths = self._get_thread_paths(context.thread_id)
        else:
            paths = self._create_thread_directories(context.thread_id)

        for key, value in paths.items():
            context.set(key, value)

        return MiddlewareResult(state_update={"thread_data": paths})
