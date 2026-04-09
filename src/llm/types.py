"""
PyAgent LLM 类型定义

定义四层模型架构的类型系统：
- ModelTier: 模型层级枚举
- VerticalType: 垂类模型类型枚举
- TaskType: 任务类型枚举
- ModelConfig: 模型配置数据类
- VerticalModelConfig: 垂类模型配置数据类
- LLMResponse: LLM响应数据类
- Message: 消息数据类
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Optional


class ModelTier(StrEnum):
    """模型层级枚举

    四层模型架构：
    - BASE: 基础模型，用于最基础的任务
    - STRONG: 强力模型，用于复杂规划、推理、代码生成
    - PERFORMANCE: 性能模型，用于通用任务、工具调用、回复生成
    - COST_EFFECTIVE: 经济模型，用于记忆处理、意图检测、简单任务
    """

    BASE = "base"
    STRONG = "strong"
    PERFORMANCE = "performance"
    COST_EFFECTIVE = "cost_effective"


class VerticalType(StrEnum):
    """垂类模型类型枚举

    专用垂类模型类型：
    - SCREEN_OPERATION: 屏幕操作模型，用于GUI操作、屏幕理解
    - MULTIMODAL: 多模态模型，用于图像理解、视觉任务
    - CUSTOM: 自定义垂类模型
    """

    SCREEN_OPERATION = "screen_operation"
    MULTIMODAL = "multimodal"
    CUSTOM = "custom"


class TaskType(StrEnum):
    """任务类型枚举

    不同任务类型对应不同的模型层级或垂类模型：
    - PLANNING: 规划任务 -> STRONG
    - GENERAL: 通用任务 -> PERFORMANCE
    - MEMORY: 记忆任务 -> COST_EFFECTIVE
    - INTENT: 意图检测 -> COST_EFFECTIVE
    - TOOL_USE: 工具调用 -> PERFORMANCE
    - REPLY: 回复生成 -> PERFORMANCE
    - BROWSER: 浏览器任务 -> COST_EFFECTIVE
    - SCREEN_OPERATION: 屏幕操作 -> 垂类模型
    - MULTIMODAL: 多模态任务 -> 垂类模型
    """

    PLANNING = "planning"
    GENERAL = "general"
    MEMORY = "memory"
    INTENT = "intent"
    TOOL_USE = "tool_use"
    REPLY = "reply"
    BROWSER = "browser"
    SCREEN_OPERATION = "screen_operation"
    MULTIMODAL = "multimodal"


TASK_TO_TIER: dict[TaskType, ModelTier] = {
    TaskType.PLANNING: ModelTier.STRONG,
    TaskType.GENERAL: ModelTier.PERFORMANCE,
    TaskType.MEMORY: ModelTier.COST_EFFECTIVE,
    TaskType.INTENT: ModelTier.COST_EFFECTIVE,
    TaskType.TOOL_USE: ModelTier.PERFORMANCE,
    TaskType.REPLY: ModelTier.PERFORMANCE,
    TaskType.BROWSER: ModelTier.COST_EFFECTIVE,
}

TASK_TO_VERTICAL: dict[TaskType, VerticalType] = {
    TaskType.SCREEN_OPERATION: VerticalType.SCREEN_OPERATION,
    TaskType.MULTIMODAL: VerticalType.MULTIMODAL,
}


def get_model_for_task(task_type: TaskType) -> ModelTier | VerticalType:
    """根据任务类型获取对应的模型层级或垂类模型类型
    
    Args:
        task_type: 任务类型
        
    Returns:
        模型层级或垂类模型类型
    """
    if task_type in TASK_TO_TIER:
        return TASK_TO_TIER[task_type]
    if task_type in TASK_TO_VERTICAL:
        return TASK_TO_VERTICAL[task_type]
    return ModelTier.PERFORMANCE


def is_vertical_task(task_type: TaskType) -> bool:
    """判断任务是否需要使用垂类模型
    
    Args:
        task_type: 任务类型
        
    Returns:
        是否为垂类任务
    """
    return task_type in TASK_TO_VERTICAL


class MessageRole(StrEnum):
    """消息角色枚举"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class Usage:
    """Token使用统计"""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.input_tokens + self.output_tokens


