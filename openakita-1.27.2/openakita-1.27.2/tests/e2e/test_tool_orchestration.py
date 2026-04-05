"""
L4 E2E Tests: Multi-step tool orchestration scenarios.

Tests that the agent can chain multiple tool calls in sequence,
using MockLLMClient with preset ReAct sequences.
"""

import pytest

from openakita.llm.types import StopReason
from tests.fixtures.mock_llm import MockBrain, MockLLMClient, MockResponse


@pytest.fixture
def orchestration_brain():
    client = MockLLMClient()
    return MockBrain(client), client


class TestSearchThenRead:
    async def test_search_then_read_file(self, orchestration_brain):
        """Agent searches for a file, then reads it."""
        brain, client = orchestration_brain
        client.preset_sequence([
            MockResponse(
                content="Let me search for the file first.",
                tool_calls=[{"name": "search_files", "input": {"query": "config.py"}}],
            ),
            MockResponse(
                content="Found it, let me read it.",
                tool_calls=[{"name": "read_file", "input": {"path": "src/config.py"}}],
            ),
            MockResponse(content="The config file contains database settings and API keys."),
        ])

        messages = [{"role": "user", "content": "Show me the config file"}]

        r1 = await brain.messages_create_async(messages=messages)
        assert r1.stop_reason == StopReason.TOOL_USE

        messages.append({"role": "assistant", "content": [
            {"type": "text", "text": "Let me search for the file first."},
            {"type": "tool_use", "id": "t1", "name": "search_files", "input": {"query": "config.py"}},
        ]})
        messages.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": "Found: src/config.py"},
        ]})

        r2 = await brain.messages_create_async(messages=messages)
        assert r2.stop_reason == StopReason.TOOL_USE

        messages.append({"role": "assistant", "content": [
            {"type": "text", "text": "Found it, let me read it."},
            {"type": "tool_use", "id": "t2", "name": "read_file", "input": {"path": "src/config.py"}},
        ]})
        messages.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t2", "content": "DB_HOST=localhost\nAPI_KEY=sk-xxx"},
        ]})

        r3 = await brain.messages_create_async(messages=messages)
        assert r3.stop_reason == StopReason.END_TURN
        assert "config" in r3.content[0].text.lower() or "database" in r3.content[0].text.lower()


class TestWriteThenVerify:
    async def test_write_then_verify(self, orchestration_brain):
        """Agent writes a file, then reads it back to verify."""
        brain, client = orchestration_brain
        client.preset_sequence([
            MockResponse(
                content="I'll write the file now.",
                tool_calls=[{"name": "write_file", "input": {"path": "test.txt", "content": "hello"}}],
            ),
            MockResponse(
                content="Let me verify by reading it back.",
                tool_calls=[{"name": "read_file", "input": {"path": "test.txt"}}],
            ),
            MockResponse(content="File written and verified successfully. Contains 'hello'."),
        ])

        r1 = await brain.messages_create_async(
            messages=[{"role": "user", "content": "Write 'hello' to test.txt and verify"}],
        )
        assert r1.stop_reason == StopReason.TOOL_USE
        assert client.total_calls == 1

        # Simulate tool results and continue
        r2 = await brain.messages_create_async(messages=[
            {"role": "user", "content": "Write 'hello' to test.txt and verify"},
            {"role": "assistant", "content": [
                {"type": "tool_use", "id": "t1", "name": "write_file", "input": {"path": "test.txt", "content": "hello"}},
            ]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "File written."}]},
        ])
        assert r2.stop_reason == StopReason.TOOL_USE

        r3 = await brain.messages_create_async(messages=[
            {"role": "user", "content": "result"},
            {"role": "assistant", "content": [
                {"type": "tool_use", "id": "t2", "name": "read_file", "input": {"path": "test.txt"}},
            ]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t2", "content": "hello"}]},
        ])
        assert r3.stop_reason == StopReason.END_TURN
        assert "hello" in r3.content[0].text.lower()


class TestMultipleParallelTools:
    async def test_parallel_tool_calls(self, orchestration_brain):
        """Agent calls multiple tools in a single turn."""
        brain, client = orchestration_brain
        client.preset_sequence([
            MockResponse(
                content="Let me search both.",
                tool_calls=[
                    {"name": "search_memory", "input": {"query": "Python"}},
                    {"name": "search_memory", "input": {"query": "JavaScript"}},
                ],
            ),
            MockResponse(content="Found 3 Python memories and 2 JavaScript memories."),
        ])

        r1 = await brain.messages_create_async(
            messages=[{"role": "user", "content": "Search memories for Python and JavaScript"}],
        )
        assert r1.stop_reason == StopReason.TOOL_USE
        from openakita.llm.types import ToolUseBlock
        tool_blocks = [b for b in r1.content if isinstance(b, ToolUseBlock)]
        assert len(tool_blocks) == 2


class TestToolChainLength:
    async def test_five_step_chain(self, orchestration_brain):
        """Agent completes a 5-step tool chain."""
        brain, client = orchestration_brain
        for i in range(4):
            client.preset_response(
                content=f"Step {i+1} done.",
                tool_calls=[{"name": f"tool_{i+1}", "input": {"step": i+1}}],
            )
        client.preset_response(content="All 5 steps completed successfully.")

        for i in range(5):
            r = await brain.messages_create_async(
                messages=[{"role": "user", "content": f"step {i}"}],
            )
            if i < 4:
                assert r.stop_reason == StopReason.TOOL_USE
            else:
                assert r.stop_reason == StopReason.END_TURN

        assert client.total_calls == 5
