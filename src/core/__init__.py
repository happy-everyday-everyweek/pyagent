"""
PyAgent 核心模块

提供核心功能和基础类，支持Web端和移动端统一后端。
"""

from src.core.app_factory import (
    ChatRequest,
    ChatResponse,
    ConnectionManager,
    create_app,
    get_chat_agent,
    get_collaboration_manager,
    get_executor_agent,
    get_tool_registry,
    set_chat_agent,
    set_collaboration_manager,
    set_executor_agent,
    set_tool_registry,
)
from src.core.platform import (
    PlatformAdapter,
    PlatformCapabilities,
    PlatformConfig,
    PlatformDetector,
    PlatformType,
    detect_platform,
    get_platform_adapter,
)

__all__ = [
    "ChatRequest",
    "ChatResponse",
    "ConnectionManager",
    "CoreContext",
    "PlatformAdapter",
    "PlatformCapabilities",
    "PlatformConfig",
    "PlatformDetector",
    "PlatformType",
    "core_context",
    "create_app",
    "detect_platform",
    "get_chat_agent",
    "get_collaboration_manager",
    "get_executor_agent",
    "get_platform_adapter",
    "get_tool_registry",
    "set_chat_agent",
    "set_collaboration_manager",
    "set_executor_agent",
    "set_tool_registry",
]

from src.core import CoreContext, core_context
