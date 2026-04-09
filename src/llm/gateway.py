"""
PyAgent LLM模块 - 模型网关

参考LiteLLM设计，提供统一的模型提供商接口。
"""

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    ZHIPU = "zhipu"
    MOONSHOT = "moonshot"
    BAIDU = "baidu"
    ALIBABA = "alibaba"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclass
class ProviderInfo:
    name: str
    provider_type: ProviderType
    base_url: str = ""
    api_key: str = ""
    default_model: str = ""
    supports_streaming: bool = True
    supports_tools: bool = True
    supports_vision: bool = False
    max_context_length: int = 4096
    rate_limit_rpm: int = 60
    rate_limit_tpm: int = 100000


@dataclass
class ModelGatewayConfig:
    enable_fallback: bool = True
    fallback_order: list[str] = field(default_factory=list)
    default_timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0


class ModelGateway:
    """统一模型网关

    提供统一的接口访问多个LLM提供商。
    """

    def __init__(self, config: ModelGatewayConfig | None = None):
        self.config = config or ModelGatewayConfig()
        self._providers: dict[str, ProviderInfo] = {}
        self._adapters: dict[str, Any] = {}
        self._rate_limits: dict[str, dict[str, Any]] = {}

    def register_provider(self, provider_info: ProviderInfo) -> None:
        self._providers[provider_info.name] = provider_info
        self._rate_limits[provider_info.name] = {
            "requests": [],
            "tokens": [],
        }

    def get_provider(self, name: str) -> ProviderInfo | None:
        return self._providers.get(name)

    def list_providers(self) -> list[ProviderInfo]:
        return list(self._providers.values())

    async def chat(
        self,
        messages: list[dict[str, Any]],
        model: str,
        provider: str | None = None,
        **kwargs
    ) -> dict[str, Any]:
        if provider is None:
            provider = self._detect_provider_from_model(model)

        provider_info = self.get_provider(provider)
        if not provider_info:
            raise ValueError(f"Unknown provider: {provider}")

        adapter = await self._get_adapter(provider, provider_info)

        try:
            response = await adapter.chat(
                messages=messages,
                model=model,
                **kwargs
            )
            return response
        except Exception as e:
            if self.config.enable_fallback:
                return await self._fallback_chat(messages, model, provider, str(e))
            raise

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        model: str,
        provider: str | None = None,
        **kwargs
    ) -> AsyncIterator[dict[str, Any]]:
        if provider is None:
            provider = self._detect_provider_from_model(model)

        provider_info = self.get_provider(provider)
        if not provider_info:
            raise ValueError(f"Unknown provider: {provider}")

        if not provider_info.supports_streaming:
            response = await self.chat(messages, model, provider, **kwargs)
            yield response
            return

        adapter = await self._get_adapter(provider, provider_info)

        async for chunk in adapter.chat_stream(
            messages=messages,
            model=model,
            **kwargs
        ):
            yield chunk

    def _detect_provider_from_model(self, model: str) -> str:
        model_lower = model.lower()

        if "gpt" in model_lower or "o1" in model_lower:
            return "openai"
        if "claude" in model_lower:
            return "anthropic"
        if "deepseek" in model_lower:
            return "deepseek"
        if "glm" in model_lower:
            return "zhipu"
        if "moonshot" in model_lower:
            return "moonshot"
        if "ernie" in model_lower:
            return "baidu"
        if "qwen" in model_lower:
            return "alibaba"

        return "openai"

    async def _get_adapter(self, provider: str, provider_info: ProviderInfo) -> Any:
        if provider in self._adapters:
            return self._adapters[provider]

        adapter = await self._create_adapter(provider_info)
        self._adapters[provider] = adapter
        return adapter

    async def _create_adapter(self, provider_info: ProviderInfo) -> Any:
        from .adapters.anthropic_adapter import AnthropicAdapter
        from .adapters.openai_adapter import OpenAIAdapter

        if provider_info.provider_type == ProviderType.ANTHROPIC:
            return AnthropicAdapter(
                api_key=provider_info.api_key,
                base_url=provider_info.base_url,
                model=provider_info.default_model,
            )
        return OpenAIAdapter(
            api_key=provider_info.api_key,
            base_url=provider_info.base_url,
            model=provider_info.default_model,
            provider=provider_info.provider_type.value,
        )

    async def _fallback_chat(
        self,
        messages: list[dict[str, Any]],
        model: str,
        failed_provider: str,
        error: str
    ) -> dict[str, Any]:
        logger.warning(f"Provider {failed_provider} failed: {error}, trying fallback")

        fallback_order = self.config.fallback_order or [
            p for p in self._providers.keys() if p != failed_provider
        ]

        for fallback_provider in fallback_order:
            try:
                provider_info = self.get_provider(fallback_provider)
                if not provider_info:
                    continue

                adapter = await self._get_adapter(fallback_provider, provider_info)
                fallback_model = provider_info.default_model

                response = await adapter.chat(
                    messages=messages,
                    model=fallback_model,
                )
                logger.info(f"Fallback to {fallback_provider} succeeded")
                return response
            except Exception as e:
                logger.warning(f"Fallback provider {fallback_provider} also failed: {e}")
                continue

        raise Exception("All providers failed")

    async def embeddings(
        self,
        texts: list[str],
        model: str = "text-embedding-ada-002",
        provider: str | None = None,
    ) -> list[list[float]]:
        if provider is None:
            provider = self._detect_provider_from_model(model)

        provider_info = self.get_provider(provider)
        if not provider_info:
            raise ValueError(f"Unknown provider: {provider}")

        adapter = await self._get_adapter(provider, provider_info)

        if hasattr(adapter, "embeddings"):
            return await adapter.embeddings(texts, model)

        raise NotImplementedError(f"Provider {provider} does not support embeddings")

    async def health_check(self) -> dict[str, bool]:
        results = {}

        for provider_name, provider_info in self._providers.items():
            try:
                adapter = await self._get_adapter(provider_name, provider_info)
                if hasattr(adapter, "health_check"):
                    results[provider_name] = await adapter.health_check()
                else:
                    results[provider_name] = True
            except Exception:
                results[provider_name] = False

        return results

    def get_supported_models(self, provider: str) -> list[str]:
        provider_info = self.get_provider(provider)
        if not provider_info:
            return []

        models_map = {
            "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "o1", "o1-mini"],
            "anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            "deepseek": ["deepseek-chat", "deepseek-coder"],
            "zhipu": ["glm-4", "glm-4v", "glm-3-turbo"],
            "moonshot": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        }

        return models_map.get(provider, [])


model_gateway = ModelGateway()
