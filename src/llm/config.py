"""
PyAgent LLM 模型配置加载器

从 config/models.yaml 加载模型配置，支持：
- 基础模型配置（必填）
- 分级模型架构（STRONG/PERFORMANCE/COST_EFFECTIVE）
- 垂类模型支持（SCREEN_OPERATION/MULTIMODAL/CUSTOM）
- 环境变量替换
- 任务类型到模型的自动映射
- 提供商配置管理
"""

import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml

from .types import (
    TASK_TO_TIER,
    TASK_TO_VERTICAL,
    ConfigurationError,
    ModelConfig,
    ModelNotFoundError,
    ModelTier,
    ProviderConfig,
    RoutingConfig,
    TaskType,
    VerticalModelConfig,
    VerticalType,
    is_vertical_task,
)

logger = logging.getLogger(__name__)

ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def substitute_env_vars(value: str) -> str:
    """替换字符串中的环境变量

    支持格式: ${ENV_VAR_NAME}

    Args:
        value: 包含环境变量占位符的字符串

    Returns:
        替换后的字符串
    """
    if not isinstance(value, str):
        return value

    def replace(match: re.Match) -> str:
        var_name = match.group(1)
        env_value = os.environ.get(var_name, "")
        if not env_value:
            logger.warning(f"环境变量 '{var_name}' 未设置")
        return env_value

    return ENV_VAR_PATTERN.sub(replace, value)


def deep_substitute_env_vars(obj: Any) -> Any:
    """递归替换字典/列表中的所有环境变量

    Args:
        obj: 要处理的对象

    Returns:
        处理后的对象
    """
    if isinstance(obj, str):
        return substitute_env_vars(obj)
    elif isinstance(obj, dict):
        return {k: deep_substitute_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deep_substitute_env_vars(item) for item in obj]
    return obj


