"""
平台类型定义

定义平台能力、配置等数据结构。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PlatformType(Enum):
    """平台类型"""
    WEB = "web"
    MOBILE_ANDROID = "mobile_android"
    MOBILE_IOS = "mobile_ios"
    DESKTOP = "desktop"
    UNKNOWN = "unknown"


class ToolCategory(Enum):
    """工具类别"""
    CORE = "core"
    FILE = "file"
    WEB = "web"
    SHELL = "shell"
    SCREEN = "screen"
    NOTIFICATION = "notification"
    SMS = "sms"
    CAMERA = "camera"
    GPS = "gps"
    BLUETOOTH = "bluetooth"
    NFC = "nfc"


@dataclass
class PlatformCapabilities:
    """平台能力"""
    platform_type: PlatformType = PlatformType.UNKNOWN
    has_screen: bool = True
    has_camera: bool = True
    has_gps: bool = True
    has_bluetooth: bool = True
    has_nfc: bool = False
    has_telephony: bool = True
    has_file_system: bool = True
    has_shell: bool = True
    has_web_access: bool = True
    screen_width: int = 1920
    screen_height: int = 1080
    screen_dpi: int = 96
    supported_tool_categories: list[ToolCategory] = field(
        default_factory=lambda: list(ToolCategory)
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform_type": self.platform_type.value,
            "has_screen": self.has_screen,
            "has_camera": self.has_camera,
            "has_gps": self.has_gps,
            "has_bluetooth": self.has_bluetooth,
            "has_nfc": self.has_nfc,
            "has_telephony": self.has_telephony,
            "has_file_system": self.has_file_system,
            "has_shell": self.has_shell,
            "has_web_access": self.has_web_access,
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "screen_dpi": self.screen_dpi,
            "supported_tool_categories": [c.value for c in self.supported_tool_categories],
        }

    def supports_tool_category(self, category: ToolCategory) -> bool:
        return category in self.supported_tool_categories


@dataclass
class PlatformConfig:
    """平台配置"""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    enable_cors: bool = True
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    debug: bool = False
    log_level: str = "info"
    data_dir: str = "data"
    config_dir: str = "config"
    enable_hot_reload: bool = False
    enable_screen_tools: bool = True
    enable_notification: bool = True
    enable_sms: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_host": self.api_host,
            "api_port": self.api_port,
            "enable_cors": self.enable_cors,
            "cors_origins": self.cors_origins,
            "debug": self.debug,
            "log_level": self.log_level,
            "data_dir": self.data_dir,
            "config_dir": self.config_dir,
            "enable_hot_reload": self.enable_hot_reload,
            "enable_screen_tools": self.enable_screen_tools,
            "enable_notification": self.enable_notification,
            "enable_sms": self.enable_sms,
        }


WEB_CAPABILITIES = PlatformCapabilities(
    platform_type=PlatformType.WEB,
    has_screen=True,
    has_camera=False,
    has_gps=False,
    has_bluetooth=False,
    has_nfc=False,
    has_telephony=False,
    has_file_system=True,
    has_shell=True,
    has_web_access=True,
    screen_width=1920,
    screen_height=1080,
    screen_dpi=96,
    supported_tool_categories=[
        ToolCategory.CORE,
        ToolCategory.FILE,
        ToolCategory.WEB,
        ToolCategory.SHELL,
    ],
)

ANDROID_CAPABILITIES = PlatformCapabilities(
    platform_type=PlatformType.MOBILE_ANDROID,
    has_screen=True,
    has_camera=True,
    has_gps=True,
    has_bluetooth=True,
    has_nfc=True,
    has_telephony=True,
    has_file_system=True,
    has_shell=True,
    has_web_access=True,
    screen_width=1080,
    screen_height=1920,
    screen_dpi=480,
    supported_tool_categories=[
        ToolCategory.CORE,
        ToolCategory.FILE,
        ToolCategory.WEB,
        ToolCategory.SHELL,
        ToolCategory.SCREEN,
        ToolCategory.NOTIFICATION,
        ToolCategory.SMS,
        ToolCategory.CAMERA,
        ToolCategory.GPS,
        ToolCategory.BLUETOOTH,
        ToolCategory.NFC,
    ],
)

IOS_CAPABILITIES = PlatformCapabilities(
    platform_type=PlatformType.MOBILE_IOS,
    has_screen=True,
    has_camera=True,
    has_gps=True,
    has_bluetooth=True,
    has_nfc=True,
    has_telephony=True,
    has_file_system=False,
    has_shell=False,
    has_web_access=True,
    screen_width=1170,
    screen_height=2532,
    screen_dpi=460,
    supported_tool_categories=[
        ToolCategory.CORE,
        ToolCategory.WEB,
        ToolCategory.SCREEN,
        ToolCategory.NOTIFICATION,
        ToolCategory.CAMERA,
        ToolCategory.GPS,
        ToolCategory.BLUETOOTH,
        ToolCategory.NFC,
    ],
)

DESKTOP_CAPABILITIES = PlatformCapabilities(
    platform_type=PlatformType.DESKTOP,
    has_screen=True,
    has_camera=True,
    has_gps=False,
    has_bluetooth=True,
    has_nfc=False,
    has_telephony=False,
    has_file_system=True,
    has_shell=True,
    has_web_access=True,
    screen_width=1920,
    screen_height=1080,
    screen_dpi=96,
    supported_tool_categories=[
        ToolCategory.CORE,
        ToolCategory.FILE,
        ToolCategory.WEB,
        ToolCategory.SHELL,
        ToolCategory.CAMERA,
        ToolCategory.BLUETOOTH,
    ],
)
