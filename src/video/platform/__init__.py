from typing import Optional
from .base import PlatformCapabilities, PlatformAdapter
from .detector import PlatformDetector
from .desktop import DesktopAdapter, FileSystemAccess, FFmpegRenderer, HardwareEncoder
from .mobile import (
    MobileAdapter,
    TouchGestureHandler,
    PerformanceOptimizer,
    OfflineStorage,
    GestureType,
    DeviceTier,
    RendererConfig,
)


class DefaultAdapter(PlatformAdapter):
    def __init__(self):
        super().__init__()
        self.capabilities = self.detect_capabilities()

    def get_platform_name(self) -> str:
        return PlatformDetector.detect()

    def detect_capabilities(self) -> PlatformCapabilities:
        platform_type = PlatformDetector.detect()
        os_type = PlatformDetector.get_os()
        
        capabilities = PlatformCapabilities()
        
        if platform_type == "desktop":
            capabilities.can_hardware_encode = True
            capabilities.can_gpu_render = True
            capabilities.max_preview_fps = 60
            capabilities.max_resolution = (3840, 2160)
            capabilities.supports_touch = False
            capabilities.supports_offline = True
            capabilities.storage_type = "file"
            capabilities.renderer_type = "opengl"
        elif platform_type == "mobile":
            capabilities.can_hardware_encode = True
            capabilities.can_gpu_render = True
            capabilities.max_preview_fps = 30
            capabilities.max_resolution = (1920, 1080)
            capabilities.supports_touch = True
            capabilities.supports_offline = True
            capabilities.storage_type = "file"
            capabilities.renderer_type = "opengl"
        elif platform_type == "web":
            capabilities.can_hardware_encode = False
            capabilities.can_gpu_render = True
            capabilities.max_preview_fps = 30
            capabilities.max_resolution = (1920, 1080)
            capabilities.supports_touch = True
            capabilities.supports_offline = False
            capabilities.storage_type = "indexeddb"
            capabilities.renderer_type = "canvas"
        
        return capabilities

    def get_storage(self):
        return {
            "type": self.capabilities.storage_type,
            "platform": self.get_platform_name(),
        }

    def get_renderer_config(self) -> dict:
        return {
            "type": self.capabilities.renderer_type,
            "max_fps": self.capabilities.max_preview_fps,
            "max_resolution": self.capabilities.max_resolution,
            "gpu_enabled": self.capabilities.can_gpu_render,
        }


_adapter_instance: Optional[PlatformAdapter] = None


def get_platform_adapter() -> PlatformAdapter:
    global _adapter_instance
    
    if _adapter_instance is None:
        platform_type = PlatformDetector.detect()
        if platform_type == "mobile":
            _adapter_instance = MobileAdapter()
        elif platform_type == "desktop":
            _adapter_instance = DesktopAdapter()
        else:
            _adapter_instance = DefaultAdapter()
    
    return _adapter_instance


__all__ = [
    "PlatformCapabilities",
    "PlatformAdapter",
    "PlatformDetector",
    "get_platform_adapter",
    "DesktopAdapter",
    "FileSystemAccess",
    "FFmpegRenderer",
    "HardwareEncoder",
    "MobileAdapter",
    "TouchGestureHandler",
    "PerformanceOptimizer",
    "OfflineStorage",
    "GestureType",
    "DeviceTier",
    "RendererConfig",
]