class ModelConfigLoader:
    """模型配置加载器

    从 YAML 配置文件加载模型配置，支持：
    - 基础模型配置
    - 分级模型架构
    - 垂类模型支持
    - 环境变量替换
    - 任务类型映射
    - 提供商配置
    - 路由规则
    """

    DEFAULT_CONFIG_PATH = "config/models.yaml"

    def __init__(self, config_path: str | Path | None = None):
        """初始化配置加载器

        Args:
            config_path: 配置文件路径，默认为 config/models.yaml
        """
        self._config_path = self._resolve_config_path(config_path)
        self._base_model: ModelConfig | None = None
        self._tier_models: dict[ModelTier, ModelConfig] = {}
        self._vertical_models: dict[VerticalType, VerticalModelConfig] = {}
        self._providers: dict[str, ProviderConfig] = {}
        self._routing: RoutingConfig | None = None
        self._raw_config: dict[str, Any] = {}

        self._load_config()

    def _resolve_config_path(self, config_path: str | Path | None) -> Path:
        """解析配置文件路径

        Args:
            config_path: 用户指定的路径

        Returns:
            解析后的绝对路径
        """
        if config_path:
            path = Path(config_path)
            if path.is_absolute():
                return path
            return Path.cwd() / path

        env_path = os.environ.get("PYAGENT_MODEL_CONFIG")
        if env_path:
            return Path(env_path)

        cwd_config = Path.cwd() / self.DEFAULT_CONFIG_PATH
        if cwd_config.exists():
            return cwd_config

        package_root = Path(__file__).parent.parent.parent
        return package_root / self.DEFAULT_CONFIG_PATH

    def _load_config(self) -> None:
        """加载配置文件"""
        if not self._config_path.exists():
            logger.warning(f"配置文件不存在: {self._config_path}，使用默认配置")
            self._set_defaults()
            return

        try:
            with open(self._config_path, encoding="utf-8") as f:
                raw_data = yaml.safe_load(f) or {}

            self._raw_config = deep_substitute_env_vars(raw_data)
            self._parse_config()

            logger.info(f"已加载模型配置: {self._config_path}")
            if self._base_model:
                logger.info(f"基础模型: {self._base_model.name}")
            logger.info(f"已配置分级模型: {list(self._tier_models.keys())}")
            logger.info(f"已配置垂类模型: {list(self._vertical_models.keys())}")
            logger.info(f"已配置提供商: {list(self._providers.keys())}")

        except yaml.YAMLError as e:
            logger.error(f"配置文件解析错误: {e}")
            raise ConfigurationError(f"配置文件解析错误: {e}") from e
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            raise ConfigurationError(f"配置加载失败: {e}") from e

    def _parse_config(self) -> None:
        """解析配置数据"""
        models_data = self._raw_config.get("models", {})
        providers_data = self._raw_config.get("providers", {})
        routing_data = self._raw_config.get("routing", {})

        self._parse_base_model(models_data)
        self._parse_tier_models(models_data)
        self._parse_vertical_models(models_data)

        for provider_name, provider_data in providers_data.items():
            self._providers[provider_name] = ProviderConfig.from_dict(
                provider_name, provider_data
            )

        if routing_data:
            self._routing = RoutingConfig.from_dict(routing_data)

    def _parse_base_model(self, models_data: dict[str, Any]) -> None:
        """解析基础模型配置"""
        base_data = models_data.get("base")
        if base_data:
            base_data["tier"] = ModelTier.BASE
            self._base_model = ModelConfig.from_dict(base_data)
            logger.debug(f"已加载基础模型: {self._base_model.name}")

    def _parse_tier_models(self, models_data: dict[str, Any]) -> None:
        """解析分级模型配置"""
        tiers_data = models_data.get("tiers", {})
        tier_mapping = {
            "strong": ModelTier.STRONG,
            "performance": ModelTier.PERFORMANCE,
            "cost-effective": ModelTier.COST_EFFECTIVE,
        }

        for tier_name, tier in tier_mapping.items():
            if tier_name in tiers_data:
                tier_data = tiers_data[tier_name]
                tier_data["tier"] = tier
                self._tier_models[tier] = ModelConfig.from_dict(tier_data)
                logger.debug(f"已加载分级模型 {tier}: {self._tier_models[tier].name}")

    def _parse_vertical_models(self, models_data: dict[str, Any]) -> None:
        """解析垂类模型配置"""
        vertical_data = models_data.get("vertical", {})
        vertical_mapping = {
            "screen-operation": VerticalType.SCREEN_OPERATION,
            "multimodal": VerticalType.MULTIMODAL,
        }

        for vkey, vtype in vertical_mapping.items():
            if vkey in vertical_data:
                vmodel_data = vertical_data[vkey]
                vmodel_data["vertical_type"] = vtype
                self._vertical_models[vtype] = VerticalModelConfig.from_dict(vmodel_data)
                logger.debug(f"已加载垂类模型 {vtype}: {self._vertical_models[vtype].name}")

        for vkey, vmodel_data in vertical_data.items():
            if vkey not in vertical_mapping:
                vmodel_data["vertical_type"] = VerticalType.CUSTOM
                vmodel = VerticalModelConfig.from_dict(vmodel_data)
                custom_type = VerticalType(f"custom_{vkey}")
                self._vertical_models[custom_type] = vmodel
                logger.debug(f"已加载自定义垂类模型 {vkey}: {vmodel.name}")

    def _set_defaults(self) -> None:
        """设置默认配置"""
        self._base_model = ModelConfig(
            name="default-base",
            tier=ModelTier.BASE,
            provider="default",
            max_tokens=2048,
            temperature=0.7,
        )
        self._tier_models = {
            ModelTier.STRONG: ModelConfig(
                name="default-strong",
                tier=ModelTier.STRONG,
                provider="default",
                max_tokens=4096,
                temperature=0.7,
            ),
            ModelTier.PERFORMANCE: ModelConfig(
                name="default-performance",
                tier=ModelTier.PERFORMANCE,
                provider="default",
                max_tokens=2048,
                temperature=0.7,
            ),
            ModelTier.COST_EFFECTIVE: ModelConfig(
                name="default-cost-effective",
                tier=ModelTier.COST_EFFECTIVE,
                provider="default",
                max_tokens=1024,
                temperature=0.5,
            ),
        }
        self._routing = RoutingConfig()

    def get_base_model(self) -> ModelConfig:
        """获取基础模型配置

        Returns:
            基础模型配置

        Raises:
            ModelNotFoundError: 基础模型未配置
        """
        if not self._base_model:
            raise ModelNotFoundError("基础模型未配置")

        model = self._base_model
        provider = self.get_provider(model.provider)

        return self._merge_model_with_provider(model, provider)

    def get_tier_model(self, tier: ModelTier) -> ModelConfig:
        """获取指定层级的模型配置

        如果分级模型未配置，回退到基础模型

        Args:
            tier: 模型层级

        Returns:
            模型配置
        """
        if tier in self._tier_models:
            model = self._tier_models[tier]
            provider = self.get_provider(model.provider)
            return self._merge_model_with_provider(model, provider)

        logger.debug(f"分级模型 '{tier}' 未配置，使用基础模型")
        return self.get_base_model()

    def get_vertical_model(self, vertical_type: VerticalType) -> VerticalModelConfig:
        """获取指定类型的垂类模型配置

        Args:
            vertical_type: 垂类模型类型

        Returns:
            垂类模型配置

        Raises:
            ModelNotFoundError: 垂类模型未配置
        """
        if vertical_type not in self._vertical_models:
            raise ModelNotFoundError(f"垂类模型 '{vertical_type}' 未配置")

        model = self._vertical_models[vertical_type]
        provider = self.get_provider(model.provider)

        return self._merge_vertical_with_provider(model, provider)

    def get_model_for_task(self, task_type: TaskType) -> ModelConfig | VerticalModelConfig:
        """根据任务类型获取对应的模型配置

        Args:
            task_type: 任务类型

        Returns:
            模型配置（分级模型或垂类模型）
        """
        if is_vertical_task(task_type):
            vertical_type = TASK_TO_VERTICAL.get(task_type)
            if vertical_type:
                try:
                    return self.get_vertical_model(vertical_type)
                except ModelNotFoundError:
                    logger.warning(f"垂类模型 '{vertical_type}' 未配置，使用基础模型")
                    return self.get_base_model()

        tier = TASK_TO_TIER.get(task_type, ModelTier.PERFORMANCE)
        return self.get_tier_model(tier)

    def _merge_model_with_provider(
        self, model: ModelConfig, provider: ProviderConfig
    ) -> ModelConfig:
        """合并模型配置和提供商配置"""
        return ModelConfig(
            name=model.name,
            tier=model.tier,
            provider=model.provider,
            api_key=provider.api_key or model.api_key,
            base_url=provider.base_url or model.base_url,
            max_tokens=model.max_tokens,
            temperature=model.temperature,
            top_p=model.top_p,
            timeout=model.timeout,
            retry_count=model.retry_count,
            capabilities=model.capabilities,
            fallback=model.fallback,
            vertical_models=model.vertical_models,
            extra_params=model.extra_params,
        )

    def _merge_vertical_with_provider(
        self, model: VerticalModelConfig, provider: ProviderConfig
    ) -> VerticalModelConfig:
        """合并垂类模型配置和提供商配置"""
        return VerticalModelConfig(
            name=model.name,
            vertical_type=model.vertical_type,
            provider=model.provider,
            description=model.description,
            api_key=provider.api_key or model.api_key,
            base_url=provider.base_url or model.base_url,
            max_tokens=model.max_tokens,
            temperature=model.temperature,
            top_p=model.top_p,
            timeout=model.timeout,
            retry_count=model.retry_count,
            capabilities=model.capabilities,
            fallback=model.fallback,
            extra_params=model.extra_params,
        )

    def get_provider(self, provider_name: str) -> ProviderConfig:
        """获取提供商配置

        Args:
            provider_name: 提供商名称

        Returns:
            提供商配置
        """
        if provider_name not in self._providers:
            logger.debug(f"提供商 '{provider_name}' 未配置，返回空配置")
            return ProviderConfig(name=provider_name)

        return self._providers[provider_name]

    def get_routing(self) -> RoutingConfig:
        """获取路由配置

        Returns:
            路由配置
        """
        if not self._routing:
            return RoutingConfig()
        return self._routing

    def get_all_tier_models(self) -> dict[ModelTier, ModelConfig]:
        """获取所有分级模型配置

        Returns:
            模型配置字典
        """
        return self._tier_models.copy()

    def get_all_vertical_models(self) -> dict[VerticalType, VerticalModelConfig]:
        """获取所有垂类模型配置

        Returns:
            垂类模型配置字典
        """
        return self._vertical_models.copy()

    def get_all_providers(self) -> dict[str, ProviderConfig]:
        """获取所有提供商配置

        Returns:
            提供商配置字典
        """
        return self._providers.copy()

    def has_vertical_model(self, vertical_type: VerticalType) -> bool:
        """检查是否配置了指定类型的垂类模型

        Args:
            vertical_type: 垂类模型类型

        Returns:
            是否已配置
        """
        return vertical_type in self._vertical_models

    def has_tier_model(self, tier: ModelTier) -> bool:
        """检查是否配置了指定层级的分级模型

        Args:
            tier: 模型层级

        Returns:
            是否已配置
        """
        return tier in self._tier_models

    def reload(self) -> None:
        """重新加载配置"""
        self._base_model = None
        self._tier_models.clear()
        self._vertical_models.clear()
        self._providers.clear()
        self._routing = None
        self._raw_config = {}
        self._load_config()

    @property
    def config_path(self) -> Path:
        """配置文件路径"""
        return self._config_path

    def validate(self) -> list[str]:
        """验证配置

        Returns:
            错误消息列表，空列表表示验证通过
        """
        errors = []

        if not self._base_model:
            errors.append("缺少基础模型配置")

        if self._base_model:
            if not self._base_model.name:
                errors.append("基础模型缺少名称")
            if not self._base_model.provider:
                errors.append("基础模型缺少提供商")

        for tier, model in self._tier_models.items():
            if not model.name:
                errors.append(f"分级模型 '{tier}' 缺少名称")
            if not model.provider:
                errors.append(f"分级模型 '{tier}' 缺少提供商")

        for vtype, model in self._vertical_models.items():
            if not model.name:
                errors.append(f"垂类模型 '{vtype}' 缺少名称")
            if not model.provider:
                errors.append(f"垂类模型 '{vtype}' 缺少提供商")

        for provider_name, provider in self._providers.items():
            if not provider.base_url:
                errors.append(f"提供商 '{provider_name}' 缺少 base_url")
            if not provider.api_key:
                env_var = f"{provider_name.upper()}_API_KEY"
                if not os.environ.get(env_var):
                    errors.append(
                        f"提供商 '{provider_name}' 缺少 API Key (未设置 {env_var})"
                    )

        return errors


