"""
PyAgent 平台适配模块

提供平台检测和适配功能,支持Web端和移动端统一后端。
"""

from src.core.platform.adapter import PlatformAdapter, get_platform_adapter
from src.core.platform.detector import PlatformDetector, PlatformType, detect_platform
from src.core.platform.types import PlatformCapabilities, PlatformConfig

__all__ = [
    "PlatformAdapter",
    "PlatformCapabilities",
    "PlatformConfig",
    "PlatformDetector",
    "PlatformType",
    "detect_platform",
    "get_platform_adapter",
]
