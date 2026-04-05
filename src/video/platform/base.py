from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class PlatformCapabilities:
    can_hardware_encode: bool = False
    can_gpu_render: bool = False
    max_preview_fps: int = 30
    max_resolution: tuple[int, int] = (1920, 1080)
    supports_touch: bool = False
    supports_offline: bool = False
    storage_type: str = "file"
    renderer_type: str = "canvas"


class PlatformAdapter(ABC):
    def __init__(self):
        self.capabilities = PlatformCapabilities()

    @abstractmethod
    def get_platform_name(self) -> str:
        pass

    @abstractmethod
    def detect_capabilities(self) -> PlatformCapabilities:
        pass

    @abstractmethod
    def get_storage(self) -> Any:
        pass

    @abstractmethod
    def get_renderer_config(self) -> dict:
        pass
