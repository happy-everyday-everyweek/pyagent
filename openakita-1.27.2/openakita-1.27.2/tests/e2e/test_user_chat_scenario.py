"""
L4 E2E Tests: Real user chat scenarios via Agent.chat() full pipeline.

These tests simulate what happens when a real user sends messages.
The Agent walks the full pipeline:
  User Input → Session → Prompt Compiler → Context Builder → ReasoningEngine → LLM → Response
Only the LLM backend is mocked (MockLLMClient); everything else runs as real code.
"""

import asyncio
import os
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.fixtures.mock_llm import MockBrain, MockLLMClient, MockResponse


def _create_test_workspace(tmp_path: Path) -> Path:
    """Build a minimal workspace with all dirs Agent expects."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "data").mkdir()
    (ws / "data" / "memory").mkdir()
    (ws / "logs").mkdir()
    (ws / "skills").mkdir()

    identity = ws / "identity"
    identity.mkdir()
    (identity / "SOUL.md").write_text("# Soul\nYou are OpenAkita, a loyal AI assistant.", encoding="utf-8")
    (identity / "AGENT.md").write_text("# Agent\n## Core\nBe helpful.\n## Tooling\nUse tools.", encoding="utf-8")
    (identity / "USER.md").write_text("# User\nTest user.", encoding="utf-8")
    (identity / "personas").mkdir()
    (identity / "personas" / "default.md").write_text("# Default\nFriendly.", encoding="utf-8")

    (ws / "data" / "memory" / "MEMORY.md").write_text("", encoding="utf-8")
    (identity / "MEMORY.md").write_text("", encoding="utf-8")

    # Minimal llm_endpoints.json so Brain can initialize
    import json
    llm_config = [
        {
            "name": "mock-endpoint",
            "base_url": "http://localhost:1234/v1",
            "api_key": "sk-test",
            "model": "mock-model",
            "provider": "openai",
            "context_window": 128000,
            "enabled": True,
        }
    ]
    (ws / "llm_endpoints.json").write_text(json.dumps(llm_config), encoding="utf-8")

    return ws


def _inject_mock_brain(agent, mock_client: MockLLMClient):
    """Replace all brain references in Agent's sub-modules with MockBrain."""
    mock_brain = MockBrain(mock_client)
    mock_brain.max_tokens = 4096
    mock_brain._llm_client = mock_client
    mock_brain.is_thinking_enabled = lambda: False
    mock_brain._thinking_enabled = False
    mock_brain.get_fallback_model = lambda *a, **kw: ""
    mock_brain.restore_default_model = lambda *a, **kw: (True, "ok")
    mock_brain.get_current_model_info = lambda: {"name": "mock", "model": "mock"}
    mock_brain.get_current_endpoint_info = lambda: {"name": "mock"}
    mock_brain.switch_model = lambda *a, **kw: (True, "switched")

    agent.brain = mock_brain
    agent.reasoning_engine._brain = mock_brain
    agent.context_manager._brain = mock_brain
    agent.response_handler.brain = mock_brain
    agent.prompt_assembler._brain = mock_brain


@pytest.fixture
def test_workspace(tmp_path):
    return _create_test_workspace(tmp_path)


@pytest.fixture
def mock_client():
    return MockLLMClient()


@pytest.fixture
async def user_agent(test_workspace, mock_client, monkeypatch):
    """Create a real Agent with mocked LLM, ready for user scenario testing."""
    monkeypatch.setenv("OPENAKITA_PROJECT_ROOT", str(test_workspace))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-placeholder")

    import openakita.config as config_mod
    from openakita.config import Settings
    test_settings = Settings(
        project_root=test_workspace,
        database_path="data/agent.db",
        log_dir=str(test_workspace / "logs"),
        log_level="WARNING",
        max_iterations=10,
        thinking_mode="never",
    )
    monkeypatch.setattr(config_mod, "settings", test_settings)

    from openakita.core.agent import Agent
    agent = Agent(name="TestAgent")

    _inject_mock_brain(agent, mock_client)

    # Skip heavy initialization (MCP, scheduler, skills loading)
    # but mark as initialized so chat() works
    agent._initialized = True
    agent.identity.load()

    yield agent


