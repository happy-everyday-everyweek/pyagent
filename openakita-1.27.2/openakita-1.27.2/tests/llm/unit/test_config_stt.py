"""
单元测试 - 配置保存/加载 STT 端点 (3 个)

UT-G07 ~ UT-G09
"""

import json
import pytest

from openakita.llm.config import load_endpoints_config, save_endpoints_config
from openakita.llm.types import EndpointConfig


class TestSTTConfigSaving:
    """STT 端点配置保存测试"""

    def test_ut_g07_save_with_stt_endpoints(self, tmp_path):
        """UT-G07: 保存含 stt_endpoints 的配置 → 文件中包含 stt_endpoints 字段"""
        config_path = tmp_path / "config_with_stt.json"

        endpoints = [
            EndpointConfig(
                name="main-llm",
                provider="openai",
                api_type="openai",
                base_url="https://api.openai.com/v1",
                api_key_env="OPENAI_KEY",
                model="gpt-4o",
                capabilities=["text", "vision"],
            )
        ]

        stt_endpoints = [
            EndpointConfig(
                name="stt-whisper",
                provider="openai",
                api_type="openai",
                base_url="https://api.openai.com/v1",
                api_key_env="OPENAI_KEY",
                model="whisper-1",
                priority=1,
            ),
            EndpointConfig(
                name="stt-paraformer",
                provider="dashscope",
                api_type="openai",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                api_key_env="DASHSCOPE_KEY",
                model="paraformer-v2",
                priority=2,
            ),
        ]

        save_endpoints_config(
            endpoints,
            config_path=config_path,
            stt_endpoints=stt_endpoints,
        )

        # 直接读取 JSON 验证结构
        with open(config_path) as f:
            data = json.load(f)

        assert "stt_endpoints" in data
        assert len(data["stt_endpoints"]) == 2
        assert data["stt_endpoints"][0]["name"] == "stt-whisper"
        assert data["stt_endpoints"][1]["name"] == "stt-paraformer"


class TestSTTConfigLoading:
    """STT 端点配置加载测试"""

    def test_ut_g08_load_with_stt_endpoints(self, tmp_path):
        """UT-G08: 加载含 stt_endpoints 的配置 → 4 元组第 3 项非空"""
        config_path = tmp_path / "config_with_stt.json"

        config_data = {
            "endpoints": [
                {
                    "name": "main-llm",
                    "provider": "openai",
                    "api_type": "openai",
                    "base_url": "https://api.openai.com/v1",
                    "api_key_env": "OPENAI_KEY",
                    "model": "gpt-4o",
                    "capabilities": ["text"],
                }
            ],
            "stt_endpoints": [
                {
                    "name": "stt-whisper",
                    "provider": "openai",
                    "api_type": "openai",
                    "base_url": "https://api.openai.com/v1",
                    "api_key_env": "STT_KEY",
                    "model": "whisper-1",
                    "priority": 1,
                }
            ],
            "settings": {"retry_count": 3},
        }

        with open(config_path, "w") as f:
            json.dump(config_data, f)

        endpoints, compiler_eps, stt_eps, settings = load_endpoints_config(config_path)

        assert len(endpoints) == 1
        assert len(stt_eps) == 1
        assert stt_eps[0].name == "stt-whisper"
        assert stt_eps[0].model == "whisper-1"
        assert isinstance(stt_eps[0], EndpointConfig)
        assert settings["retry_count"] == 3

    def test_ut_g09_backward_compat_no_stt(self, tmp_path):
        """UT-G09: 兼容旧配置（无 stt_endpoints）→ 加载不报错，stt_endpoints 为空列表"""
        config_path = tmp_path / "old_config.json"

        # 旧配置没有 stt_endpoints 字段
        old_config = {
            "endpoints": [
                {
                    "name": "old-endpoint",
                    "provider": "anthropic",
                    "api_type": "anthropic",
                    "base_url": "https://api.anthropic.com",
                    "api_key_env": "ANTHROPIC_KEY",
                    "model": "claude-3-sonnet",
                    "capabilities": ["text", "vision"],
                }
            ],
            "settings": {"retry_count": 2},
        }

        with open(config_path, "w") as f:
            json.dump(old_config, f)

        endpoints, compiler_eps, stt_eps, settings = load_endpoints_config(config_path)

        assert len(endpoints) == 1
        # 关键断言：旧配置不报错，stt_endpoints 返回空列表
        assert stt_eps == []
        assert compiler_eps == []
        assert settings["retry_count"] == 2
