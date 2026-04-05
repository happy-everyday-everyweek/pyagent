"""
PyAgent LLM客户端

支持新的模型架构：
- 基础模型（必填）
- 分级模型（STRONG/PERFORMANCE/COST_EFFECTIVE）
- 垂类模型（SCREEN_OPERATION/MULTIMODAL/CUSTOM）
- 任务类型到模型的自动映射
- 多模态模型回退机制
"""

import asyncio
import logging
import random
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .adapters.anthropic_adapter import AnthropicAdapter
from .adapters.base import (
    BaseAdapter,
    LLMError,
    LLMRequest,
    LLMResponse,
    Message,
    NetworkError,
    RateLimitError,
    StreamChunk,
    Tool,
)
from .adapters.openai_adapter import OpenAIAdapter
from .config import get_model_config_loader
from .types import (
    TASK_TO_TIER,
    TASK_TO_VERTICAL,
    ModelConfig,
    ModelTier,
    TaskType,
    VerticalModelConfig,
    VerticalType,
    is_vertical_task,
)

logger = logging.getLogger(__name__)


class AdapterType:
    """适配器类型"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    ZHIPU = "zhipu"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class ModelUsage:
    """模型使用统计"""
    total_tokens: int = 0
    penalty: int = 0
    usage_penalty: int = 0
    last_success: datetime | None = None
    last_failure: datetime | None = None
    consecutive_failures: int = 0
    cooldown_until: datetime | None = None

    def is_in_cooldown(self) -> bool:
        if self.cooldown_until is None:
            return False
        return datetime.now() < self.cooldown_until

    def set_cooldown(self, seconds: int):
        self.cooldown_until = datetime.now() + timedelta(seconds=seconds)

    def clear_cooldown(self):
        self.cooldown_until = None


class AllModelsFailedError(LLMError):
    """所有模型都失败"""
    def __init__(self, message: str, failed_models: list[str] | None = None):
        super().__init__(message)
        self.failed_models = failed_models or []


class LLMClient:
    """LLM客户端

    支持新的模型架构：
    - 基础模型作为默认模型
    - 分级模型根据任务类型自动选择
    - 垂类模型处理特殊场景
    - 多模态模型回退机制
    """

    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0
    DEFAULT_COOLDOWN_SECONDS = 60
    MAX_COOLDOWN_SECONDS = 300

    def __init__(self):
        self._config_loader = get_model_config_loader()
        self._adapters: dict[str, BaseAdapter] = {}
        self._model_usage: dict[str, ModelUsage] = {}
        self._max_retries = self.DEFAULT_MAX_RETRIES
        self._retry_delay = self.DEFAULT_RETRY_DELAY

    def _get_adapter_for_model(self, model: ModelConfig | VerticalModelConfig) -> BaseAdapter:
        """获取模型对应的适配器"""
        model_key = f"{model.provider}:{model.name}"

        if model_key not in self._adapters:
            provider = model.provider.lower()

            if provider == "anthropic":
                adapter = AnthropicAdapter(
                    api_key=model.api_key or "",
                    base_url=model.base_url,
                    model=model.name,
                    timeout=model.timeout or 60,
                    max_retries=model.retry_count or 3,
                )
            else:
                adapter = OpenAIAdapter(
                    api_key=model.api_key or "",
                    base_url=model.base_url,
                    model=model.name,
                    timeout=model.timeout or 60,
                    max_retries=model.retry_count or 3,
                    provider=provider,
                )

            self._adapters[model_key] = adapter
            self._model_usage[model_key] = ModelUsage()

        return self._adapters[model_key]

    def _get_model_key(self, model: ModelConfig | VerticalModelConfig) -> str:
        """获取模型的唯一键"""
        return f"{model.provider}:{model.name}"

    def select_model_for_task(self, task_type: TaskType) -> ModelConfig | VerticalModelConfig:
        """根据任务类型选择模型

        Args:
            task_type: 任务类型

        Returns:
            模型配置
        """
        return self._config_loader.get_model_for_task(task_type)

    def select_vertical_model(self, vertical_type: VerticalType) -> VerticalModelConfig:
        """选择垂类模型

        Args:
            vertical_type: 垂类模型类型

        Returns:
            垂类模型配置

        Raises:
            ModelNotFoundError: 垂类模型未配置
        """
        return self._config_loader.get_vertical_model(vertical_type)

    def get_base_model(self) -> ModelConfig:
        """获取基础模型"""
        return self._config_loader.get_base_model()

    def get_tier_model(self, tier: ModelTier) -> ModelConfig:
        """获取指定层级的模型"""
        return self._config_loader.get_tier_model(tier)

    async def generate(
        self,
        messages: list[Message],
        system: str = "",
        tools: list[Tool] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        task_type: TaskType | None = None,
        model: ModelConfig | VerticalModelConfig | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """生成响应

        Args:
            messages: 消息列表
            system: 系统提示
            tools: 工具列表
            max_tokens: 最大token数
            temperature: 温度参数
            task_type: 任务类型（用于自动选择模型）
            model: 指定模型配置
            extra_params: 额外参数

        Returns:
            LLM响应
        """
        if model is None:
            if task_type:
                model = self.select_model_for_task(task_type)
            else:
                model = self.get_base_model()

        request = LLMRequest(
            messages=messages,
            system=system,
            tools=tools,
            max_tokens=max_tokens or model.max_tokens,
            temperature=temperature if temperature is not None else model.temperature,
            extra_params=extra_params,
        )

        return await self._execute_with_retry(model, request)

    async def generate_stream(
        self,
        messages: list[Message],
        system: str = "",
        tools: list[Tool] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        task_type: TaskType | None = None,
        model: ModelConfig | VerticalModelConfig | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """流式生成响应

        Args:
            messages: 消息列表
            system: 系统提示
            tools: 工具列表
            max_tokens: 最大token数
            temperature: 温度参数
            task_type: 任务类型
            model: 指定模型配置
            extra_params: 额外参数

        Yields:
            流式响应块
        """
        if model is None:
            if task_type:
                model = self.select_model_for_task(task_type)
            else:
                model = self.get_base_model()

        request = LLMRequest(
            messages=messages,
            system=system,
            tools=tools,
            max_tokens=max_tokens or model.max_tokens,
            temperature=temperature if temperature is not None else model.temperature,
            extra_params=extra_params,
        )

        async for chunk in self._execute_stream_with_retry(model, request):
            yield chunk

    async def call_vertical_model(
        self,
        vertical_type: VerticalType,
        messages: list[Message],
        system: str = "",
        tools: list[Tool] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """调用垂类模型

        Args:
            vertical_type: 垂类模型类型
            messages: 消息列表
            system: 系统提示
            tools: 工具列表
            max_tokens: 最大token数
            temperature: 温度参数
            extra_params: 额外参数

        Returns:
            LLM响应
        """
        model = self.select_vertical_model(vertical_type)
        return await self.generate(
            messages=messages,
            system=system,
            tools=tools,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
            extra_params=extra_params,
        )

    async def generate_with_multimodal_fallback(
        self,
        messages: list[Message],
        system: str = "",
        tools: list[Tool] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        task_type: TaskType | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """生成响应，支持多模态回退

        如果当前模型不支持多模态，会使用垂类多模态模型处理

        Args:
            messages: 消息列表
            system: 系统提示
            tools: 工具列表
            max_tokens: 最大token数
            temperature: 温度参数
            task_type: 任务类型
            extra_params: 额外参数

        Returns:
            LLM响应
        """
        model = self.select_model_for_task(task_type) if task_type else self.get_base_model()

        has_multimodal_content = self._check_multimodal_content(messages)

        if has_multimodal_content and not self._model_supports_multimodal(model):
            if self._config_loader.has_vertical_model(VerticalType.MULTIMODAL):
                logger.info("当前模型不支持多模态，使用垂类多模态模型处理")
                multimodal_model = self.select_vertical_model(VerticalType.MULTIMODAL)

                multimodal_response = await self.generate(
                    messages=messages,
                    system=system,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model=multimodal_model,
                    extra_params=extra_params,
                )

                return multimodal_response
            else:
                logger.warning("当前模型不支持多模态，且未配置垂类多模态模型")

        return await self.generate(
            messages=messages,
            system=system,
            tools=tools,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
            extra_params=extra_params,
        )

    def _check_multimodal_content(self, messages: list[Message]) -> bool:
        """检查消息是否包含多模态内容"""
        for message in messages:
            content = message.content
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        part_type = part.get("type", "")
                        if part_type in ["image", "image_url", "video", "audio"]:
                            return True
        return False

    def _model_supports_multimodal(self, model: ModelConfig | VerticalModelConfig) -> bool:
        """检查模型是否支持多模态"""
        capabilities = model.capabilities or []
        multimodal_caps = ["vision", "image", "audio", "video", "multimodal"]
        return any(cap in capabilities for cap in multimodal_caps)

    async def _execute_with_retry(
        self,
        model: ModelConfig | VerticalModelConfig,
        request: LLMRequest,
    ) -> LLMResponse:
        """带重试的执行"""
        model_key = self._get_model_key(model)
        adapter = self._get_adapter_for_model(model)

        for attempt in range(self._max_retries):
            try:
                usage = self._model_usage.get(model_key)
                if usage and usage.is_in_cooldown():
                    raise LLMError(f"Model {model_key} is in cooldown")

                response = await adapter.generate(request)

                if model_key in self._model_usage:
                    self._model_usage[model_key].total_tokens += response.usage.total_tokens
                    self._model_usage[model_key].last_success = datetime.now()
                    self._model_usage[model_key].consecutive_failures = 0
                    self._model_usage[model_key].clear_cooldown()

                return response

            except (RateLimitError, NetworkError) as e:
                self._record_failure(model_key)
                logger.warning(f"Model '{model_key}' failed: {e}")

                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))

            except LLMError as e:
                logger.error(f"Model '{model_key}' LLM error: {e}")
                raise

        raise AllModelsFailedError(f"All retries failed for model {model_key}")

    async def _execute_stream_with_retry(
        self,
        model: ModelConfig | VerticalModelConfig,
        request: LLMRequest,
    ) -> AsyncIterator[StreamChunk]:
        """带重试的流式执行"""
        model_key = self._get_model_key(model)
        adapter = self._get_adapter_for_model(model)

        for attempt in range(self._max_retries):
            try:
                usage = self._model_usage.get(model_key)
                if usage and usage.is_in_cooldown():
                    raise LLMError(f"Model {model_key} is in cooldown")

                async for chunk in adapter.generate_stream(request):
                    yield chunk

                if model_key in self._model_usage:
                    self._model_usage[model_key].last_success = datetime.now()
                    self._model_usage[model_key].consecutive_failures = 0
                    self._model_usage[model_key].clear_cooldown()

                return

            except (RateLimitError, NetworkError) as e:
                self._record_failure(model_key)
                logger.warning(f"Model '{model_key}' stream failed: {e}")

                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))

            except LLMError as e:
                logger.error(f"Model '{model_key}' stream LLM error: {e}")
                raise

        raise AllModelsFailedError(f"All retries failed for model {model_key}")

    def _record_failure(self, model_key: str):
        """记录失败"""
        if model_key in self._model_usage:
            usage = self._model_usage[model_key]
            usage.penalty += 1
            usage.last_failure = datetime.now()
            usage.consecutive_failures += 1

            cooldown_seconds = min(
                self.DEFAULT_COOLDOWN_SECONDS * (2 ** (usage.consecutive_failures - 1)),
                self.MAX_COOLDOWN_SECONDS,
            )
            usage.set_cooldown(cooldown_seconds)

    async def health_check(self) -> dict[str, bool]:
        """健康检查"""
        results = {}

        base_model = self.get_base_model()
        model_key = self._get_model_key(base_model)

        try:
            adapter = self._get_adapter_for_model(base_model)
            results[model_key] = await adapter.health_check()
        except Exception as e:
            logger.warning(f"Health check failed for '{model_key}': {e}")
            results[model_key] = False

        return results

    def get_model_status(self) -> dict[str, dict[str, Any]]:
        """获取模型状态"""
        status = {}

        for model_key, usage in self._model_usage.items():
            status[model_key] = {
                "total_tokens": usage.total_tokens,
                "penalty": usage.penalty,
                "consecutive_failures": usage.consecutive_failures,
                "in_cooldown": usage.is_in_cooldown(),
                "last_success": usage.last_success.isoformat() if usage.last_success else None,
                "last_failure": usage.last_failure.isoformat() if usage.last_failure else None,
            }

        return status

    def reset_cooldowns(self):
        """重置所有冷却"""
        for usage in self._model_usage.values():
            usage.clear_cooldown()
            usage.consecutive_failures = 0
        logger.info("All model cooldowns reset")

    async def close(self):
        """关闭客户端"""
        for adapter in self._adapters.values():
            if hasattr(adapter, "close"):
                await adapter.close()
        self._adapters.clear()


_default_client: LLMClient | None = None


def get_default_client() -> LLMClient:
    """获取默认客户端"""
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client


def set_default_client(client: LLMClient):
    """设置默认客户端"""
    global _default_client
    _default_client = client


def create_client_from_env() -> LLMClient:
    """从环境变量创建LLM客户端

    从环境变量读取配置并创建默认客户端。
    如果已有默认客户端，直接返回。

    Returns:
        LLMClient: LLM客户端实例
    """
    global _default_client

    if _default_client is not None:
        return _default_client

    client = LLMClient()
    _default_client = client

    return client
