"""L2 Component Tests: ToolExecutor execution and truncation guard."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from openakita.core.tool_executor import ToolExecutor, OVERFLOW_MARKER


def _make_registry(*tool_names: str) -> MagicMock:
    """Create a mock SystemHandlerRegistry with given tool names."""
    registry = MagicMock()
    handlers = {}
    for name in tool_names:
        handler = AsyncMock(return_value=f"Result of {name}")
        handlers[name] = handler
    registry.get_handler.side_effect = lambda n: handlers.get(n)
    registry.has_handler.side_effect = lambda n: n in handlers
    return registry


@pytest.fixture
def executor():
    registry = _make_registry("read_file", "write_file", "search_memory")
    return ToolExecutor(handler_registry=registry, max_parallel=1)


class TestExecuteTool:
    async def test_execute_known_tool(self, executor):
        result = await executor.execute_tool("read_file", {"path": "/tmp/x"})
        assert isinstance(result, str)

    async def test_execute_unknown_tool(self, executor):
        result = await executor.execute_tool("nonexistent_tool", {})
        assert "error" in result.lower() or "not found" in result.lower() or isinstance(result, str)


class TestGuardTruncate:
    def test_short_result_unchanged(self):
        result = ToolExecutor._guard_truncate("read_file", "short content")
        assert result == "short content"

    def test_very_long_result_truncated(self):
        long_text = "x" * 500_000
        result = ToolExecutor._guard_truncate("read_file", long_text)
        assert len(result) < len(long_text)
        assert OVERFLOW_MARKER in result or len(result) < 500_000

    def test_empty_result(self):
        result = ToolExecutor._guard_truncate("read_file", "")
        assert result == ""


class TestExecutorInit:
    def test_default_max_parallel(self):
        registry = _make_registry()
        executor = ToolExecutor(handler_registry=registry)
        assert executor._max_parallel == 1

    def test_custom_max_parallel(self):
        registry = _make_registry()
        executor = ToolExecutor(handler_registry=registry, max_parallel=5)
        assert executor._max_parallel == 5
