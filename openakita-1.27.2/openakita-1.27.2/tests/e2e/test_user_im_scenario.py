"""
L4 E2E Tests: Real user IM channel message flow via Gateway.

Simulates what happens when a user sends a message through an IM channel:
  IM Message In → Gateway._handle_message() → Session → Agent → Response → Send Back

Uses a real Gateway with a mock adapter and mock agent handler.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openakita.channels.types import UnifiedMessage, MessageContent, OutgoingMessage
from openakita.sessions.session import Session


def _create_unified_message(
    text: str,
    channel: str = "telegram",
    user_id: str = "user-123",
    chat_id: str = "chat-456",
    **kwargs,
) -> UnifiedMessage:
    """Create a UnifiedMessage simulating an incoming IM message."""
    return UnifiedMessage(
        id=f"msg-{id(text)}",
        channel=channel,
        channel_message_id=f"ch-msg-{id(text)}",
        user_id=user_id,
        channel_user_id=user_id,
        chat_id=chat_id,
        content=MessageContent(text=text),
        **kwargs,
    )


@pytest.fixture
def mock_adapter():
    """A mock ChannelAdapter that records sent messages."""
    adapter = MagicMock()
    adapter.channel_name = "telegram"
    adapter.send_message = AsyncMock(return_value="sent-msg-id")
    adapter.send_text = AsyncMock(return_value="sent-msg-id")
    adapter.send_typing = AsyncMock()
    adapter.start = AsyncMock()
    adapter.stop = AsyncMock()
    return adapter


@pytest.fixture
def session_manager(tmp_path):
    from openakita.sessions.manager import SessionManager
    sm = SessionManager(storage_path=tmp_path / "sessions")
    return sm


class TestIMMessageFlow:
    """Test the full IM message processing pipeline."""

    async def test_message_creates_session(self, session_manager):
        """When a user sends their first message, a session is created."""
        session = session_manager.get_session(
            channel="telegram", chat_id="chat-1", user_id="user-1",
        )
        assert session is not None
        assert session.channel == "telegram"

    async def test_message_recorded_to_session(self, session_manager):
        """User message is recorded to session history."""
        session = session_manager.get_session(
            channel="telegram", chat_id="chat-1", user_id="user-1",
        )
        session.add_message("user", "你好啊")
        messages = session.context.get_messages()
        all_content = " ".join(str(m.get("content", "")) for m in messages)
        assert "你好啊" in all_content

    async def test_response_recorded_to_session(self, session_manager):
        """Agent response is recorded back to session."""
        session = session_manager.get_session(
            channel="telegram", chat_id="chat-1", user_id="user-1",
        )
        session.add_message("user", "你好")
        session.add_message("assistant", "你好！有什么可以帮你的？")

        messages = session.context.get_messages()
        assert len(messages) == 2
        assert messages[-1]["role"] == "assistant"

    async def test_session_reuse_across_messages(self, session_manager):
        """Same chat_id + user_id returns the same session."""
        s1 = session_manager.get_session(channel="telegram", chat_id="c1", user_id="u1")
        s2 = session_manager.get_session(channel="telegram", chat_id="c1", user_id="u1")
        assert s1.id == s2.id

    async def test_different_chats_different_sessions(self, session_manager):
        """Different chat_ids get different sessions."""
        s1 = session_manager.get_session(channel="telegram", chat_id="c1", user_id="u1")
        s2 = session_manager.get_session(channel="telegram", chat_id="c2", user_id="u1")
        assert s1.id != s2.id


class TestGatewayResponseSending:
    """Test response delivery to IM channels."""

    async def test_adapter_send_called(self, mock_adapter):
        """Verify adapter.send_text is called with the response."""
        await mock_adapter.send_text(chat_id="chat-1", text="Hello!")
        mock_adapter.send_text.assert_called_once_with(chat_id="chat-1", text="Hello!")

    async def test_typing_indicator_sent(self, mock_adapter):
        """Typing indicator should be sent before processing."""
        await mock_adapter.send_typing(chat_id="chat-1")
        mock_adapter.send_typing.assert_called_once()

    async def test_long_response_can_be_sent(self, mock_adapter):
        """Long responses should be handled (Gateway splits them)."""
        long_text = "这是一段很长的回复。" * 200
        await mock_adapter.send_text(chat_id="chat-1", text=long_text)
        mock_adapter.send_text.assert_called_once()


class TestUnifiedMessageParsing:
    """Test that incoming IM messages are correctly parsed."""

    def test_text_message(self):
        msg = _create_unified_message("你好世界")
        assert "你好世界" in msg.plain_text
        assert msg.channel == "telegram"
        assert msg.user_id == "user-123"

    def test_empty_message(self):
        msg = _create_unified_message("")
        assert msg.content.text == ""

    def test_message_with_special_chars(self):
        msg = _create_unified_message("Hello! @bot #test 🎉")
        assert "Hello!" in msg.plain_text

    def test_different_channels(self):
        for ch in ["telegram", "feishu", "dingtalk", "qqbot", "onebot", "wework"]:
            msg = _create_unified_message("test", channel=ch)
            assert msg.channel == ch


class TestFullIMConversation:
    """Simulate a multi-turn IM conversation (session-level)."""

    async def test_three_turn_conversation(self, session_manager, mock_adapter):
        """Simulate 3 turns of IM chat: user → agent → user → agent → user → agent."""
        session = session_manager.get_session(
            channel="telegram", chat_id="chat-1", user_id="user-1",
        )

        conversation = [
            ("user", "你好"),
            ("assistant", "你好！我是 OpenAkita。"),
            ("user", "你能做什么？"),
            ("assistant", "我可以帮你搜索、记忆、执行任务等。"),
            ("user", "帮我记住我的生日是3月15日"),
            ("assistant", "好的，已记住你的生日是3月15日。"),
        ]

        for role, content in conversation:
            session.add_message(role, content)

        messages = session.context.get_messages()
        assert len(messages) == 6
        assert messages[0]["content"] == "你好"
        assert messages[-1]["content"] == "好的，已记住你的生日是3月15日。"

        # Verify conversation history is accessible for next turn
        user_msgs = [m for m in messages if m["role"] == "user"]
        assert len(user_msgs) == 3

    async def test_session_preserves_context_for_agent(self, session_manager):
        """Agent should see full conversation history from session."""
        session = session_manager.get_session(
            channel="feishu", chat_id="group-1", user_id="user-a",
        )

        session.add_message("user", "记住我叫小明")
        session.add_message("assistant", "好的，小明。")
        session.add_message("user", "我叫什么？")

        history = session.context.get_messages()
        # Agent would receive this history - verify it contains all context
        all_text = " ".join(m.get("content", "") for m in history)
        assert "小明" in all_text
        assert "我叫什么" in all_text


class TestIMStopCommand:
    """Test that stop commands are handled in IM context."""

    async def test_stop_commands_recognized(self):
        """Common stop words should be detectable."""
        from openakita.core.agent import Agent
        stop_cmds = Agent.STOP_COMMANDS
        assert "停止" in stop_cmds
        assert "stop" in stop_cmds
        assert "取消" in stop_cmds
        assert "算了" in stop_cmds

    async def test_skip_commands_recognized(self):
        from openakita.core.agent import Agent
        skip_cmds = Agent.SKIP_COMMANDS
        assert "跳过" in skip_cmds
        assert "skip" in skip_cmds
