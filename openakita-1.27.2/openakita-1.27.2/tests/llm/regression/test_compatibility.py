"""
回归测试 - 接口兼容性 (8 个)

REG-01 ~ REG-08

确保新的 LLM 层与现有代码兼容。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from openakita.llm.types import (
    Message,
    TextBlock,
    ToolUseBlock,
    EndpointConfig,
    LLMResponse,
    Usage,
    StopReason,
    Tool,
)
from openakita.llm.client import LLMClient


@pytest.fixture
def test_client():
    """创建测试客户端"""
    endpoints = [
        EndpointConfig(
            name="test",
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


def create_mock_response(text: str, has_tool: bool = False):
    """创建模拟响应"""
    content = [TextBlock(text=text)]
    if has_tool:
        content.append(ToolUseBlock(id="call_1", name="test_tool", input={}))
    
    return LLMResponse(
        id="msg_123",
        content=content,
        stop_reason=StopReason.TOOL_USE if has_tool else StopReason.END_TURN,
        usage=Usage(input_tokens=10, output_tokens=20),
        model="test-model",
    )


class TestBrainCompatibility:
    """Brain 类兼容性测试"""
    
    @pytest.mark.asyncio
    async def test_reg_01_response_format(self, test_client):
        """REG-01: Brain 响应格式兼容"""
        mock_response = create_mock_response("Test response")
        
        for provider in test_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        response = await test_client.chat(
            messages=[Message(role="user", content="Hello")],
        )
        
        # 验证响应格式
        assert hasattr(response, 'text')
        assert hasattr(response, 'tool_calls')
        assert hasattr(response, 'stop_reason')
        assert hasattr(response, 'usage')
        assert hasattr(response, 'model')
        
        # 验证 text 属性
        assert response.text == "Test response"
        
        # 验证 tool_calls 属性
        assert isinstance(response.tool_calls, list)
    
    @pytest.mark.asyncio
    async def test_reg_02_tool_call_format(self, test_client):
        """REG-02: Brain 工具调用格式兼容"""
        mock_response = create_mock_response("Using tool", has_tool=True)
        
        for provider in test_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        tool = Tool(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}}
        )
        
        response = await test_client.chat(
            messages=[Message(role="user", content="Use tool")],
            tools=[tool],
        )
        
        # 验证工具调用格式
        assert response.has_tool_calls
        tool_call = response.tool_calls[0]
        
        assert hasattr(tool_call, 'id')
        assert hasattr(tool_call, 'name')
        assert hasattr(tool_call, 'input')
        
        assert isinstance(tool_call.input, dict)


class TestMediaHandlerCompatibility:
    """MediaHandler 兼容性测试"""
    
    @pytest.mark.asyncio
    async def test_reg_03_image_handling(self, test_client):
        """REG-03: MediaHandler 图片处理兼容"""
        from openakita.llm.types import ImageBlock, ImageContent
        
        mock_response = create_mock_response("Image described")
        
        for provider in test_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        # MediaHandler 发送图片消息的方式
        image = ImageContent(media_type="image/png", data="base64data")
        
        response = await test_client.chat(
            messages=[Message(role="user", content=[
                ImageBlock(image=image),
                TextBlock(text="Describe"),
            ])],
        )
        
        assert response.text is not None
    
    @pytest.mark.asyncio
    async def test_reg_04_multimodal_message(self, test_client):
        """REG-04: MediaHandler 多模态消息兼容"""
        from openakita.llm.types import ImageBlock, ImageContent
        
        mock_response = create_mock_response("Processed")
        
        for provider in test_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        # 复杂多模态消息
        messages = [
            Message(role="user", content=[
                ImageBlock(image=ImageContent(media_type="image/png", data="img1")),
                TextBlock(text="First image"),
            ]),
            Message(role="assistant", content=[
                TextBlock(text="I see the first image"),
            ]),
            Message(role="user", content=[
                ImageBlock(image=ImageContent(media_type="image/png", data="img2")),
                TextBlock(text="Now compare with this"),
            ]),
        ]
        
        response = await test_client.chat(messages=messages)
        
        assert response.text is not None


class TestMemoryCompatibility:
    """Memory 兼容性测试"""
    
    @pytest.mark.asyncio
    async def test_reg_05_context_messages(self, test_client):
        """REG-05: Memory 上下文消息兼容"""
        mock_response = create_mock_response("I remember our conversation")
        
        for provider in test_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        # Memory 模块构建的长对话上下文
        messages = []
        for i in range(20):
            messages.append(Message(role="user", content=f"Message {i}"))
            messages.append(Message(role="assistant", content=[
                TextBlock(text=f"Response {i}")
            ]))
        messages.append(Message(role="user", content="Summarize our chat"))
        
        response = await test_client.chat(messages=messages)
        
        assert response.text is not None
    
    @pytest.mark.asyncio
    async def test_reg_06_system_prompt_injection(self, test_client):
        """REG-06: Memory 系统提示注入兼容"""
        mock_response = create_mock_response("Following system instructions")
        
        for provider in test_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        # Memory 模块可能注入的系统提示
        system_prompt = (
            "You are a helpful assistant.\n"
            "Previous context summary: User discussed weather yesterday.\n"
            "User preferences: Concise responses."
        )
        
        response = await test_client.chat(
            messages=[Message(role="user", content="Hello")],
            system=system_prompt,
        )
        
        assert response.text is not None


class TestEvolutionSkillCompatibility:
    """Evolution 和 Skill 兼容性测试"""
    
    @pytest.mark.asyncio
    async def test_reg_07_skill_tool_definition(self, test_client):
        """REG-07: Skill 工具定义兼容"""
        mock_response = create_mock_response("Using skill tool", has_tool=True)
        
        for provider in test_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        # Skill 模块定义的工具
        skill_tools = [
            Tool(
                name="search_web",
                description="Search the web for information",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "num_results": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="run_code",
                description="Execute Python code",
                input_schema={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "timeout": {"type": "integer", "default": 30}
                    },
                    "required": ["code"]
                }
            ),
        ]
        
        response = await test_client.chat(
            messages=[Message(role="user", content="Search for AI news")],
            tools=skill_tools,
        )
        
        assert response.has_tool_calls or response.text is not None
    
    @pytest.mark.asyncio
    async def test_reg_08_evolution_analysis(self, test_client):
        """REG-08: Evolution 分析兼容"""
        mock_response = create_mock_response(
            "Analysis complete:\n"
            "- Pattern 1: User prefers morning updates\n"
            "- Pattern 2: Frequent weather queries"
        )
        
        for provider in test_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        # Evolution 模块发送的分析请求
        analysis_prompt = (
            "Analyze the following conversation patterns:\n"
            "1. User messages: [list of recent messages]\n"
            "2. Tool usage: [tool usage stats]\n"
            "Identify patterns and suggest improvements."
        )
        
        response = await test_client.chat(
            messages=[Message(role="user", content=analysis_prompt)],
            system="You are an AI behavior analyst.",
            max_tokens=2000,
        )
        
        assert response.text is not None
        assert len(response.text) > 0
