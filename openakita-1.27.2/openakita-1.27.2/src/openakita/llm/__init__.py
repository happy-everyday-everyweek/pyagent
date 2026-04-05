"""
LLM 统一调用层

提供统一的 LLM 调用接口，支持：
- Anthropic 和 OpenAI 两种 API 格式
- 多模态（图片、视频）
- 工具调用
- 思考模式 (thinking)
- 自动故障切换
- 能力分流
"""

from .adapter import LegacyContext, LegacyResponse, LLMAdapter, think
from .client import LLMClient, chat, get_default_client
from .config import get_default_config_path, load_endpoints_config
from .types import (
    ContentBlock,
    EndpointConfig,
    ImageContent,
    LLMRequest,
    LLMResponse,
    Message,
    StopReason,
    TextBlock,
    Tool,
    ToolResultBlock,
    ToolUseBlock,
    Usage,
    VideoContent,
)

__all__ = [
    # Types
    "LLMRequest",
    "LLMResponse",
    "EndpointConfig",
    "ContentBlock",
    "TextBlock",
    "ToolUseBlock",
    "ToolResultBlock",
    "ImageContent",
    "VideoContent",
    "Message",
    "Tool",
    "Usage",
    "StopReason",
    # Client
    "LLMClient",
    "get_default_client",
    "chat",
    # Config
    "load_endpoints_config",
    "get_default_config_path",
    # Adapter (backward compatibility)
    "LLMAdapter",
    "LegacyResponse",
    "LegacyContext",
    "think",
]
