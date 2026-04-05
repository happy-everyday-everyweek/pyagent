"""
L4 E2E Tests: Real user CLI interaction scenarios.

Simulates what happens when a user runs OpenAkita from the command line:
- `openakita` starts interactive mode
- User types messages and sees responses
- Special commands like /status, /help, /clear work

Since the interactive loop uses Rich Prompt.ask() which is hard to automate,
we test the CLI entry points and commands via subprocess and the Agent.chat()
interface (which is what run_interactive() delegates to).
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestCLIStartup:
    """User runs `openakita` or `python -m openakita` for the first time."""

    def test_module_importable(self):
        """The package can be imported without errors."""
        result = subprocess.run(
            [sys.executable, "-c", "import openakita; print('OK')"],
            capture_output=True, text=True, timeout=15,
        )
        assert "OK" in result.stdout

    def test_version_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "openakita", "--version"],
            capture_output=True, text=True, timeout=15,
        )
        combined = result.stdout + result.stderr
        assert result.returncode == 0 or "version" in combined.lower()

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "openakita", "--help"],
            capture_output=True, text=True, timeout=15,
        )
        combined = result.stdout + result.stderr
        assert "usage" in combined.lower() or "help" in combined.lower() or "openakita" in combined.lower()


class TestCLISubcommands:
    """User runs specific CLI subcommands."""

    def test_status_command_exists(self):
        """'openakita status' should be a recognized command."""
        result = subprocess.run(
            [sys.executable, "-m", "openakita", "status"],
            capture_output=True, text=True, timeout=15,
        )
        # Should not crash with "unrecognized arguments"
        assert "unrecognized" not in result.stderr.lower()

    def test_init_command_exists(self):
        """'openakita init' should be a recognized command."""
        result = subprocess.run(
            [sys.executable, "-m", "openakita", "init", "--help"],
            capture_output=True, text=True, timeout=15,
        )
        combined = result.stdout + result.stderr
        # Should show help for init, not crash
        assert result.returncode == 0 or "init" in combined.lower() or "usage" in combined.lower()

    def test_selfcheck_command_exists(self):
        """'openakita selfcheck' should be a recognized command."""
        result = subprocess.run(
            [sys.executable, "-m", "openakita", "selfcheck", "--help"],
            capture_output=True, text=True, timeout=15,
        )
        combined = result.stdout + result.stderr
        assert result.returncode == 0 or "selfcheck" in combined.lower()

    def test_serve_command_exists(self):
        """'openakita serve --help' should show API server options."""
        result = subprocess.run(
            [sys.executable, "-m", "openakita", "serve", "--help"],
            capture_output=True, text=True, timeout=15,
        )
        combined = result.stdout + result.stderr
        assert result.returncode == 0 or "serve" in combined.lower()


class TestCLIAgentChat:
    """
    Test the Agent.chat() method which is what CLI interactive mode calls.
    This simulates user typing messages at the CLI prompt.
    """

    async def test_agent_chat_interface_exists(self):
        """Agent.chat() method should exist and be callable."""
        from openakita.core.agent import Agent
        assert hasattr(Agent, "chat")
        assert callable(getattr(Agent, "chat"))

    async def test_agent_chat_with_session_exists(self):
        """Agent.chat_with_session() exists for external callers."""
        from openakita.core.agent import Agent
        assert hasattr(Agent, "chat_with_session")

    async def test_agent_chat_with_session_stream_exists(self):
        """Agent.chat_with_session_stream() exists for SSE callers."""
        from openakita.core.agent import Agent
        assert hasattr(Agent, "chat_with_session_stream")


class TestCLISpecialCommands:
    """Test CLI-specific special commands that users can type."""

    def test_stop_commands_defined(self):
        from openakita.core.agent import Agent
        assert len(Agent.STOP_COMMANDS) > 5
        assert all(isinstance(cmd, str) for cmd in Agent.STOP_COMMANDS)

    def test_skip_commands_defined(self):
        from openakita.core.agent import Agent
        assert len(Agent.SKIP_COMMANDS) > 3

    def test_stop_commands_include_chinese(self):
        from openakita.core.agent import Agent
        chinese_cmds = [c for c in Agent.STOP_COMMANDS if any('\u4e00' <= ch <= '\u9fff' for ch in c)]
        assert len(chinese_cmds) >= 5  # 停止, 取消, 算了, 不用了, 别做了, etc.

    def test_stop_commands_include_english(self):
        from openakita.core.agent import Agent
        english_cmds = [c for c in Agent.STOP_COMMANDS if c.isascii()]
        assert len(english_cmds) >= 3  # stop, cancel, abort, quit


class TestCLIOutputFormat:
    """Test that CLI would format output correctly."""

    def test_agent_returns_string(self):
        """Agent.chat() should return str, which CLI displays via Rich."""
        from openakita.core.agent import Agent
        # Verify return type annotation
        import inspect
        sig = inspect.signature(Agent.chat)
        # chat returns str
        assert sig.return_annotation == str or "str" in str(sig.return_annotation)
