"""
端到端测试 - 语音识别 (6 个)

E2E-A01 ~ E2E-A06

注意：语音识别通常由专门的 ASR 服务处理，这里测试的是
LLM 处理语音转文字后的文本场景。
"""

import pytest
from unittest.mock import AsyncMock

from openakita.llm.types import (
    Message,
    TextBlock,
    EndpointConfig,
    LLMResponse,
    Usage,
    StopReason,
)
from openakita.llm.client import LLMClient


@pytest.fixture
def text_client():
    """创建文本处理客户端"""
    endpoints = [
        EndpointConfig(
            name="text-endpoint",
            provider="anthropic",
            api_type="anthropic",
            base_url="https://api.anthropic.com",
            api_key_env="TEST_KEY",
            model="claude-3-sonnet",
            priority=1,
            capabilities=["text", "tools"],
        ),
    ]
    return LLMClient(endpoints=endpoints)


def create_mock_response(text: str):
    """创建模拟响应"""
    return LLMResponse(
        id="msg_123",
        content=[TextBlock(text=text)],
        stop_reason=StopReason.END_TURN,
        usage=Usage(input_tokens=50, output_tokens=30),
        model="test-model",
    )


class TestTranscriptionProcessing:
    """语音转文字后处理测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_a01_simple_transcription(self, text_client):
        """E2E-A01: 简单语音文本"""
        mock_response = create_mock_response("你说了：你好，请问今天天气怎么样？")
        
        for provider in text_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        # 模拟 ASR 转写结果
        transcription = "你好请问今天天气怎么样"
        
        response = await text_client.chat(
            messages=[Message(role="user", content=f"用户语音输入：{transcription}")],
            system="你是一个语音助手，请理解用户的语音输入并回复",
        )
        
        assert response.text is not None
    
    @pytest.mark.asyncio
    async def test_e2e_a02_noisy_transcription(self, text_client):
        """E2E-A02: 噪音语音文本"""
        mock_response = create_mock_response("我理解你想查询北京的天气。")
        
        for provider in text_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        # 模拟带噪音的转写
        transcription = "呃...北京...嗯...天气"
        
        response = await text_client.chat(
            messages=[Message(role="user", content=f"[语音转写] {transcription}")],
            system="你是一个语音助手，请理解用户可能不太清晰的语音输入",
        )
        
        assert response.text is not None
    
    @pytest.mark.asyncio
    async def test_e2e_a03_long_transcription(self, text_client):
        """E2E-A03: 长语音文本"""
        mock_response = create_mock_response("已收到您的长消息，正在处理...")
        
        for provider in text_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        # 模拟长语音转写
        long_transcription = "今天我想和你讨论一下关于人工智能的发展，" * 10
        
        response = await text_client.chat(
            messages=[Message(role="user", content=long_transcription)],
        )
        
        assert response.text is not None


class TestMultilingual:
    """多语言语音测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_a04_chinese_transcription(self, text_client):
        """E2E-A04: 中文语音"""
        mock_response = create_mock_response("好的，我来帮您查询北京的天气。")
        
        for provider in text_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        response = await text_client.chat(
            messages=[Message(role="user", content="帮我查一下北京天气")],
        )
        
        assert response.text is not None
    
    @pytest.mark.asyncio
    async def test_e2e_a05_english_transcription(self, text_client):
        """E2E-A05: 英文语音"""
        mock_response = create_mock_response("I'll help you check the weather in London.")
        
        for provider in text_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        response = await text_client.chat(
            messages=[Message(role="user", content="What's the weather like in London?")],
        )
        
        assert response.text is not None


class TestContinuousConversation:
    """连续对话测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_a06_voice_conversation(self, text_client):
        """E2E-A06: 语音连续对话"""
        mock_response = create_mock_response("根据我们之前的对话，北京今天天气晴朗。")
        
        for provider in text_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        # 模拟多轮语音对话
        messages = [
            Message(role="user", content="我想查天气"),
            Message(role="assistant", content=[TextBlock(text="好的，请问您想查哪个城市？")]),
            Message(role="user", content="北京"),
            Message(role="assistant", content=[TextBlock(text="北京今天晴，25度。还有什么需要的吗？")]),
            Message(role="user", content="明天呢"),
        ]
        
        response = await text_client.chat(messages=messages)
        
        assert response.text is not None
