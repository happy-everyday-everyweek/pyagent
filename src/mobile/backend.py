"""
PyAgent 移动端模块 - 移动端后端

初始化和管理移动端后端服务，提供移动设备特定的API路由。
v0.8.0: 新增移动端支持
"""

import logging
import os
import platform
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from src.mobile.linux_env import LinuxEnv, ServiceConfig


class BackendMode(Enum):
    """后端模式"""
    STANDALONE = "standalone"
    EMBEDDED = "embedded"
    CLIENT = "client"


class BackendStatus(Enum):
    """后端状态"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class MobileCapabilities:
    """移动设备能力"""
    has_screen: bool = True
    has_camera: bool = True
    has_gps: bool = True
    has_bluetooth: bool = True
    has_nfc: bool = False
    has_telephony: bool = True
    screen_width: int = 1080
    screen_height: int = 1920
    screen_dpi: int = 480

    def to_dict(self) -> dict[str, Any]:
        return {
            "has_screen": self.has_screen,
            "has_camera": self.has_camera,
            "has_gps": self.has_gps,
            "has_bluetooth": self.has_bluetooth,
            "has_nfc": self.has_nfc,
            "has_telephony": self.has_telephony,
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "screen_dpi": self.screen_dpi,
        }


@dataclass
class MobileConfig:
    """移动端配置"""
    mode: BackendMode = BackendMode.STANDALONE
    api_host: str = "127.0.0.1"
    api_port: int = 8080
    enable_screen_tools: bool = True
    enable_notification: bool = True
    enable_sms: bool = True
    data_dir: str = "data/mobile"
    log_level: str = "info"
    auto_start: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "enable_screen_tools": self.enable_screen_tools,
            "enable_notification": self.enable_notification,
            "enable_sms": self.enable_sms,
            "data_dir": self.data_dir,
            "log_level": self.log_level,
            "auto_start": self.auto_start,
        }


class MobileBackend:
    """移动端后端管理器

    负责初始化和管理移动端后端服务，检测移动设备环境，
    并提供移动设备特定的API路由。
    """

    _instance: "MobileBackend | None" = None

    def __new__(cls, config: MobileConfig | None = None) -> "MobileBackend":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: MobileConfig | None = None):
        if self._initialized:
            return

        self._config = config or MobileConfig()
        self._status = BackendStatus.UNINITIALIZED
        self._linux_env: LinuxEnv | None = None
        self._capabilities: MobileCapabilities | None = None
        self._is_mobile: bool = False
        self._app = None
        self._routes: list[tuple[str, str, Callable]] = []
        self._logger = logging.getLogger(__name__)
        self._initialized = True

    @property
    def status(self) -> BackendStatus:
        return self._status

    @property
    def config(self) -> MobileConfig:
        return self._config

    @property
    def capabilities(self) -> MobileCapabilities | None:
        return self._capabilities

    @property
    def is_mobile(self) -> bool:
        return self._is_mobile

    @property
    def api_endpoint(self) -> str:
        if self._linux_env:
            return self._linux_env.api_endpoint
        return f"http://{self._config.api_host}:{self._config.api_port}"

    @classmethod
    def detect_mobile(cls) -> bool:
        """检测是否运行在移动设备上"""
        system = platform.system().lower()
        machine = platform.machine().lower()

        if system == "linux":
            if "android" in platform.platform().lower():
                return True

            if "arm" in machine or "aarch" in machine:
                if os.path.exists("/system/bin") or os.path.exists("/vendor/bin"):
                    return True

                if os.path.exists("/data/data"):
                    return True

        return False

    def detect_capabilities(self) -> MobileCapabilities:
        """检测移动设备能力"""
        capabilities = MobileCapabilities()

        try:
            if os.path.exists("/sys/class/graphics/fb0"):
                with open("/sys/class/graphics/fb0/virtual_size", encoding="utf-8") as f:
                    size = f.read().strip().split(",")
                    if len(size) == 2:
                        capabilities.screen_width = int(size[0])
                        capabilities.screen_height = int(size[1])
        except Exception:
            pass

        try:
            if os.path.exists("/proc/device-tree/firmware/android"):
                capabilities.has_nfc = os.path.exists("/proc/device-tree/firmware/android/nfc")
        except Exception:
            pass

        capabilities.has_camera = os.path.exists("/dev/video0") or os.path.exists("/dev/video1")
        capabilities.has_gps = os.path.exists("/dev/ttyGPS0") or os.path.exists("/dev/gps")
        capabilities.has_bluetooth = os.path.exists("/dev/ttyBT0") or os.path.exists("/sys/class/bluetooth")
        capabilities.has_telephony = os.path.exists("/dev/ttyUSB0") or os.path.exists("/dev/radio")

        return capabilities

    def initialize(self) -> bool:
        """初始化移动端后端"""
        if self._status == BackendStatus.READY:
            return True

        self._status = BackendStatus.INITIALIZING
        self._logger.info("Initializing mobile backend...")

        try:
            self._is_mobile = self.detect_mobile()
            self._logger.info(f"Running on mobile: {self._is_mobile}")

            self._capabilities = self.detect_capabilities()
            self._logger.info(f"Capabilities: {self._capabilities.to_dict()}")

            data_dir = Path(self._config.data_dir)
            data_dir.mkdir(parents=True, exist_ok=True)

            if self._is_mobile or self._config.mode == BackendMode.EMBEDDED:
                service_config = ServiceConfig(
                    host=self._config.api_host,
                    port=self._config.api_port,
                )
                self._linux_env = LinuxEnv(config=service_config)

                if not self._linux_env.initialize():
                    self._logger.error("Failed to initialize Linux environment")
                    self._status = BackendStatus.ERROR
                    return False

            self._setup_routes()

            self._status = BackendStatus.READY
            self._logger.info("Mobile backend initialized successfully")
            return True

        except Exception as e:
            self._logger.error(f"Failed to initialize mobile backend: {e}")
            self._status = BackendStatus.ERROR
            return False

    def _setup_routes(self) -> None:
        """设置移动端特定路由"""
        self._routes = [
            ("/api/mobile/status", "GET", self._handle_status),
            ("/api/mobile/capabilities", "GET", self._handle_capabilities),
            ("/api/mobile/screen/capture", "POST", self._handle_screen_capture),
            ("/api/mobile/screen/tap", "POST", self._handle_screen_tap),
            ("/api/mobile/screen/swipe", "POST", self._handle_screen_swipe),
            ("/api/mobile/notifications", "GET", self._handle_get_notifications),
            ("/api/mobile/sms", "GET", self._handle_get_sms),
            ("/api/mobile/sms/send", "POST", self._handle_send_sms),
        ]

    async def _handle_status(self) -> dict[str, Any]:
        """处理状态请求"""
        return {
            "status": self._status.value,
            "is_mobile": self._is_mobile,
            "api_endpoint": self.api_endpoint,
            "config": self._config.to_dict(),
        }

    async def _handle_capabilities(self) -> dict[str, Any]:
        """处理能力请求"""
        if self._capabilities:
            return self._capabilities.to_dict()
        return {}

    async def _handle_screen_capture(self) -> dict[str, Any]:
        """处理屏幕截图请求"""
        if not self._config.enable_screen_tools:
            return {"success": False, "error": "Screen tools disabled"}

        from src.mobile.screen_tools import ScreenTools
        tools = ScreenTools()
        result = await tools.capture_screen()
        return result.to_dict()

    async def _handle_screen_tap(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理屏幕点击请求"""
        if not self._config.enable_screen_tools:
            return {"success": False, "error": "Screen tools disabled"}

        from src.mobile.screen_tools import ScreenTools
        tools = ScreenTools()
        x = data.get("x", 0)
        y = data.get("y", 0)
        result = await tools.tap(x, y)
        return result.to_dict()

    async def _handle_screen_swipe(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理屏幕滑动请求"""
        if not self._config.enable_screen_tools:
            return {"success": False, "error": "Screen tools disabled"}

        from src.mobile.screen_tools import ScreenTools
        tools = ScreenTools()
        x1 = data.get("x1", 0)
        y1 = data.get("y1", 0)
        x2 = data.get("x2", 0)
        y2 = data.get("y2", 0)
        result = await tools.swipe(x1, y1, x2, y2)
        return result.to_dict()

    async def _handle_get_notifications(self) -> dict[str, Any]:
        """处理获取通知请求"""
        if not self._config.enable_notification:
            return {"success": False, "error": "Notification disabled"}

        from src.mobile.notification import NotificationReader
        reader = NotificationReader()
        notifications = await reader.get_notifications()
        return {"success": True, "notifications": notifications}

    async def _handle_get_sms(self) -> dict[str, Any]:
        """处理获取短信请求"""
        if not self._config.enable_sms:
            return {"success": False, "error": "SMS disabled"}

        from src.mobile.sms import SMSTools
        tools = SMSTools()
        messages = await tools.get_messages()
        return {"success": True, "messages": messages}

    async def _handle_send_sms(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理发送短信请求"""
        if not self._config.enable_sms:
            return {"success": False, "error": "SMS disabled"}

        from src.mobile.sms import SMSTools
        tools = SMSTools()
        to = data.get("to", "")
        body = data.get("body", "")
        result = await tools.send_message(to, body)
        return result.to_dict()

    def get_routes(self) -> list[tuple[str, str, Callable]]:
        """获取移动端路由列表"""
        return self._routes

    def start(self) -> bool:
        """启动移动端后端"""
        if self._status == BackendStatus.RUNNING:
            return True

        if self._status != BackendStatus.READY:
            if not self.initialize():
                return False

        try:
            if self._linux_env:
                if not self._linux_env.start_service():
                    self._logger.error("Failed to start Linux service")
                    self._status = BackendStatus.ERROR
                    return False

            self._status = BackendStatus.RUNNING
            self._logger.info(f"Mobile backend started on {self.api_endpoint}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to start mobile backend: {e}")
            self._status = BackendStatus.ERROR
            return False

    def stop(self) -> bool:
        """停止移动端后端"""
        if self._status != BackendStatus.RUNNING:
            return True

        try:
            if self._linux_env:
                self._linux_env.stop_service()

            self._status = BackendStatus.STOPPED
            self._logger.info("Mobile backend stopped")
            return True

        except Exception as e:
            self._logger.error(f"Failed to stop mobile backend: {e}")
            return False

    def get_status_info(self) -> dict[str, Any]:
        """获取状态信息"""
        return {
            "status": self._status.value,
            "is_mobile": self._is_mobile,
            "api_endpoint": self.api_endpoint,
            "config": self._config.to_dict(),
            "capabilities": self._capabilities.to_dict() if self._capabilities else None,
            "linux_env": self._linux_env.get_status_info() if self._linux_env else None,
        }

    async def health_check(self) -> bool:
        """健康检查"""
        if self._linux_env:
            return await self._linux_env.health_check()
        return self._status == BackendStatus.RUNNING

    def cleanup(self) -> None:
        """清理资源"""
        self.stop()
        if self._linux_env:
            self._linux_env.cleanup()
        self._status = BackendStatus.UNINITIALIZED

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例实例（仅用于测试）"""
        cls._instance = None


mobile_backend = MobileBackend()
