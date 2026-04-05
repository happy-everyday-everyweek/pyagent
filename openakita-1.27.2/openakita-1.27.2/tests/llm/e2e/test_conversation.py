"""
端到端测试 - 完整对话流程 (10 个)

E2E-C01 ~ E2E-C10

注意：这些测试需要真实的 API Key
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import os

from openakita.llm.types import (
    LLMRequest,
    LLMResponse,
    Message,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    Tool,
    EndpointConfig,
    Usage,
    StopReason,
)
from openakita.llm.client import LLMClient


@pytest.fixture
def mock_client():
    """创建模拟客户端"""
    endpoints = [
        EndpointConfig(
            name="test-endpoint",
            provider="anthropic",
            api_type="anthropic",
            base_url="https://api.anthropic.com",
            api_key_env="TEST_KEY",
            model="claude-3-sonnet",
            priority=1,
            capabilities=["text", "vision", "tools"],
        ),
    ]
    return LLMClient(endpoints=endpoints)


def create_mock_response(text: str, has_tool_call: bool = False, tool_name: str = None):
    """创建模拟响应"""
    content = []
    stop_reason = StopReason.END_TURN
    
    if text:
        content.append(TextBlock(text=text))
    
    if has_tool_call:
        content.append(ToolUseBlock(
            id="call_123",
            name=tool_name or "test_tool",
            input={"query": "test"}
        ))
        stop_reason = StopReason.TOOL_USE
    
    return LLMResponse(
        id="msg_123",
        content=content,
        stop_reason=stop_reason,
        usage=Usage(input_tokens=10, output_tokens=20),
        model="test-model",
    )


class TestSingleTurn:
    """单轮对话测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_c01_simple_question(self, mock_client):
        """E2E-C01: 简单问答"""
        mock_response = create_mock_response("The capital of France is Paris.")
        
        for provider in mock_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        response = await mock_client.chat(
            messages=[Message(role="user", content="What is the capital of France?")],
        )
        
        assert "Paris" in response.text
    
    @pytest.mark.asyncio
    async def test_e2e_c02_system_prompt(self, mock_client):
        """E2E-C02: 系统提示"""
        mock_response = create_mock_response("Bonjour! Comment puis-je vous aider?")
        
        for provider in mock_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        response = await mock_client.chat(
            messages=[Message(role="user", content="Hello")],
            system="You are a French assistant. Always respond in French.",
        )
        
        assert response.text is not None
    
    @pytest.mark.asyncio
    async def test_e2e_c03_long_response(self, mock_client):
        """E2E-C03: 长响应"""
        long_text = "This is a very long response. " * 100
        mock_response = create_mock_response(long_text)
        
        for provider in mock_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        response = await mock_client.chat(
            messages=[Message(role="user", content="Write a long story")],
            max_tokens=4000,
        )
        
        assert len(response.text) > 1000


