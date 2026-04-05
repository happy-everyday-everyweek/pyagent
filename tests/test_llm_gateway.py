"""
PyAgent LLM模型网关测试
"""

import pytest

from llm.gateway import (
    ModelGateway,
    ModelGatewayConfig,
    ProviderInfo,
    ProviderType,
    model_gateway,
)


class TestProviderType:
    """测试提供商类型枚举"""

    def test_provider_type_values(self):
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.ANTHROPIC.value == "anthropic"
        assert ProviderType.DEEPSEEK.value == "deepseek"
        assert ProviderType.ZHIPU.value == "zhipu"
        assert ProviderType.MOONSHOT.value == "moonshot"
        assert ProviderType.BAIDU.value == "baidu"
        assert ProviderType.ALIBABA.value == "alibaba"
        assert ProviderType.LOCAL.value == "local"
        assert ProviderType.CUSTOM.value == "custom"

    def test_provider_type_count(self):
        assert len(ProviderType) == 9


class TestProviderInfo:
    """测试提供商信息"""

    def test_provider_info_creation(self):
        info = ProviderInfo(
            name="test_provider",
            provider_type=ProviderType.OPENAI,
            base_url="https://api.example.com",
            api_key="test_key",
            default_model="gpt-4"
        )
        assert info.name == "test_provider"
        assert info.provider_type == ProviderType.OPENAI
        assert info.base_url == "https://api.example.com"
        assert info.default_model == "gpt-4"

    def test_provider_info_defaults(self):
        info = ProviderInfo(
            name="test",
            provider_type=ProviderType.OPENAI
        )
        assert info.supports_streaming is True
        assert info.supports_tools is True
        assert info.supports_vision is False
        assert info.max_context_length == 4096


class TestModelGatewayConfig:
    """测试模型网关配置"""

    def test_config_defaults(self):
        config = ModelGatewayConfig()
        assert config.enable_fallback is True
        assert config.default_timeout == 60
        assert config.max_retries == 3
        assert config.retry_delay == 1.0

    def test_config_custom(self):
        config = ModelGatewayConfig(
            enable_fallback=False,
            default_timeout=120,
            max_retries=5
        )
        assert config.enable_fallback is False
        assert config.default_timeout == 120
        assert config.max_retries == 5


class TestModelGateway:
    """测试模型网关"""

    def setup_method(self):
        self.gateway = ModelGateway()

    def test_gateway_creation(self):
        assert self.gateway.config is not None
        assert self.gateway._providers == {}
        assert self.gateway._adapters == {}

    def test_register_provider(self):
        provider = ProviderInfo(
            name="openai",
            provider_type=ProviderType.OPENAI,
            api_key="test_key"
        )
        self.gateway.register_provider(provider)

        assert "openai" in self.gateway._providers
        assert self.gateway.get_provider("openai") == provider

    def test_get_nonexistent_provider(self):
        provider = self.gateway.get_provider("nonexistent")
        assert provider is None

    def test_list_providers(self):
        provider1 = ProviderInfo(
            name="openai",
            provider_type=ProviderType.OPENAI
        )
        provider2 = ProviderInfo(
            name="anthropic",
            provider_type=ProviderType.ANTHROPIC
        )

        self.gateway.register_provider(provider1)
        self.gateway.register_provider(provider2)

        providers = self.gateway.list_providers()
        assert len(providers) == 2

    def test_detect_provider_from_model(self):
        assert self.gateway._detect_provider_from_model("gpt-4") == "openai"
        assert self.gateway._detect_provider_from_model("gpt-3.5-turbo") == "openai"
        assert self.gateway._detect_provider_from_model("o1-preview") == "openai"
        assert self.gateway._detect_provider_from_model("claude-3-opus") == "anthropic"
        assert self.gateway._detect_provider_from_model("deepseek-chat") == "deepseek"
        assert self.gateway._detect_provider_from_model("glm-4") == "zhipu"
        assert self.gateway._detect_provider_from_model("moonshot-v1") == "moonshot"
        assert self.gateway._detect_provider_from_model("ernie-bot") == "baidu"
        assert self.gateway._detect_provider_from_model("qwen-max") == "alibaba"

    def test_get_supported_models(self):
        provider = ProviderInfo(
            name="openai",
            provider_type=ProviderType.OPENAI,
            api_key="test_key"
        )
        self.gateway.register_provider(provider)

        models = self.gateway.get_supported_models("openai")
        assert len(models) > 0
        assert "gpt-4o" in models or "gpt-3.5-turbo" in models

        anthropic_provider = ProviderInfo(
            name="anthropic",
            provider_type=ProviderType.ANTHROPIC,
            api_key="test_key"
        )
        self.gateway.register_provider(anthropic_provider)

        models = self.gateway.get_supported_models("anthropic")
        assert len(models) > 0

    def test_get_supported_models_unknown_provider(self):
        models = self.gateway.get_supported_models("unknown")
        assert models == []

    @pytest.mark.asyncio
    async def test_chat_without_provider(self):
        provider = ProviderInfo(
            name="openai",
            provider_type=ProviderType.OPENAI,
            api_key="test_key"
        )
        self.gateway.register_provider(provider)

        with pytest.raises(Exception):
            await self.gateway.chat(
                messages=[{"role": "user", "content": "Hello"}],
                model="gpt-4"
            )

    @pytest.mark.asyncio
    async def test_chat_unknown_provider(self):
        with pytest.raises(ValueError):
            await self.gateway.chat(
                messages=[{"role": "user", "content": "Hello"}],
                model="gpt-4",
                provider="unknown"
            )


class TestModelGatewayGlobal:
    """测试全局模型网关实例"""

    def test_global_instance(self):
        assert model_gateway is not None
        assert isinstance(model_gateway, ModelGateway)
