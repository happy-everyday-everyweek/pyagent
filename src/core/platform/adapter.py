"""
平台适配器

为不同平台提供统一的接口适配。
"""

import logging
from collections.abc import Callable
from typing import Any, Optional

from src.core.platform.detector import PlatformDetector, PlatformType
from src.core.platform.routes import get_mobile_routes
from src.core.platform.types import PlatformCapabilities, PlatformConfig, ToolCategory

logger = logging.getLogger(__name__)


class PlatformAdapter:
    """平台适配器"""

    _instance: Optional["PlatformAdapter"] = None

    def __new__(cls) -> "PlatformAdapter":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, config: PlatformConfig | None = None):
        if self.initialized:
            return

        self._config = config or PlatformConfig()
        self._detector = PlatformDetector()
        self._platform_type = self._detector.platform_type
        self._capabilities = self._detector.capabilities
        self._tool_filters: dict[ToolCategory, Callable] = {}
        self._route_overrides: dict[str, Callable] = {}
        self.initialized = True

    @property
    def platform_type(self) -> PlatformType:
        return self._platform_type

    @property
    def capabilities(self) -> PlatformCapabilities:
        return self._capabilities

    @property
    def config(self) -> PlatformConfig:
        return self._config

    def is_mobile(self) -> bool:
        return self._detector.is_mobile()

    def is_android(self) -> bool:
        return self._detector.is_android()

    def is_ios(self) -> bool:
        return self._detector.is_ios()

    def is_web(self) -> bool:
        return self._detector.is_web()

    def is_desktop(self) -> bool:
        return self._detector.is_desktop()

    def get_supported_tool_categories(self) -> list[ToolCategory]:
        return self._capabilities.supported_tool_categories

    def is_tool_supported(self, tool_category: ToolCategory) -> bool:
        return self._capabilities.supports_tool_category(tool_category)

    def register_tool_filter(self, category: ToolCategory, filter_func: Callable) -> None:
        self._tool_filters[category] = filter_func

    def filter_tools(self, tools: list[Any], category: ToolCategory) -> list[Any]:
        if not self.is_tool_supported(category):
            return []

        if category in self._tool_filters:
            return self._tool_filters[category](tools)

        return tools

    def register_route_override(self, route_path: str, handler: Callable) -> None:
        self._route_overrides[route_path] = handler

    def get_route_handler(self, route_path: str) -> Callable | None:
        return self._route_overrides.get(route_path)

    def get_platform_specific_routes(self) -> list[tuple[str, str, Callable]]:
        routes = []

        if self.is_android() or self.is_ios():
            routes.extend(get_mobile_routes())

        return routes

    def get_status_info(self) -> dict[str, Any]:
        return {
            "platform_type": self._platform_type.value,
            "is_mobile": self.is_mobile(),
            "capabilities": self._capabilities.to_dict(),
            "config": self._config.to_dict(),
        }

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None


def get_platform_adapter(config: PlatformConfig | None = None) -> PlatformAdapter:
    _ = config
    return PlatformAdapter()
