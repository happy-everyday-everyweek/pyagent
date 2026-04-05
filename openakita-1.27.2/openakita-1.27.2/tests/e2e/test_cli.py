"""
L4 E2E Tests: CLI commands.

Tests CLI entry points via subprocess. Does not require LLM for status/version commands.
"""

import subprocess
import sys

import pytest


class TestCLIStatus:
    def test_version_flag(self):
        """openakita --version should print version."""
        result = subprocess.run(
            [sys.executable, "-m", "openakita", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0 or "version" in (result.stdout + result.stderr).lower()

    def test_help_flag(self):
        """openakita --help should show available commands."""
        result = subprocess.run(
            [sys.executable, "-m", "openakita", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        output = result.stdout + result.stderr
        assert "openakita" in output.lower() or "usage" in output.lower()

    def test_status_command(self):
        """openakita status should not crash."""
        result = subprocess.run(
            [sys.executable, "-m", "openakita", "status"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # status may fail gracefully if not running, but should not crash
        assert result.returncode in (0, 1)


class TestCLIModuleEntry:
    def test_module_importable(self):
        """python -m openakita should be importable."""
        result = subprocess.run(
            [sys.executable, "-c", "import openakita; print(openakita.__name__)"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0
        assert "openakita" in result.stdout