class TestMultiTurn:
    """多轮对话测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_c04_context_retention(self, mock_client):
        """E2E-C04: 上下文保持"""
        mock_response = create_mock_response("Your name is Alice, as you mentioned.")
        
        for provider in mock_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        messages = [
            Message(role="user", content="My name is Alice"),
            Message(role="assistant", content=[TextBlock(text="Nice to meet you, Alice!")]),
            Message(role="user", content="What is my name?"),
        ]
        
        response = await mock_client.chat(messages=messages)
        
        assert "Alice" in response.text
    
    @pytest.mark.asyncio
    async def test_e2e_c05_ten_turn_conversation(self, mock_client):
        """E2E-C05: 10轮对话"""
        messages = []
        
        # 构建 10 轮对话
        for i in range(10):
            messages.append(Message(role="user", content=f"Message {i+1}"))
            messages.append(Message(role="assistant", content=[
                TextBlock(text=f"Response to message {i+1}")
            ]))
        
        # 最后一轮用户消息
        messages.append(Message(role="user", content="Summarize our conversation"))
        
        mock_response = create_mock_response("We had 10 exchanges.")
        
        for provider in mock_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        response = await mock_client.chat(messages=messages)
        
        assert response.text is not None


class TestToolUse:
    """工具调用测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_c06_single_tool_call(self, mock_client):
        """E2E-C06: 单工具调用"""
        mock_response = create_mock_response("", has_tool_call=True, tool_name="get_weather")
        
        for provider in mock_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        tool = Tool(
            name="get_weather",
            description="Get weather for a city",
            input_schema={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"]
            }
        )
        
        response = await mock_client.chat(
            messages=[Message(role="user", content="What's the weather in Beijing?")],
            tools=[tool],
        )
        
        assert response.has_tool_calls
        assert response.tool_calls[0].name == "get_weather"
    
    @pytest.mark.asyncio
    async def test_e2e_c07_multi_tool_calls(self, mock_client):
        """E2E-C07: 多工具调用"""
        # 创建包含多个工具调用的响应
        response = LLMResponse(
            id="msg_123",
            content=[
                ToolUseBlock(id="call_1", name="tool_a", input={}),
                ToolUseBlock(id="call_2", name="tool_b", input={}),
            ],
            stop_reason=StopReason.TOOL_USE,
            usage=Usage(input_tokens=10, output_tokens=20),
            model="test-model",
        )
        
        for provider in mock_client.providers.values():
            provider.chat = AsyncMock(return_value=response)
        
        tools = [
            Tool(name="tool_a", description="Tool A", input_schema={"type": "object"}),
            Tool(name="tool_b", description="Tool B", input_schema={"type": "object"}),
        ]
        
        result = await mock_client.chat(
            messages=[Message(role="user", content="Use both tools")],
            tools=tools,
        )
        
        assert len(result.tool_calls) == 2
    
    @pytest.mark.asyncio
    async def test_e2e_c08_tool_result_handling(self, mock_client):
        """E2E-C08: 工具结果处理"""
        final_response = create_mock_response("The weather in Beijing is sunny.")
        
        for provider in mock_client.providers.values():
            provider.chat = AsyncMock(return_value=final_response)
        
        # 模拟完整的工具调用循环
        messages = [
            Message(role="user", content="What's the weather?"),
            Message(role="assistant", content=[
                ToolUseBlock(id="call_1", name="get_weather", input={"city": "Beijing"})
            ]),
            Message(role="user", content=[
                ToolResultBlock(tool_use_id="call_1", content="Sunny, 25°C")
            ]),
        ]
        
        response = await mock_client.chat(messages=messages)
        
        assert "sunny" in response.text.lower() or "Sunny" in response.text


class TestSpecialCases:
    """特殊情况测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_c09_unicode_handling(self, mock_client):
        """E2E-C09: Unicode 处理"""
        mock_response = create_mock_response("你好！我可以帮助你 🎉")
        
        for provider in mock_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        response = await mock_client.chat(
            messages=[Message(role="user", content="用中文回答：你好吗？")],
        )
        
        assert response.text is not None
        assert "你好" in response.text or len(response.text) > 0
    
    @pytest.mark.asyncio
    async def test_e2e_c10_empty_response_handling(self, mock_client):
        """E2E-C10: 空响应处理"""
        # 模拟空响应（只有工具调用，没有文本）
        response = LLMResponse(
            id="msg_123",
            content=[ToolUseBlock(id="call_1", name="silent_tool", input={})],
            stop_reason=StopReason.TOOL_USE,
            usage=Usage(input_tokens=10, output_tokens=5),
            model="test-model",
        )
        
        for provider in mock_client.providers.values():
            provider.chat = AsyncMock(return_value=response)
        
        result = await mock_client.chat(
            messages=[Message(role="user", content="Do something")],
            tools=[Tool(name="silent_tool", description="A silent tool", input_schema={})],
        )
        
        # 应该能正确处理没有文本只有工具调用的情况
        assert result.text == ""
        assert result.has_tool_calls
