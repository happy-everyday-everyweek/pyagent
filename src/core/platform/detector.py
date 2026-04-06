"""
平台检测器

自动检测运行平台类型和能力。
"""

import logging
import platform
import sys
from pathlib import Path
from typing import Optional

from src.core.platform.types import (
    ANDROID_CAPABILITIES,
    DESKTOP_CAPABILITIES,
    IOS_CAPABILITIES,
    WEB_CAPABILITIES,
    PlatformCapabilities,
    PlatformType,
)

logger = logging.getLogger(__name__)


class PlatformDetector:
    """平台检测器"""

    _instance: Optional["PlatformDetector"] = None
    _platform_type: PlatformType | None = None
    _capabilities: PlatformCapabilities | None = None

    def __new__(cls) -> "PlatformDetector":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        self.initialized = True
        self._detect()

    def _detect(self) -> None:
        self._platform_type = self._detect_platform_type()
        self._capabilities = self._detect_capabilities()
        logger.info("Detected platform: %s", self._platform_type.value)

    def _detect_platform_type(self) -> PlatformType:
        if self._is_android():
            return PlatformType.MOBILE_ANDROID

        if self._is_ios():
            return PlatformType.MOBILE_IOS

        if self._is_web():
            return PlatformType.WEB

        if self._is_desktop():
            return PlatformType.DESKTOP

        return PlatformType.UNKNOWN

    def _is_android(self) -> bool:
        system = platform.system().lower()
        machine = platform.machine().lower()

        if system == "linux":
            if "android" in platform.platform().lower():
                return True

            if "arm" in machine or "aarch" in machine:
                if Path("/system/bin").exists() or Path("/vendor/bin").exists():
                    return True

                if Path("/data/data").exists():
                    return True

            if "ANDROID_ROOT" in __import__("os").environ:
                return True

            if "TERMUX_VERSION" in __import__("os").environ:
                return True

        return False

    def _is_ios(self) -> bool:
        system = platform.system().lower()
        if system == "darwin":
            if "iphone" in platform.platform().lower():
                return True

            if "ipad" in platform.platform().lower():
                return True

        return False

    def _is_web(self) -> bool:
        if "pyodide" in sys.modules:
            return True

        if "browser" in sys.modules:
            return True

        return False

    def _is_desktop(self) -> bool:
        system = platform.system().lower()
        return system in ["windows", "darwin", "linux"]

    def _detect_capabilities(self) -> PlatformCapabilities:
        if self._platform_type == PlatformType.MOBILE_ANDROID:
            return self._detect_android_capabilities()
        if self._platform_type == PlatformType.MOBILE_IOS:
            return self._detect_ios_capabilities()
        if self._platform_type == PlatformType.WEB:
            return WEB_CAPABILITIES
        if self._platform_type == PlatformType.DESKTOP:
            return self._detect_desktop_capabilities()

        return WEB_CAPABILITIES

    def _detect_android_capabilities(self) -> PlatformCapabilities:
        capabilities = ANDROID_CAPABILITIES

        try:
            fb_path = Path("/sys/class/graphics/fb0")
            if fb_path.exists():
                virtual_size_path = fb_path / "virtual_size"
                content = virtual_size_path.read_text(encoding="utf-8").strip()
                size = content.split(",")
                if len(size) == 2:
                    capabilities.screen_width = int(size[0])
                    capabilities.screen_height = int(size[1])
        except Exception:
            pass

        capabilities.has_camera = Path("/dev/video0").exists() or Path("/dev/video1").exists()
        capabilities.has_gps = Path("/dev/ttyGPS0").exists() or Path("/dev/gps").exists()
        capabilities.has_bluetooth = (
            Path("/dev/ttyBT0").exists() or Path("/sys/class/bluetooth").exists()
        )
        capabilities.has_telephony = Path("/dev/ttyUSB0").exists() or Path("/dev/radio").exists()

        return capabilities

    def _detect_ios_capabilities(self) -> PlatformCapabilities:
        return IOS_CAPABILITIES

    def _detect_desktop_capabilities(self) -> PlatformCapabilities:
        capabilities = DESKTOP_CAPABILITIES

        try:
            import tkinter as tk

            root = tk.Tk()
            capabilities.screen_width = root.winfo_screenwidth()
            capabilities.screen_height = root.winfo_screenheight()
            root.destroy()
        except Exception:
            pass

        return capabilities

    @property
    def platform_type(self) -> PlatformType:
        return self._platform_type or PlatformType.UNKNOWN

    @property
    def capabilities(self) -> PlatformCapabilities:
        return self._capabilities or WEB_CAPABILITIES

    def is_mobile(self) -> bool:
        return self._platform_type in [PlatformType.MOBILE_ANDROID, PlatformType.MOBILE_IOS]

    def is_android(self) -> bool:
        return self._platform_type == PlatformType.MOBILE_ANDROID

    def is_ios(self) -> bool:
        return self._platform_type == PlatformType.MOBILE_IOS

    def is_web(self) -> bool:
        return self._platform_type == PlatformType.WEB

    def is_desktop(self) -> bool:
        return self._platform_type == PlatformType.DESKTOP

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None


def detect_platform() -> PlatformType:
    detector = PlatformDetector()
    return detector.platform_type


def get_platform_detector() -> PlatformDetector:
    return PlatformDetector()
