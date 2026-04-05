"""L4 E2E Tests: Multi-step complex tasks — simulating real agent task chains.

Tests realistic multi-step scenarios that chain tool calls, context, memory,
and reasoning across multiple iterations. Uses MockLLMClient to control the
exact LLM response sequence.
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "fixtures"))
from mock_llm import MockLLMClient, MockResponse, MockBrain

from openakita.core.task_monitor import TaskMonitor, TaskMetrics
from openakita.core.ralph import Task, TaskResult, TaskStatus


class TestSearchThenSummarize:
    """Simulate: user asks question → agent searches → reads results → summarizes."""

    def test_task_monitor_tracks_multistep(self):
        tm = TaskMonitor(task_id="multi-1", description="Search and summarize")
        tm.start(model="gpt-4")

        # Step 1: Search
        tm.begin_iteration(1, model="gpt-4")
        tm.record_tool_call("web_search", {"query": "Python GIL"}, "Results: ...", success=True, duration_ms=500)
        tm.end_iteration(llm_response_preview="Found info about GIL")

        # Step 2: Read
        tm.begin_iteration(2, model="gpt-4")
        tm.record_tool_call("read_file", {"path": "notes.md"}, "# GIL Notes", success=True, duration_ms=50)
        tm.end_iteration(llm_response_preview="Read the notes")

        # Step 3: Summarize
        tm.begin_iteration(3, model="gpt-4")
        tm.end_iteration(llm_response_preview="GIL 是 Python 的全局解释器锁...")

        metrics = tm.complete(success=True, response="Summary generated")
        assert metrics.total_iterations == 3
        assert metrics.success is True

    def test_mock_llm_chain(self):
        client = MockLLMClient()
        client.preset_sequence([
            MockResponse(
                content="",
                tool_calls=[{"name": "web_search", "input": {"query": "Python GIL"}}],
            ),
            MockResponse(content="Python 的 GIL（全局解释器锁）是一个互斥锁..."),
        ])

        r1 = client.chat_sync([{"role": "user", "content": "什么是GIL"}])
        assert r1.tool_calls is not None
        assert r1.tool_calls[0].name == "web_search"

        r2 = client.chat_sync([{"role": "user", "content": "什么是GIL"}])
        text = r2.content[0].text if hasattr(r2.content, '__iter__') and r2.content else str(r2.content)
        assert "GIL" in text
        assert client.total_calls == 2


class TestWriteVerifyLoop:
    """Simulate: agent writes file → reads back to verify → confirms."""

    def test_write_then_verify(self):
        client = MockLLMClient()
        client.preset_sequence([
            MockResponse(
                content="",
                tool_calls=[{"name": "write_file", "input": {"path": "/tmp/test.py", "content": "print('hello')"}}],
            ),
            MockResponse(
                content="",
                tool_calls=[{"name": "read_file", "input": {"path": "/tmp/test.py"}}],
            ),
            MockResponse(content="文件已创建并验证成功。"),
        ])

        r1 = client.chat_sync([{"role": "user", "content": "创建 test.py"}])
        assert r1.tool_calls[0].name == "write_file"

        r2 = client.chat_sync([{"role": "tool", "content": "OK"}])
        assert r2.tool_calls[0].name == "read_file"

        r3 = client.chat_sync([{"role": "tool", "content": "print('hello')"}])
        text = r3.content[0].text if hasattr(r3.content, '__iter__') and r3.content else str(r3.content)
        assert "成功" in text or "验证" in text


class TestRalphTaskPersistence:
    """Test Ralph loop's task state transitions through a multi-attempt task."""

    def test_retry_on_failure(self):
        task = Task(id="ralph-1", description="Complex task", max_attempts=3)
        assert task.can_retry is True

        # Attempt 1: fails
        task.mark_in_progress()
        task.attempts = 1
        task.mark_failed("LLM returned invalid JSON")
        assert task.can_retry is True

        # Attempt 2: fails
        task.mark_in_progress()
        task.attempts = 2
        task.mark_failed("Timeout")
        assert task.can_retry is True

        # Attempt 3: succeeds
        task.mark_in_progress()
        task.attempts = 3
        task.mark_completed(result="Finally done")
        assert task.is_complete is True
        assert task.result == "Finally done"

    def test_max_attempts_reached(self):
        task = Task(id="ralph-2", description="Failing task", max_attempts=2)
        task.attempts = 2
        assert task.can_retry is False


class TestModelSwitchDuringTask:
    """Simulate model switch mid-task due to errors."""

    def test_monitor_tracks_switch(self):
        tm = TaskMonitor(task_id="switch-1", description="Switch test")
        tm.start(model="gpt-4")

        # First attempt with gpt-4 fails
        tm.begin_iteration(1, model="gpt-4")
        tm.record_tool_call("web_search", {"query": "test"}, "Error: rate limited", success=False, duration_ms=1000)
        tm.end_iteration()
        tm.record_error("Rate limit exceeded")

        # Switch to claude-3
        tm.switch_model("claude-3", reason="rate_limit")
        assert tm.current_model == "claude-3"

        # Retry succeeds
        tm.begin_iteration(2, model="claude-3")
        tm.end_iteration(llm_response_preview="Success with claude-3")

        metrics = tm.complete(success=True, response="Done")
        assert metrics.model_switched is True
        assert metrics.initial_model == "gpt-4"
        assert metrics.final_model == "claude-3"


class TestContextAccumulationAcrossSteps:
    """Verify conversation context grows correctly across multi-step interactions."""

    def test_context_builds_up(self):
        client = MockLLMClient()
        messages = []

        def _text(r):
            """Extract text from LLMResponse."""
            if hasattr(r.content, '__iter__') and r.content:
                return r.content[0].text
            return str(r.content)

        messages.append({"role": "user", "content": "帮我分析项目结构"})
        client.preset_response("我来帮你分析。先看一下目录...")
        r1 = client.chat_sync(messages)
        messages.append({"role": "assistant", "content": _text(r1)})
        assert len(messages) == 2

        messages.append({"role": "user", "content": "重点看 src 目录"})
        client.preset_response("src 目录下有以下模块...")
        r2 = client.chat_sync(messages)
        messages.append({"role": "assistant", "content": _text(r2)})
        assert len(messages) == 4
        assert client.total_calls == 2

        messages.append({"role": "user", "content": "总结一下"})
        client.preset_response("总结：项目包含核心模块、工具系统、记忆系统...")
        r3 = client.chat_sync(messages)
        assert "总结" in _text(r3)
        assert client.total_calls == 3


class TestToolChainWithMemory:
    """Simulate tool chain that involves memory operations."""

    def test_search_remember_recall(self):
        client = MockLLMClient()

        client.preset_sequence([
            MockResponse(content="", tool_calls=[
                {"name": "web_search", "input": {"query": "OpenAkita features"}},
            ]),
            MockResponse(content="", tool_calls=[
                {"name": "remember", "input": {"content": "OpenAkita 是一个 AI Agent 框架", "importance": 4}},
            ]),
            MockResponse(content="我已经搜索并记住了 OpenAkita 的特性。"),
        ])

        r1 = client.chat_sync([{"role": "user", "content": "了解一下 OpenAkita"}])
        assert r1.tool_calls[0].name == "web_search"

        r2 = client.chat_sync([{"role": "tool", "content": "OpenAkita is an AI agent framework"}])
        assert r2.tool_calls[0].name == "remember"

        r3 = client.chat_sync([{"role": "tool", "content": "Memory saved"}])
        text = r3.content[0].text if hasattr(r3.content, '__iter__') and r3.content else str(r3.content)
        assert "记住" in text or "OpenAkita" in text
