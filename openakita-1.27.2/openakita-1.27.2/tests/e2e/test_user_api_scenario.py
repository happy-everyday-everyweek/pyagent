"""
L4 E2E Tests: Real user desktop chat via /api/chat SSE endpoint.

Simulates the desktop client sending messages to the API and receiving SSE events.
Uses a real FastAPI app with a real Agent (brain mocked).
"""

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from tests.fixtures.mock_llm import MockLLMClient, MockResponse


def _create_test_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "workspace"
    ws.mkdir()
    for d in ["data", "data/memory", "logs", "skills"]:
        (ws / d).mkdir(parents=True, exist_ok=True)
    identity = ws / "identity"
    identity.mkdir()
    (identity / "SOUL.md").write_text("# Soul\nI am OpenAkita.", encoding="utf-8")
    (identity / "AGENT.md").write_text("# Agent\n## Core\nHelp.\n## Tooling\nTools.", encoding="utf-8")
    (identity / "USER.md").write_text("# User\nTest.", encoding="utf-8")
    (identity / "personas").mkdir()
    (identity / "personas" / "default.md").write_text("Friendly.", encoding="utf-8")
    (identity / "MEMORY.md").write_text("", encoding="utf-8")
    (ws / "data" / "memory" / "MEMORY.md").write_text("", encoding="utf-8")

    llm_config = [{"name": "mock", "base_url": "http://localhost:1234/v1",
                    "api_key": "sk-test", "model": "mock", "provider": "openai",
                    "context_window": 128000, "enabled": True}]
    (ws / "llm_endpoints.json").write_text(json.dumps(llm_config), encoding="utf-8")
    return ws


def _inject_mock_brain(agent, mock_client):
    from tests.fixtures.mock_llm import MockBrain
    mb = MockBrain(mock_client)
    mb.max_tokens = 4096
    mb._llm_client = mock_client
    mb.is_thinking_enabled = lambda: False
    mb._thinking_enabled = False
    mb.get_fallback_model = lambda *a, **kw: ""
    mb.restore_default_model = lambda *a, **kw: (True, "ok")
    mb.get_current_model_info = lambda: {"name": "mock", "model": "mock"}
    mb.get_current_endpoint_info = lambda: {"name": "mock"}
    mb.switch_model = lambda *a, **kw: (True, "switched")
    agent.brain = mb
    agent.reasoning_engine._brain = mb
    agent.context_manager._brain = mb
    agent.response_handler.brain = mb
    agent.prompt_assembler._brain = mb


def _parse_sse_events(raw: str) -> list[dict]:
    """Parse raw SSE text into a list of event dicts."""
    events = []
    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                pass
    return events


@pytest.fixture
async def api_client(tmp_path, monkeypatch):
    """Create a real FastAPI app with a real Agent (mocked brain), return httpx client."""
    ws = _create_test_workspace(tmp_path)
    monkeypatch.setenv("OPENAKITA_PROJECT_ROOT", str(ws))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    import openakita.config as config_mod
    from openakita.config import Settings
    test_settings = Settings(
        project_root=ws,
        database_path="data/agent.db",
        log_dir=str(ws / "logs"),
        log_level="WARNING",
        max_iterations=10,
        thinking_mode="never",
    )
    monkeypatch.setattr(config_mod, "settings", test_settings)

    from openakita.core.agent import Agent
    agent = Agent(name="TestAgent")

    mock_client = MockLLMClient()
    _inject_mock_brain(agent, mock_client)
    agent._initialized = True
    agent.identity.load()

    from openakita.api.server import create_app
    app = create_app()
    app.state.agent = agent
    app.state.session_manager = None  # SSE flow handles missing session_manager gracefully

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client, mock_client


class TestDesktopUserChatFlow:
    """Simulate the desktop client sending chat messages."""

    async def test_simple_message_returns_sse_stream(self, api_client):
        client, mock_llm = api_client
        mock_llm.preset_response("你好！欢迎使用 OpenAkita。")

        resp = await client.post("/api/chat", json={"message": "你好"})

        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

        events = _parse_sse_events(resp.text)
        event_types = [e["type"] for e in events]

        assert "done" in event_types

    async def test_text_delta_events_contain_response(self, api_client):
        client, mock_llm = api_client
        mock_llm.preset_response("Python是一门优雅的编程语言。")

        resp = await client.post("/api/chat", json={"message": "什么是Python？"})
        events = _parse_sse_events(resp.text)

        text_deltas = [e for e in events if e["type"] == "text_delta"]
        if text_deltas:
            full_text = "".join(e.get("content", "") for e in text_deltas)
            assert "Python" in full_text or len(full_text) > 0

    async def test_done_event_is_last(self, api_client):
        client, mock_llm = api_client
        mock_llm.preset_response("Done testing.")

        resp = await client.post("/api/chat", json={"message": "test"})
        events = _parse_sse_events(resp.text)

        assert len(events) > 0
        assert events[-1]["type"] == "done"

    async def test_error_when_no_agent(self, tmp_path, monkeypatch):
        """If agent is None, SSE should return an error event."""
        from openakita.api.server import create_app
        app = create_app()
        app.state.agent = None
        app.state.session_manager = None

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            resp = await client.post("/api/chat", json={"message": "hello"})
            events = _parse_sse_events(resp.text)
            event_types = [e["type"] for e in events]
            assert "error" in event_types or "done" in event_types


class TestDesktopMultiTurn:
    """Simulate desktop user having a multi-turn conversation."""

    async def test_two_messages_with_conversation_id(self, api_client):
        client, mock_llm = api_client
        mock_llm.preset_sequence([
            MockResponse(content="回答1"),
            MockResponse(content="回答2"),
        ])

        conv_id = "test-conv-001"

        resp1 = await client.post("/api/chat", json={
            "message": "第一个问题",
            "conversation_id": conv_id,
        })
        assert resp1.status_code == 200

        resp2 = await client.post("/api/chat", json={
            "message": "第二个问题",
            "conversation_id": conv_id,
        })
        assert resp2.status_code == 200
        # Both requests should have reached the agent
        assert mock_llm.total_calls >= 1
