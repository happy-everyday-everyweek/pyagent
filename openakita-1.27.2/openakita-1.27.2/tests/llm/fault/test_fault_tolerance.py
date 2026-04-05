"""
故障模拟测试 - 故障容错 (12 个)

FT-01 ~ FT-12
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import httpx

from openakita.llm.types import (
    Message,
    TextBlock,
    EndpointConfig,
    LLMResponse,
    Usage,
    StopReason,
    LLMError,
    AuthenticationError,
    RateLimitError,
    AllEndpointsFailedError,
)
from openakita.llm.client import LLMClient
from openakita.llm.providers.anthropic import AnthropicProvider
from openakita.llm.providers.openai import OpenAIProvider


@pytest.fixture
def multi_endpoint_client():
    """创建多端点客户端"""
    endpoints = [
        EndpointConfig(
            name="primary",
            provider="anthropic",
            api_type="anthropic",
            base_url="https://api.anthropic.com",
            api_key_env="KEY_1",
            model="claude-3-sonnet",
            priority=1,
            capabilities=["text", "tools"],
        ),
        EndpointConfig(
            name="secondary",
            provider="dashscope",
            api_type="openai",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key_env="KEY_2",
            model="qwen-plus",
            priority=2,
            capabilities=["text", "tools"],
        ),
        EndpointConfig(
            name="tertiary",
            provider="openai",
            api_type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="KEY_3",
            model="gpt-4o",
            priority=3,
            capabilities=["text", "tools"],
        ),
    ]
    return LLMClient(endpoints=endpoints)


def create_success_response():
    """创建成功响应"""
    return LLMResponse(
        id="msg_success",
        content=[TextBlock(text="Success!")],
        stop_reason=StopReason.END_TURN,
        usage=Usage(input_tokens=10, output_tokens=5),
        model="test-model",
    )


class TestTimeout:
    """超时测试"""
    
    @pytest.mark.asyncio
    async def test_ft_01_single_timeout(self, multi_endpoint_client):
        """FT-01: 单端点超时"""
        # 主端点超时，备用端点成功
        multi_endpoint_client.providers["primary"].chat = AsyncMock(
            side_effect=LLMError("Request timeout")
        )
        multi_endpoint_client.providers["secondary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        multi_endpoint_client.providers["tertiary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content="Hello")],
        )
        
        assert response.text == "Success!"
        assert multi_endpoint_client.providers["secondary"].chat.called
    
    @pytest.mark.asyncio
    async def test_ft_02_cascade_timeout(self, multi_endpoint_client):
        """FT-02: 级联超时"""
        # 前两个端点都超时
        multi_endpoint_client.providers["primary"].chat = AsyncMock(
            side_effect=LLMError("Timeout 1")
        )
        multi_endpoint_client.providers["secondary"].chat = AsyncMock(
            side_effect=LLMError("Timeout 2")
        )
        multi_endpoint_client.providers["tertiary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content="Hello")],
        )
        
        assert response.text == "Success!"
        assert multi_endpoint_client.providers["tertiary"].chat.called
    
    @pytest.mark.asyncio
    async def test_ft_03_all_timeout(self, multi_endpoint_client):
        """FT-03: 全部超时"""
        for name, provider in multi_endpoint_client.providers.items():
            provider.chat = AsyncMock(side_effect=LLMError("Timeout"))
        
        with pytest.raises(AllEndpointsFailedError):
            await multi_endpoint_client.chat(
                messages=[Message(role="user", content="Hello")],
            )


class TestErrorResponse:
    """错误响应测试"""
    
    @pytest.mark.asyncio
    async def test_ft_04_server_error(self, multi_endpoint_client):
        """FT-04: 服务器错误 (500)"""
        multi_endpoint_client.providers["primary"].chat = AsyncMock(
            side_effect=LLMError("Internal Server Error (500)")
        )
        multi_endpoint_client.providers["secondary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        multi_endpoint_client.providers["tertiary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content="Hello")],
        )
        
        assert response.text == "Success!"
    
    @pytest.mark.asyncio
    async def test_ft_05_auth_error_no_retry(self, multi_endpoint_client):
        """FT-05: 认证错误不重试"""
        # 认证错误应该直接跳到下一个端点，不重试
        multi_endpoint_client.providers["primary"].chat = AsyncMock(
            side_effect=AuthenticationError("Invalid API key")
        )
        multi_endpoint_client.providers["secondary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        multi_endpoint_client.providers["tertiary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content="Hello")],
        )
        
        assert response.text == "Success!"
        # 主端点只调用一次（不重试）
        assert multi_endpoint_client.providers["primary"].chat.call_count == 1
    
    @pytest.mark.asyncio
    async def test_ft_06_rate_limit_retry(self, multi_endpoint_client):
        """FT-06: 速率限制重试"""
        call_count = 0
        
        async def mock_rate_limit(request):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RateLimitError("Rate limit exceeded")
            return create_success_response()
        
        multi_endpoint_client.providers["primary"].chat = mock_rate_limit
        multi_endpoint_client.providers["secondary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        multi_endpoint_client.providers["tertiary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        
        # 修改 settings 允许重试
        multi_endpoint_client._settings = {"retry_count": 3, "retry_delay_seconds": 0.1}
        
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content="Hello")],
        )
        
        assert response.text == "Success!"


class TestFailover:
    """故障切换测试"""
    
    @pytest.mark.asyncio
    async def test_ft_07_auto_failover(self, multi_endpoint_client):
        """FT-07: 自动故障切换"""
        multi_endpoint_client.providers["primary"].chat = AsyncMock(
            side_effect=LLMError("Connection refused")
        )
        multi_endpoint_client.providers["secondary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        multi_endpoint_client.providers["tertiary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content="Hello")],
        )
        
        assert response.text == "Success!"
        # 应该切换到 secondary
        assert multi_endpoint_client.providers["secondary"].chat.called
    
    @pytest.mark.asyncio
    async def test_ft_08_failover_preserves_request(self, multi_endpoint_client):
        """FT-08: 故障切换保持请求"""
        captured_requests = []
        
        async def capture_request(request):
            captured_requests.append(request)
            if len(captured_requests) == 1:
                raise LLMError("First endpoint failed")
            return create_success_response()
        
        multi_endpoint_client.providers["primary"].chat = capture_request
        multi_endpoint_client.providers["secondary"].chat = capture_request
        multi_endpoint_client.providers["tertiary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content="Test message")],
        )
        
        # 请求应该被正确传递
        assert len(captured_requests) == 2
        assert captured_requests[0].messages[0].content == "Test message"
        assert captured_requests[1].messages[0].content == "Test message"
    
    @pytest.mark.asyncio
    async def test_ft_09_partial_degradation(self, multi_endpoint_client):
        """FT-09: 部分降级"""
        # 主端点失败但标记为不健康
        multi_endpoint_client.providers["primary"].mark_unhealthy("Test failure")
        multi_endpoint_client.providers["primary"].chat = AsyncMock(
            side_effect=LLMError("Unhealthy")
        )
        multi_endpoint_client.providers["secondary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        multi_endpoint_client.providers["tertiary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content="Hello")],
        )
        
        # 应该跳过不健康的端点
        assert response.text == "Success!"


class TestHealthCheck:
    """健康检查测试"""
    
    @pytest.mark.asyncio
    async def test_ft_10_health_check_success(self, multi_endpoint_client):
        """FT-10: 健康检查成功"""
        for provider in multi_endpoint_client.providers.values():
            provider.chat = AsyncMock(return_value=create_success_response())
        
        results = await multi_endpoint_client.health_check()
        
        assert all(results.values())
    
    @pytest.mark.asyncio
    async def test_ft_11_health_check_partial(self, multi_endpoint_client):
        """FT-11: 健康检查部分失败"""
        multi_endpoint_client.providers["primary"].chat = AsyncMock(
            side_effect=LLMError("Unhealthy")
        )
        multi_endpoint_client.providers["secondary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        multi_endpoint_client.providers["tertiary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        
        results = await multi_endpoint_client.health_check()
        
        assert results["primary"] == False
        assert results["secondary"] == True
        assert results["tertiary"] == True
    
    @pytest.mark.asyncio
    async def test_ft_12_recovery_after_failure(self, multi_endpoint_client):
        """FT-12: 故障恢复"""
        call_count = 0
        
        async def mock_recovery(request):
            nonlocal call_count
            call_count += 1
            # 第一次失败，之后恢复
            if call_count == 1:
                raise LLMError("Temporary failure")
            return create_success_response()
        
        multi_endpoint_client.providers["primary"].chat = mock_recovery
        multi_endpoint_client.providers["secondary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        multi_endpoint_client.providers["tertiary"].chat = AsyncMock(
            return_value=create_success_response()
        )
        
        # 第一次调用会失败并切换
        response1 = await multi_endpoint_client.chat(
            messages=[Message(role="user", content="Hello 1")],
        )
        
        # 标记 primary 恢复健康
        multi_endpoint_client.providers["primary"].mark_healthy()
        
        # 第二次调用可以使用 primary
        response2 = await multi_endpoint_client.chat(
            messages=[Message(role="user", content="Hello 2")],
        )
        
        assert response1.text == "Success!"
        assert response2.text == "Success!"