_model_config_loader: ModelConfigLoader | None = None


def get_model_config_loader(config_path: str | Path | None = None) -> ModelConfigLoader:
    """获取模型配置加载器单例

    Args:
        config_path: 配置文件路径（仅首次调用时有效）

    Returns:
        ModelConfigLoader 实例
    """
    global _model_config_loader

    if _model_config_loader is None:
        _model_config_loader = ModelConfigLoader(config_path)

    return _model_config_loader


def get_model_for_task(task_type: TaskType) -> ModelConfig | VerticalModelConfig:
    """快捷方法：根据任务类型获取模型配置

    Args:
        task_type: 任务类型

    Returns:
        模型配置
    """
    return get_model_config_loader().get_model_for_task(task_type)


def get_base_model() -> ModelConfig:
    """快捷方法：获取基础模型配置

    Returns:
        基础模型配置
    """
    return get_model_config_loader().get_base_model()


def get_tier_model(tier: ModelTier) -> ModelConfig:
    """快捷方法：获取指定层级的模型配置

    Args:
        tier: 模型层级

    Returns:
        模型配置
    """
    return get_model_config_loader().get_tier_model(tier)


def get_vertical_model(vertical_type: VerticalType) -> VerticalModelConfig:
    """快捷方法：获取指定类型的垂类模型配置

    Args:
        vertical_type: 垂类模型类型

    Returns:
        垂类模型配置
    """
    return get_model_config_loader().get_vertical_model(vertical_type)
