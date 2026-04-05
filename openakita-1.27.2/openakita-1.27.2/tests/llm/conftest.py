"""
pytest fixtures for LLM tests
"""

import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# 添加项目路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from openakita.llm.types import (
    LLMRequest,
    LLMResponse,
    EndpointConfig,
    Message,
    Tool,
    TextBlock,
    ToolUseBlock,
    ImageBlock,
    ImageContent,
    VideoBlock,
    VideoContent,
    AudioBlock,
    AudioContent,
    DocumentBlock,
    DocumentContent,
    Usage,
    StopReason,
)
from openakita.llm.client import LLMClient


@pytest.fixture
def sample_text_message():
    """简单文本消息"""
    return Message(role="user", content="Hello, how are you?")


@pytest.fixture
def sample_messages():
    """多轮对话消息"""
    return [
        Message(role="user", content="What is 2+2?"),
        Message(role="assistant", content=[TextBlock(text="2+2 equals 4.")]),
        Message(role="user", content="And what is 3+3?"),
    ]


@pytest.fixture
def sample_image_content():
    """示例图片内容"""
    # 1x1 红色 PNG 的 base64
    return ImageContent(
        media_type="image/png",
        data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )


@pytest.fixture
def sample_video_content():
    """示例视频内容"""
    return VideoContent(
        media_type="video/mp4",
        data="AAAAIGZ0eXBpc29t",  # minimal mp4 ftyp header base64
    )


@pytest.fixture
def sample_audio_content():
    """示例音频内容"""
    return AudioContent(
        media_type="audio/wav",
        data="UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=",  # minimal WAV
        format="wav",
    )


@pytest.fixture
def sample_document_content():
    """示例 PDF 文档内容"""
    return DocumentContent(
        media_type="application/pdf",
        data="JVBERi0xLjQKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwo+PgplbmRvYmoK",  # minimal PDF header
        filename="test.pdf",
    )


@pytest.fixture
def sample_tool():
    """示例工具定义"""
    return Tool(
        name="get_weather",
        description="Get the current weather for a location",
        input_schema={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and country"
                }
            },
            "required": ["location"]
        }
    )


@pytest.fixture
def sample_tool_use_block():
    """示例工具调用块"""
    return ToolUseBlock(
        id="call_123",
        name="get_weather",
        input={"location": "Beijing, China"}
    )


@pytest.fixture
def sample_endpoint_config():
    """示例端点配置"""
    return EndpointConfig(
        name="test-endpoint",
        provider="anthropic",
        api_type="anthropic",
        base_url="https://api.anthropic.com",
        api_key_env="TEST_API_KEY",
        model="claude-3-sonnet",
        priority=1,
        max_tokens=4096,
        timeout=60,
        capabilities=["text", "vision", "tools"],
    )


@pytest.fixture
def sample_openai_endpoint_config():
    """示例 OpenAI 端点配置"""
    return EndpointConfig(
        name="test-openai",
        provider="openai",
        api_type="openai",
        base_url="https://api.openai.com/v1",
        api_key_env="TEST_OPENAI_KEY",
        model="gpt-4o",
        priority=2,
        max_tokens=4096,
        timeout=60,
        capabilities=["text", "vision", "tools"],
    )


@pytest.fixture
def sample_llm_request(sample_messages, sample_tool):
    """示例 LLM 请求"""
    return LLMRequest(
        messages=sample_messages,
        system="You are a helpful assistant.",
        tools=[sample_tool],
        max_tokens=1000,
        temperature=0.7,
    )


@pytest.fixture
def sample_llm_response():
    """示例 LLM 响应"""
    return LLMResponse(
        id="msg_123",
        content=[TextBlock(text="Hello! I'm doing well, thank you for asking.")],
        stop_reason=StopReason.END_TURN,
        usage=Usage(input_tokens=10, output_tokens=15),
        model="claude-3-sonnet",
    )


@pytest.fixture
def mock_anthropic_response():
    """模拟 Anthropic API 响应"""
    return {
        "id": "msg_123",
        "type": "message",
        "role": "assistant",
        "content": [
            {"type": "text", "text": "Hello! How can I help you today?"}
        ],
        "model": "claude-3-sonnet-20240229",
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 10,
            "output_tokens": 15
        }
    }


@pytest.fixture
def mock_openai_response():
    """模拟 OpenAI API 响应"""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4o",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25
        }
    }


@pytest.fixture
def mock_openai_tool_response():
    """模拟 OpenAI 工具调用响应"""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "model": "gpt-4o",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"location": "Beijing, China"}'
                    }
                }]
            },
            "finish_reason": "tool_calls"
        }],
        "usage": {
            "prompt_tokens": 20,
            "completion_tokens": 10,
            "total_tokens": 30
        }
    }


@pytest.fixture
def test_config_path(tmp_path):
    """临时配置文件路径"""
    return tmp_path / "llm_endpoints.json"


@pytest.fixture
def test_config_content():
    """测试配置内容"""
    return {
        "endpoints": [
            {
                "name": "test-claude",
                "provider": "anthropic",
                "api_type": "anthropic",
                "base_url": "https://api.anthropic.com",
                "api_key_env": "TEST_ANTHROPIC_KEY",
                "model": "claude-3-sonnet",
                "priority": 1,
                "capabilities": ["text", "vision", "tools"]
            },
            {
                "name": "test-qwen",
                "provider": "dashscope",
                "api_type": "openai",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key_env": "TEST_DASHSCOPE_KEY",
                "model": "qwen-plus",
                "priority": 2,
                "capabilities": ["text", "tools", "thinking"]
            }
        ],
        "settings": {
            "retry_count": 2,
            "retry_delay_seconds": 1,
            "fallback_on_error": True
        }
    }


# 标记需要真实 API Key 的测试
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "api_keys: mark test as requiring real API keys"
    )


def pytest_addoption(parser):
    parser.addoption(
        "--api-keys",
        action="store_true",
        default=False,
        help="run tests that require real API keys"
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--api-keys"):
        skip_api = pytest.mark.skip(reason="need --api-keys option to run")
        for item in items:
            if "api_keys" in item.keywords:
                item.add_marker(skip_api)