@dataclass
class VerticalModelConfig:
    """垂类模型配置数据类

    存储垂类模型的完整配置信息，包含使用场景描述
    """

    name: str
    vertical_type: VerticalType
    provider: str
    description: str = ""
    api_key: str = ""
    base_url: str = ""
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    timeout: int = 60
    retry_count: int = 3
    capabilities: list[str] = field(default_factory=list)
    fallback: Optional["VerticalModelConfig"] = None
    extra_params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.capabilities:
            self.capabilities = ["text"]
        if isinstance(self.vertical_type, str):
            self.vertical_type = VerticalType(self.vertical_type)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = {
            "name": self.name,
            "vertical_type": self.vertical_type.value,
            "provider": self.provider,
            "description": self.description,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "capabilities": self.capabilities,
        }
        if self.api_key:
            result["api_key"] = self.api_key
        if self.base_url:
            result["base_url"] = self.base_url
        if self.fallback:
            result["fallback"] = self.fallback.to_dict()
        if self.extra_params:
            result["extra_params"] = self.extra_params
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VerticalModelConfig":
        """从字典创建"""
        fallback_data = data.get("fallback")
        fallback = None
        if fallback_data and isinstance(fallback_data, dict):
            fallback = cls.from_dict(fallback_data)

        vertical_type = data.get("vertical_type", "custom")
        if isinstance(vertical_type, str):
            vertical_type = VerticalType(vertical_type)

        return cls(
            name=data.get("name", ""),
            vertical_type=vertical_type,
            provider=data.get("provider", ""),
            description=data.get("description", ""),
            api_key=data.get("api_key", ""),
            base_url=data.get("base_url", ""),
            max_tokens=data.get("max_tokens", 2048),
            temperature=data.get("temperature", 0.7),
            top_p=data.get("top_p", 0.9),
            timeout=data.get("timeout", 60),
            retry_count=data.get("retry_count", 3),
            capabilities=data.get("capabilities", ["text"]),
            fallback=fallback,
            extra_params=data.get("extra_params", {}),
        )

    def has_capability(self, capability: str) -> bool:
        """检查是否具有指定能力"""
        return capability.lower() in [c.lower() for c in self.capabilities]


@dataclass
class ModelConfig:
    """模型配置数据类

    存储分级模型的完整配置信息，支持关联垂类模型
    """

    name: str
    tier: ModelTier
    provider: str
    api_key: str = ""
    base_url: str = ""
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    timeout: int = 60
    retry_count: int = 3
    capabilities: list[str] = field(default_factory=list)
    fallback: Optional["ModelConfig"] = None
    vertical_models: dict[VerticalType, VerticalModelConfig] = field(default_factory=dict)
    extra_params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.capabilities:
            self.capabilities = ["text"]
        if isinstance(self.tier, str):
            self.tier = ModelTier(self.tier)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = {
            "name": self.name,
            "tier": self.tier.value,
            "provider": self.provider,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "capabilities": self.capabilities,
        }
        if self.api_key:
            result["api_key"] = self.api_key
        if self.base_url:
            result["base_url"] = self.base_url
        if self.fallback:
            result["fallback"] = self.fallback.to_dict()
        if self.vertical_models:
            result["vertical_models"] = {
                vt.value: vm.to_dict() for vt, vm in self.vertical_models.items()
            }
        if self.extra_params:
            result["extra_params"] = self.extra_params
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelConfig":
        """从字典创建"""
        fallback_data = data.get("fallback")
        fallback = None
        if fallback_data and isinstance(fallback_data, dict):
            fallback = cls.from_dict(fallback_data)

        tier = data.get("tier", "performance")
        if isinstance(tier, str):
            tier = ModelTier(tier)

        vertical_models = {}
        vertical_data = data.get("vertical_models", {})
        for vt_str, vm_data in vertical_data.items():
            if isinstance(vm_data, dict):
                vt = VerticalType(vt_str) if isinstance(vt_str, str) else vt_str
                vertical_models[vt] = VerticalModelConfig.from_dict(vm_data)

        return cls(
            name=data.get("name", ""),
            tier=tier,
            provider=data.get("provider", ""),
            api_key=data.get("api_key", ""),
            base_url=data.get("base_url", ""),
            max_tokens=data.get("max_tokens", 2048),
            temperature=data.get("temperature", 0.7),
            top_p=data.get("top_p", 0.9),
            timeout=data.get("timeout", 60),
            retry_count=data.get("retry_count", 3),
            capabilities=data.get("capabilities", ["text"]),
            fallback=fallback,
            vertical_models=vertical_models,
            extra_params=data.get("extra_params", {}),
        )

    def has_capability(self, capability: str) -> bool:
        """检查是否具有指定能力"""
        return capability.lower() in [c.lower() for c in self.capabilities]

    def get_vertical_model(self, vertical_type: VerticalType) -> VerticalModelConfig | None:
        """获取指定类型的垂类模型配置
        
        Args:
            vertical_type: 垂类模型类型
            
        Returns:
            垂类模型配置，如果不存在则返回None
        """
        return self.vertical_models.get(vertical_type)


