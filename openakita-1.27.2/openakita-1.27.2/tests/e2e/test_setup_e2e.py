"""
L4 E2E Tests: Full setup flow validation.

Tests the complete setup pipeline: directories + config + endpoints + identity,
then validates the result can be loaded by the config loader.
"""

import json
import os

import pytest
from pathlib import Path

from openakita.setup.wizard import SetupWizard
from openakita.llm.config import load_endpoints_config, validate_config


@pytest.fixture
def project_dir(tmp_path):
    return tmp_path / "myproject"


class TestFullSetupFlow:
    """Simulate the full init wizard output and verify everything integrates."""

    def test_directories_plus_config_roundtrip(self, project_dir):
        """Create dirs + write config → load config succeeds."""
        project_dir.mkdir()
        wizard = SetupWizard(project_dir=project_dir)

        wizard._create_directories()

        wizard.config = {
            "ANTHROPIC_API_KEY": "sk-test-full-flow",
            "ANTHROPIC_BASE_URL": "https://api.anthropic.com",
            "DEFAULT_MODEL": "claude-sonnet-4-20250514",
            "THINKING_MODE": "auto",
        }

        env_content = wizard._generate_env_content()
        wizard.env_path.write_text(env_content, encoding="utf-8")

        wizard._write_llm_endpoints()
        wizard._create_identity_examples()

        # Verify directory structure
        for d in ["data", "identity", "skills", "logs"]:
            assert (project_dir / d).is_dir()

        # Verify .env
        assert wizard.env_path.exists()
        env_text = wizard.env_path.read_text(encoding="utf-8")
        assert "sk-test-full-flow" in env_text

        # Verify endpoints config can be loaded
        ep_file = project_dir / "data" / "llm_endpoints.json"
        assert ep_file.exists()
        endpoints, compiler_eps, stt_eps, settings = load_endpoints_config(ep_file)
        assert len(endpoints) >= 1
        assert endpoints[0].model == "claude-sonnet-4-20250514"

        # Verify identity
        assert (project_dir / "identity" / "SOUL.md").exists()

    def test_config_validation_after_setup(self, project_dir):
        """Generated config passes validation."""
        project_dir.mkdir()
        wizard = SetupWizard(project_dir=project_dir)
        wizard._create_directories()
        wizard.config = {
            "ANTHROPIC_API_KEY": "sk-test-validate",
            "ANTHROPIC_BASE_URL": "https://api.anthropic.com",
            "DEFAULT_MODEL": "claude-sonnet-4-20250514",
        }
        wizard._write_llm_endpoints()

        ep_file = project_dir / "data" / "llm_endpoints.json"
        errors = validate_config(ep_file)

        # Only valid structural errors (api_key_env not set is expected in test)
        api_type_errors = [e for e in errors if "api_type" in e]
        base_url_errors = [e for e in errors if "base_url" in e]
        assert api_type_errors == []
        assert base_url_errors == []

    def test_setup_with_compiler_endpoints(self, project_dir):
        """Setup with compiler endpoints → both loaded correctly."""
        project_dir.mkdir()
        wizard = SetupWizard(project_dir=project_dir)
        wizard._create_directories()
        wizard.config = {
            "ANTHROPIC_BASE_URL": "https://api.anthropic.com",
            "DEFAULT_MODEL": "claude-sonnet-4-20250514",
            "_compiler_primary": {
                "provider": "openai-compatible",
                "api_type": "openai",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key_env": "DASHSCOPE_API_KEY",
                "model": "qwen-plus-latest",
            },
        }
        wizard._write_llm_endpoints()

        ep_file = project_dir / "data" / "llm_endpoints.json"
        endpoints, compiler_eps, _, settings = load_endpoints_config(ep_file)
        assert len(endpoints) >= 1
        assert len(compiler_eps) >= 1
        assert compiler_eps[0].model == "qwen-plus-latest"


class TestSetupAPIIntegration:
    """Test that setup config is usable by the /api/config endpoints."""

    def test_endpoints_readable_by_api(self, project_dir):
        """Config written by wizard matches the format expected by API routes."""
        project_dir.mkdir()
        (project_dir / "data").mkdir()
        wizard = SetupWizard(project_dir=project_dir)
        wizard.config = {
            "ANTHROPIC_BASE_URL": "https://api.anthropic.com",
            "DEFAULT_MODEL": "claude-sonnet-4-20250514",
        }
        wizard._write_llm_endpoints()

        ep_file = project_dir / "data" / "llm_endpoints.json"
        raw = json.loads(ep_file.read_text(encoding="utf-8"))

        # API routes expect these keys
        assert "endpoints" in raw
        assert "settings" in raw
        for ep in raw["endpoints"]:
            assert "name" in ep
            assert "provider" in ep
            assert "api_type" in ep
            assert "base_url" in ep
            assert "model" in ep
            assert "priority" in ep

    def test_env_file_parseable(self, project_dir):
        """Generated .env file is parseable by dotenv."""
        from dotenv import dotenv_values

        project_dir.mkdir()
        wizard = SetupWizard(project_dir=project_dir)
        wizard.config = {
            "ANTHROPIC_API_KEY": "sk-test-env",
            "DEFAULT_MODEL": "claude-sonnet-4-20250514",
            "THINKING_MODE": "auto",
        }
        env_content = wizard._generate_env_content()
        env_path = project_dir / ".env"
        env_path.write_text(env_content, encoding="utf-8")

        values = dotenv_values(env_path)
        assert values.get("ANTHROPIC_API_KEY") == "sk-test-env"
        assert values.get("DEFAULT_MODEL") == "claude-sonnet-4-20250514"
        assert values.get("AGENT_NAME") == "OpenAkita"


class TestCLISelfcheck:
    """Test selfcheck CLI command (non-LLM parts)."""

    def test_selfcheck_command_exists(self):
        """openakita selfcheck --help should work."""
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "openakita", "selfcheck", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout + result.stderr
        assert result.returncode == 0
        assert "selfcheck" in output.lower() or "self" in output.lower()

    def test_init_command_exists(self):
        """openakita init --help should work."""
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "openakita", "init", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout + result.stderr
        assert result.returncode == 0
