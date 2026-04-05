"""
集成测试 - Provider 调用 (12 个)

IT-P01 ~ IT-P12

注意：需要 --api-keys 参数运行这些测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from openakita.llm.types import (
    LLMRequest,
    LLMResponse,
    Message,
    TextBlock,
    EndpointConfig,
)
from openakita.llm.providers.anthropic import AnthropicProvider
from openakita.llm.providers.openai import OpenAIProvider


class TestAnthropicProvider:
    """Anthropic Provider 测试"""
    
    @pytest.fixture
    def anthropic_provider(self, sample_endpoint_config):
        """创建 Anthropic Provider"""
        return AnthropicProvider(sample_endpoint_config)
    
    @pytest.mark.asyncio
    async def test_it_p01_text_chat(self, anthropic_provider, mock_anthropic_response):
        """IT-P01: Anthropic: 文本对话"""
        with patch.object(anthropic_provider, '_get_client') as mock_client:
            # 模拟响应
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_anthropic_response
            
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_response
            mock_client.return_value = mock_http
            
            request = LLMRequest(
                messages=[Message(role="user", content="Hello")],
                max_tokens=100,
            )
            
            response = await anthropic_provider.chat(request)
            
            assert isinstance(response, LLMResponse)
            assert response.text == "Hello! How can I help you today?"
    
    @pytest.mark.asyncio
    async def test_it_p02_tool_call(self, anthropic_provider):
        """IT-P02: Anthropic: 工具调用"""
        mock_response = {
            "id": "msg_123",
            "content": [
                {
                    "type": "tool_use",
                    "id": "call_123",
                    "name": "get_weather",
                    "input": {"location": "Beijing"}
                }
            ],
            "stop_reason": "tool_use",
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "model": "claude-3-sonnet"
        }
        
        with patch.object(anthropic_provider, '_get_client') as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_resp
            mock_client.return_value = mock_http
            
            request = LLMRequest(
                messages=[Message(role="user", content="What's the weather?")],
            )
            
            response = await anthropic_provider.chat(request)
            
            assert response.has_tool_calls
            assert response.tool_calls[0].name == "get_weather"
    
    @pytest.mark.asyncio
    async def test_it_p03_image_understanding(self, anthropic_provider, sample_image_content):
        """IT-P03: Anthropic: 图片理解"""
        # 模拟包含图片描述的响应
        mock_response = {
            "id": "msg_123",
            "content": [{"type": "text", "text": "This image shows a red square."}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 100, "output_tokens": 10},
            "model": "claude-3-sonnet"
        }
        
        with patch.object(anthropic_provider, '_get_client') as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_resp
            mock_client.return_value = mock_http
            
            from openakita.llm.types import ImageBlock
            
            request = LLMRequest(
                messages=[Message(role="user", content=[
                    ImageBlock(image=sample_image_content),
                    TextBlock(text="Describe this image"),
                ])],
            )
            
            response = await anthropic_provider.chat(request)
            
            assert "image" in response.text.lower() or "square" in response.text.lower()
    
    @pytest.mark.asyncio
    async def test_it_p04_stream_response(self, anthropic_provider):
        """IT-P04: Anthropic: 流式响应（预留）"""
        # 流式功能预留测试
        pytest.skip("Streaming not yet fully implemented")


class TestOpenAIProvider:
    """OpenAI Provider 测试"""
    
    @pytest.fixture
    def openai_provider(self, sample_openai_endpoint_config):
        """创建 OpenAI Provider"""
        return OpenAIProvider(sample_openai_endpoint_config)
    
    @pytest.mark.asyncio
    async def test_it_p05_text_chat(self, openai_provider, mock_openai_response):
        """IT-P05: OpenAI: 文本对话"""
        with patch.object(openai_provider, '_get_client') as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_openai_response
            
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_resp
            mock_client.return_value = mock_http
            
            request = LLMRequest(
                messages=[Message(role="user", content="Hello")],
            )
            
            response = await openai_provider.chat(request)
            
            assert isinstance(response, LLMResponse)
            assert "Hello" in response.text
    
    @pytest.mark.asyncio
    async def test_it_p06_tool_call(self, openai_provider, mock_openai_tool_response):
        """IT-P06: OpenAI: 工具调用"""
        with patch.object(openai_provider, '_get_client') as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_openai_tool_response
            
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_resp
            mock_client.return_value = mock_http
            
            from openakita.llm.types import Tool
            
            request = LLMRequest(
                messages=[Message(role="user", content="What's the weather?")],
                tools=[Tool(
                    name="get_weather",
                    description="Get weather",
                    input_schema={"type": "object", "properties": {}}
                )],
            )
            
            response = await openai_provider.chat(request)
            
            assert response.has_tool_calls
            assert response.tool_calls[0].name == "get_weather"
    
    @pytest.mark.asyncio
    async def test_it_p07_image_understanding(self, openai_provider, sample_image_content):
        """IT-P07: OpenAI: 图片理解"""
        mock_response = {
            "id": "chatcmpl-123",
            "choices": [{
                "message": {"role": "assistant", "content": "A red pixel."},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 5}
        }
        
        with patch.object(openai_provider, '_get_client') as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_resp
            mock_client.return_value = mock_http
            
            from openakita.llm.types import ImageBlock
            
            request = LLMRequest(
                messages=[Message(role="user", content=[
                    ImageBlock(image=sample_image_content),
                    TextBlock(text="What is this?"),
                ])],
            )
            
            response = await openai_provider.chat(request)
            
            assert response.text is not None
    
    @pytest.mark.asyncio
    async def test_it_p08_stream_response(self, openai_provider):
        """IT-P08: OpenAI: 流式响应（预留）"""
        pytest.skip("Streaming not yet fully implemented")


class TestDashScopeProvider:
    """DashScope Provider 测试"""
    
    @pytest.fixture
    def dashscope_provider(self):
        """创建 DashScope Provider"""
        config = EndpointConfig(
            name="test-dashscope",
            provider="dashscope",
            api_type="openai",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key_env="DASHSCOPE_API_KEY",
            model="qwen-plus",
            capabilities=["text", "tools", "thinking"],
        )
        return OpenAIProvider(config)
    
    @pytest.mark.asyncio
    async def test_it_p09_text_chat(self, dashscope_provider):
        """IT-P09: DashScope: 文本对话"""
        mock_response = {
            "id": "cmpl-123",
            "choices": [{
                "message": {"role": "assistant", "content": "你好！"},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3}
        }
        
        with patch.object(dashscope_provider, '_get_client') as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_resp
            mock_client.return_value = mock_http
            
            request = LLMRequest(
                messages=[Message(role="user", content="你好")],
            )
            
            response = await dashscope_provider.chat(request)
            
            assert response.text == "你好！"
    
    @pytest.mark.asyncio
    async def test_it_p10_thinking_mode(self, dashscope_provider):
        """IT-P10: DashScope: 思考模式"""
        # 模拟带有 reasoning_content 的响应
        mock_response = {
            "id": "cmpl-123",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "答案是 4",
                    "reasoning_content": "让我思考一下，2+2=4"
                },
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20}
        }
        
        with patch.object(dashscope_provider, '_get_client') as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_resp
            mock_client.return_value = mock_http
            
            request = LLMRequest(
                messages=[Message(role="user", content="2+2=?")],
                enable_thinking=True,
            )
            
            response = await dashscope_provider.chat(request)
            
            # 应该包含思考内容
            assert "<thinking>" in response.text or "答案" in response.text


class TestKimiProvider:
    """Kimi Provider 测试"""
    
    @pytest.mark.asyncio
    async def test_it_p11_video_understanding(self):
        """IT-P11: Kimi: 视频理解"""
        config = EndpointConfig(
            name="test-kimi",
            provider="moonshot",
            api_type="openai",
            base_url="https://api.moonshot.cn/v1",
            api_key_env="MOONSHOT_API_KEY",
            model="kimi-k2.5",
            capabilities=["text", "vision", "video", "tools"],
        )
        provider = OpenAIProvider(config)
        
        mock_response = {
            "id": "cmpl-123",
            "choices": [{
                "message": {"role": "assistant", "content": "This video shows..."},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 500, "completion_tokens": 50}
        }
        
        with patch.object(provider, '_get_client') as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_resp
            mock_client.return_value = mock_http
            
            from openakita.llm.types import VideoBlock, VideoContent
            
            request = LLMRequest(
                messages=[Message(role="user", content=[
                    VideoBlock(video=VideoContent(media_type="video/mp4", data="base64data")),
                    TextBlock(text="Describe this video"),
                ])],
            )
            
            response = await provider.chat(request)
            
            assert response.text is not None


class TestOpenRouterProvider:
    """OpenRouter Provider 测试"""
    
    @pytest.mark.asyncio
    async def test_it_p12_model_routing(self):
        """IT-P12: OpenRouter: 模型路由"""
        config = EndpointConfig(
            name="test-openrouter",
            provider="openrouter",
            api_type="openai",
            base_url="https://openrouter.ai/api/v1",
            api_key_env="OPENROUTER_API_KEY",
            model="anthropic/claude-3-sonnet",
            capabilities=["text", "vision", "tools"],
        )
        provider = OpenAIProvider(config)
        
        mock_response = {
            "id": "gen-123",
            "choices": [{
                "message": {"role": "assistant", "content": "Hello from OpenRouter!"},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        
        with patch.object(provider, '_get_client') as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            
            mock_http = AsyncMock()
            mock_http.post.return_value = mock_resp
            mock_client.return_value = mock_http
            
            request = LLMRequest(
                messages=[Message(role="user", content="Hello")],
            )
            
            response = await provider.chat(request)
            
            assert response.text == "Hello from OpenRouter!"