@dataclass
class ProviderConfig:
    """API提供商配置"""

    name: str
    base_url: str = ""
    api_key: str = ""
    default_headers: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = {"base_url": self.base_url}
        if self.api_key:
            result["api_key"] = self.api_key
        if self.default_headers:
            result["default_headers"] = self.default_headers
        return result

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "ProviderConfig":
        return cls(
            name=name,
            base_url=data.get("base_url", ""),
            api_key=data.get("api_key", ""),
            default_headers=data.get("default_headers", {}),
        )


@dataclass
class RoutingRule:
    """路由规则"""

    pattern: str
    model: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RoutingRule":
        return cls(
            pattern=data.get("pattern", ""),
            model=data.get("model", "performance"),
        )


@dataclass
class RoutingConfig:
    """路由配置"""

    rules: list[RoutingRule] = field(default_factory=list)
    default_model: str = "performance"
    intent_detection_enabled: bool = True
    intent_detection_model: str = "cost_effective"
    confidence_threshold: float = 0.7

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RoutingConfig":
        rules = [RoutingRule.from_dict(r) for r in data.get("rules", [])]
        intent_config = data.get("intent_detection", {})
        return cls(
            rules=rules,
            default_model=data.get("default_model", "performance"),
            intent_detection_enabled=intent_config.get("enabled", True),
            intent_detection_model=intent_config.get("model", "cost_effective"),
            confidence_threshold=intent_config.get("confidence_threshold", 0.7),
        )


@dataclass
class Message:
    """消息数据类

    表示对话中的一条消息
    """

    role: MessageRole | str
    content: str
    name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        result = {
            "role": self.role.value if isinstance(self.role, MessageRole) else self.role,
            "content": self.content,
        }
        if self.name:
            result["name"] = self.name
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """从字典创建"""
        role = data.get("role", "user")
        if isinstance(role, str):
            try:
                role = MessageRole(role)
            except ValueError:
                pass
        return cls(
            role=role,
            content=data.get("content", ""),
            name=data.get("name"),
        )

    @classmethod
    def user(cls, content: str, name: str | None = None) -> "Message":
        """创建用户消息"""
        return cls(role=MessageRole.USER, content=content, name=name)

    @classmethod
    def assistant(cls, content: str, name: str | None = None) -> "Message":
        """创建助手消息"""
        return cls(role=MessageRole.ASSISTANT, content=content, name=name)

    @classmethod
    def system(cls, content: str) -> "Message":
        """创建系统消息"""
        return cls(role=MessageRole.SYSTEM, content=content)


@dataclass
class ToolCall:
    """工具调用"""

    id: str
    name: str
    arguments: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": self.arguments,
            },
        }


@dataclass
class LLMResponse:
    """LLM响应数据类

    表示LLM的响应结果
    """

    content: str
    reasoning: str = ""
    usage: Usage = field(default_factory=Usage)
    model: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    raw_response: dict[str, Any] = field(default_factory=dict)

    @property
    def has_tool_calls(self) -> bool:
        """是否有工具调用"""
        return len(self.tool_calls) > 0

    @property
    def total_tokens(self) -> int:
        """总token数"""
        return self.usage.total_tokens

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = {
            "content": self.content,
            "model": self.model,
            "finish_reason": self.finish_reason,
            "usage": {
                "input_tokens": self.usage.input_tokens,
                "output_tokens": self.usage.output_tokens,
                "total_tokens": self.usage.total_tokens,
            },
        }
        if self.reasoning:
            result["reasoning"] = self.reasoning
        if self.tool_calls:
            result["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LLMResponse":
        """从字典创建"""
        usage_data = data.get("usage", {})
        usage = Usage(
            input_tokens=usage_data.get("input_tokens", 0),
            output_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        tool_calls = []
        for tc in data.get("tool_calls", []):
            if isinstance(tc, dict):
                func = tc.get("function", {})
                tool_calls.append(
                    ToolCall(
                        id=tc.get("id", ""),
                        name=func.get("name", ""),
                        arguments=func.get("arguments", {}),
                    )
                )

        return cls(
            content=data.get("content", ""),
            reasoning=data.get("reasoning", ""),
            usage=usage,
            model=data.get("model", ""),
            tool_calls=tool_calls,
            finish_reason=data.get("finish_reason", "stop"),
            raw_response=data.get("raw_response", {}),
        )


class LLMError(Exception):
    """LLM相关错误基类"""



class ConfigurationError(LLMError):
    """配置错误"""



class ModelNotFoundError(LLMError):
    """模型未找到错误"""



class ProviderNotFoundError(LLMError):
    """提供商未找到错误"""