class TestUserSendsFirstMessage:
    """Simulate: user opens app → types first message → gets response."""

    async def test_simple_greeting(self, user_agent, mock_client):
        mock_client.preset_response("你好！我是 OpenAkita，有什么可以帮你的？")

        response = await user_agent.chat("你好")

        assert isinstance(response, str)
        assert len(response) > 0
        assert mock_client.total_calls >= 1

    async def test_response_is_meaningful(self, user_agent, mock_client):
        mock_client.preset_response("Python 是一种高级编程语言，由 Guido van Rossum 创建。")

        response = await user_agent.chat("Python是什么？")

        assert "Python" in response or "编程" in response

    async def test_stop_command_returns_immediately(self, user_agent, mock_client):
        """User sends '停止' → should get immediate stop response, no LLM call."""
        response = await user_agent.chat("停止")

        assert "停止" in response or "已停止" in response
        assert mock_client.total_calls == 0  # LLM should NOT be called


class TestMultiTurnConversation:
    """Simulate: user has a back-and-forth conversation."""

    async def test_two_turn_context_flows_through(self, user_agent, mock_client):
        """User asks Q1, then Q2 → Agent should see both in history."""
        mock_client.preset_sequence([
            MockResponse(content="我是 OpenAkita！"),
            MockResponse(content="你之前问了我是谁。"),
        ])

        r1 = await user_agent.chat("你是谁？")
        assert "OpenAkita" in r1

        r2 = await user_agent.chat("我刚才问了什么？")
        assert isinstance(r2, str)
        assert mock_client.total_calls == 2

        # Verify the second call received conversation history
        second_call = mock_client.call_log[1]
        all_content = str(second_call["messages"])
        assert "你是谁" in all_content or len(second_call["messages"]) > 1

    async def test_three_turns_accumulate(self, user_agent, mock_client):
        mock_client.preset_sequence([
            MockResponse(content="A1"),
            MockResponse(content="A2"),
            MockResponse(content="A3"),
        ])

        await user_agent.chat("Q1")
        await user_agent.chat("Q2")
        await user_agent.chat("Q3")

        assert mock_client.total_calls == 3


class TestToolCallScenario:
    """Simulate: user asks something that requires a tool call."""

    async def test_user_asks_to_read_file(self, user_agent, mock_client):
        """Agent decides to use a tool, then gives final answer."""
        mock_client.preset_sequence([
            MockResponse(
                content="让我帮你读取文件。",
                tool_calls=[{
                    "name": "read_file",
                    "input": {"target_file": "/tmp/test.txt"},
                }],
            ),
            MockResponse(content="文件内容是：Hello World"),
        ])

        # Note: the tool call will fail (no real file), but the Agent should handle it
        # and continue to produce a response
        response = await user_agent.chat("帮我读取 /tmp/test.txt")
        assert isinstance(response, str)
        assert len(response) > 0

    async def test_user_asks_to_search_memory(self, user_agent, mock_client):
        """Agent uses memory search tool."""
        mock_client.preset_sequence([
            MockResponse(
                content="让我搜索一下。",
                tool_calls=[{
                    "name": "search_memory",
                    "input": {"query": "用户生日"},
                }],
            ),
            MockResponse(content="没有找到关于你生日的记录。"),
        ])

        response = await user_agent.chat("你还记得我的生日吗？")
        assert isinstance(response, str)


class TestSessionPersistence:
    """Verify that session state persists across chat() calls."""

    async def test_session_messages_grow(self, user_agent, mock_client):
        mock_client.set_default_response("OK")

        await user_agent.chat("msg1")
        await user_agent.chat("msg2")
        await user_agent.chat("msg3")

        # CLI session should have accumulated messages
        session = user_agent._cli_session
        messages = session.context.get_messages()
        # Each turn adds user + assistant = 2 messages × 3 turns = at least 6
        assert len(messages) >= 6

    async def test_session_id_stable(self, user_agent, mock_client):
        mock_client.set_default_response("OK")

        await user_agent.chat("first")
        sid1 = user_agent._cli_session.id

        await user_agent.chat("second")
        sid2 = user_agent._cli_session.id

        assert sid1 == sid2  # Same session across turns


class TestEdgeCases:
    """Edge cases a real user might trigger."""

    async def test_empty_message(self, user_agent, mock_client):
        mock_client.set_default_response("请问有什么可以帮你的？")
        response = await user_agent.chat("")
        assert isinstance(response, str)

    async def test_very_long_message(self, user_agent, mock_client):
        mock_client.set_default_response("收到了你的长消息。")
        long_msg = "测试消息。" * 500
        response = await user_agent.chat(long_msg)
        assert isinstance(response, str)

    async def test_special_characters(self, user_agent, mock_client):
        mock_client.set_default_response("没问题！")
        response = await user_agent.chat("你好！@#$%^&*()_+ 🎉")
        assert isinstance(response, str)

    async def test_skip_command(self, user_agent, mock_client):
        """User sends '跳过' → treated as skip command if no active task."""
        mock_client.set_default_response("好的。")
        response = await user_agent.chat("跳过")
        assert isinstance(response, str)
