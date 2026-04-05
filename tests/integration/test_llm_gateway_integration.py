"""
PyAgent 集成测试 - LLM网关集成测试

测试LLM网关与各提供商适配器的集成。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from llm.gateway import (
    ModelGateway,
    ModelGatewayConfig,
    ProviderInfo,
    ProviderType,
)
from llm.adapters.openai_adapter import OpenAIAdapter
from llm.adapters.anthropic_adapter import AnthropicAdapter


class TestLLMGatewayIntegration:
    """LLM网关集成测试"""

    def setup_method(self):
        self.gateway = ModelGateway()

    @pytest.mark.asyncio
    async def test_openai_adapter_creation(self):
        """测试OpenAI适配器创建"""
        provider = ProviderInfo(
            name="openai",
            provider_type=ProviderType.OPENAI,
            api_key="test_key",
            default_model="gpt-4"
        )
        self.gateway.register_provider(provider)

        adapter = await self.gateway._get_adapter("openai", provider)
        assert isinstance(adapter, OpenAIAdapter)

    @pytest.mark.asyncio
    async def test_anthropic_adapter_creation(self):
        """测试Anthropic适配器创建"""
        provider = ProviderInfo(
            name="anthropic",
            provider_type=ProviderType.ANTHROPIC,
            api_key="test_key",
            default_model="claude-3-opus"
        )
        self.gateway.register_provider(provider)

        adapter = await self.gateway._get_adapter("anthropic", provider)
        assert isinstance(adapter, AnthropicAdapter)

    @pytest.mark.asyncio
    async def test_chat_with_mock_adapter(self):
        """测试使用模拟适配器的聊天功能"""
        provider = ProviderInfo(
            name="openai",
            provider_type=ProviderType.OPENAI,
            api_key="test_key",
            default_model="gpt-4"
        )
        self.gateway.register_provider(provider)

        mock_adapter = AsyncMock()
        mock_adapter.chat = AsyncMock(return_value={
            "choices": [{"message": {"content": "Hello!"}}],
            "usage": {"total_tokens": 10}
        })

        self.gateway._adapters["openai"] = mock_adapter

        response = await self.gateway.chat(
            messages=[{"role": "user", "content": "Hi"}],
            model="gpt-4"
        )

        assert response["choices"][0]["message"]["content"] == "Hello!"
        mock_adapter.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_chain(self):
        """测试故障转移链"""
        config = ModelGatewayConfig(
            enable_fallback=True,
            fallback_order=["backup1", "backup2"]
        )
        gateway = ModelGateway(config=config)

        primary = ProviderInfo(
            name="primary",
            provider_type=ProviderType.OPENAI,
            api_key="primary_key"
        )
        backup1 = ProviderInfo(
            name="backup1",
            provider_type=ProviderType.OPENAI,
            api_key="backup1_key"
        )
        backup2 = ProviderInfo(
            name="backup2",
            provider_type=ProviderType.OPENAI,
            api_key="backup2_key"
        )

        gateway.register_provider(primary)
        gateway.register_provider(backup1)
        gateway.register_provider(backup2)

        mock_primary = AsyncMock()
        mock_primary.chat = AsyncMock(side_effect=Exception("Primary failed"))

        mock_backup1 = AsyncMock()
        mock_backup1.chat = AsyncMock(return_value={
            "choices": [{"message": {"content": "Backup response"}}]
        })

        gateway._adapters["primary"] = mock_primary
        gateway._adapters["backup1"] = mock_backup1

        response = await gateway._fallback_chat(
            messages=[{"role": "user", "content": "test"}],
            model="gpt-4",
            failed_provider="primary",
            error="Primary failed"
        )

        assert response["choices"][0]["message"]["content"] == "Backup response"

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """测试速率限制"""
        provider = ProviderInfo(
            name="openai",
            provider_type=ProviderType.OPENAI,
            api_key="test_key",
            rate_limit_rpm=2
        )
        self.gateway.register_provider(provider)

        assert "openai" in self.gateway._rate_limits
        assert self.gateway._rate_limits["openai"]["requests"] == []

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        provider = ProviderInfo(
            name="openai",
            provider_type=ProviderType.OPENAI,
            api_key="test_key"
        )
        self.gateway.register_provider(provider)

        mock_adapter = AsyncMock()
        mock_adapter.health_check = AsyncMock(return_value=True)
        self.gateway._adapters["openai"] = mock_adapter

        results = await self.gateway.health_check()
        assert results["openai"] is True


class TestOpenAIAdapterIntegration:
    """OpenAI适配器集成测试"""

    def test_adapter_creation(self):
        """测试适配器创建"""
        adapter = OpenAIAdapter(
            api_key="test_key",
            base_url="https://api.openai.com/v1",
            model="gpt-4"
        )
        assert adapter.api_key == "test_key"
        assert adapter.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_chat_with_mock_client(self):
        """测试使用模拟客户端的聊天"""
        adapter = OpenAIAdapter(
            api_key="test_key",
            model="gpt-4"
        )

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.total_tokens = 10

        with patch.object(adapter, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            response = await adapter.chat(
                messages=[{"role": "user", "content": "Hello"}]
            )

            assert response["choices"][0]["message"]["content"] == "Test response"


class TestAnthropicAdapterIntegration:
    """Anthropic适配器集成测试"""

    def test_adapter_creation(self):
        """测试适配器创建"""
        adapter = AnthropicAdapter(
            api_key="test_key",
            model="claude-3-opus"
        )
        assert adapter.api_key == "test_key"
        assert adapter.model == "claude-3-opus"

    @pytest.mark.asyncio
    async def test_chat_with_mock_client(self):
        """测试使用模拟客户端的聊天"""
        adapter = AnthropicAdapter(
            api_key="test_key",
            model="claude-3-opus"
        )

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Test response"
        mock_response.usage.input_tokens = 5
        mock_response.usage.output_tokens = 5

        with patch.object(adapter, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.messages = MagicMock()
            mock_client.messages.create = MagicMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            response = await adapter.chat(
                messages=[{"role": "user", "content": "Hello"}]
            )

            assert response["choices"][0]["message"]["content"] == "Test response"


class TestModelDetectionIntegration:
    """模型检测集成测试"""

    def setup_method(self):
        self.gateway = ModelGateway()

    def test_detect_openai_models(self):
        """测试OpenAI模型检测"""
        assert self.gateway._detect_provider_from_model("gpt-4") == "openai"
        assert self.gateway._detect_provider_from_model("gpt-3.5-turbo") == "openai"
        assert self.gateway._detect_provider_from_model("gpt-4o") == "openai"
        assert self.gateway._detect_provider_from_model("o1-preview") == "openai"
        assert self.gateway._detect_provider_from_model("o1-mini") == "openai"

    def test_detect_anthropic_models(self):
        """测试Anthropic模型检测"""
        assert self.gateway._detect_provider_from_model("claude-3-opus") == "anthropic"
        assert self.gateway._detect_provider_from_model("claude-3-sonnet") == "anthropic"
        assert self.gateway._detect_provider_from_model("claude-3-haiku") == "anthropic"
        assert self.gateway._detect_provider_from_model("claude-2") == "anthropic"

    def test_detect_deepseek_models(self):
        """测试DeepSeek模型检测"""
        assert self.gateway._detect_provider_from_model("deepseek-chat") == "deepseek"
        assert self.gateway._detect_provider_from_model("deepseek-coder") == "deepseek"

    def test_detect_zhipu_models(self):
        """测试智谱模型检测"""
        assert self.gateway._detect_provider_from_model("glm-4") == "zhipu"
        assert self.gateway._detect_provider_from_model("glm-4v") == "zhipu"
        assert self.gateway._detect_provider_from_model("glm-3-turbo") == "zhipu"

    def test_detect_moonshot_models(self):
        """测试Moonshot模型检测"""
        assert self.gateway._detect_provider_from_model("moonshot-v1-8k") == "moonshot"
        assert self.gateway._detect_provider_from_model("moonshot-v1-32k") == "moonshot"

    def test_detect_baidu_models(self):
        """测试百度模型检测"""
        assert self.gateway._detect_provider_from_model("ernie-bot") == "baidu"
        assert self.gateway._detect_provider_from_model("ernie-bot-turbo") == "baidu"

    def test_detect_alibaba_models(self):
        """测试阿里模型检测"""
        assert self.gateway._detect_provider_from_model("qwen-max") == "alibaba"
        assert self.gateway._detect_provider_from_model("qwen-plus") == "alibaba"
        assert self.gateway._detect_provider_from_model("qwen-turbo") == "alibaba"
