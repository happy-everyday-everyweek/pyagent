"""
PyAgent 设备ID系统 - 设备ID生成和管理

实现设备唯一标识符的生成和持久化存储。
v0.7.0: 新增域系统和设备类型支持
"""

import hashlib
import json
import platform
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class DeviceType(Enum):
    """设备类型枚举"""
    PC = "pc"
    MOBILE = "mobile"
    SERVER = "server"
    EDGE = "edge"

    @classmethod
    def auto_detect(cls) -> "DeviceType":
        """自动检测设备类型"""
        system = platform.system().lower()
        machine = platform.machine().lower()

        if system == "linux" and ("arm" in machine or "aarch" in machine):
            if "android" in platform.platform().lower():
                return cls.MOBILE
            return cls.EDGE
        elif system in ["windows", "darwin"]:
            return cls.PC
        elif system == "linux":
            return cls.SERVER
        else:
            return cls.PC


@dataclass
class DeviceCapabilities:
    """设备能力描述

    v0.8.0: 扩展能力字段支持多设备架构
    """
    cpu_cores: int = 0
    memory_gb: float = 0.0
    storage_gb: float = 0.0
    has_gpu: bool = False
    gpu_info: str = ""
    network_type: str = "unknown"
    supports_offline: bool = True
    supports_multimodal: bool = False
    available_tools: list[str] = field(default_factory=list)
    screen_operations: bool = False
    browser_automation: bool = False
    notification_access: bool = False
    sms_access: bool = False
    local_inference: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu_cores": self.cpu_cores,
            "memory_gb": self.memory_gb,
            "storage_gb": self.storage_gb,
            "has_gpu": self.has_gpu,
            "gpu_info": self.gpu_info,
            "network_type": self.network_type,
            "supports_offline": self.supports_offline,
            "supports_multimodal": self.supports_multimodal,
            "available_tools": self.available_tools,
            "screen_operations": self.screen_operations,
            "browser_automation": self.browser_automation,
            "notification_access": self.notification_access,
            "sms_access": self.sms_access,
            "local_inference": self.local_inference,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceCapabilities":
        return cls(
            cpu_cores=data.get("cpu_cores", 0),
            memory_gb=data.get("memory_gb", 0.0),
            storage_gb=data.get("storage_gb", 0.0),
            has_gpu=data.get("has_gpu", False),
            gpu_info=data.get("gpu_info", ""),
            network_type=data.get("network_type", "unknown"),
            supports_offline=data.get("supports_offline", True),
            supports_multimodal=data.get("supports_multimodal", False),
            available_tools=data.get("available_tools", []),
            screen_operations=data.get("screen_operations", False),
            browser_automation=data.get("browser_automation", False),
            notification_access=data.get("notification_access", False),
            sms_access=data.get("sms_access", False),
            local_inference=data.get("local_inference", False),
        )

    @classmethod
    def auto_detect(cls, device_type: DeviceType | None = None) -> "DeviceCapabilities":
        """自动检测设备能力

        Args:
            device_type: 设备类型，如果为None则自动检测

        Returns:
            DeviceCapabilities: 设备能力对象
        """
        if device_type is None:
            device_type = DeviceType.auto_detect()

        try:
            import psutil
            cpu_cores = psutil.cpu_count(logical=True) or 0
            memory_gb = round(psutil.virtual_memory().total / (1024**3), 2)
            if platform.system() == "Windows":
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p("C:\\"), None, None, ctypes.pointer(free_bytes)
                )
                storage_gb = round(free_bytes.value / (1024**3), 2)
            else:
                storage_gb = round(psutil.disk_usage("/").total / (1024**3), 2)
        except Exception:
            cpu_cores = 0
            memory_gb = 0.0
            storage_gb = 0.0

        capabilities = cls(
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            storage_gb=storage_gb,
            has_gpu=False,
            gpu_info="",
            network_type="unknown",
            supports_offline=True,
            supports_multimodal=False,
        )

        if device_type == DeviceType.PC:
            capabilities.available_tools = [
                "file_operations",
                "code_execution",
                "web_search",
                "browser_automation",
                "screen_operations",
                "document_processing",
            ]
            capabilities.screen_operations = True
            capabilities.browser_automation = True
            capabilities.notification_access = False
            capabilities.sms_access = False
            capabilities.local_inference = memory_gb >= 16
            capabilities.supports_multimodal = True
        elif device_type == DeviceType.MOBILE:
            capabilities.available_tools = [
                "file_operations",
                "notification_access",
                "sms_access",
                "camera",
                "location",
            ]
            capabilities.screen_operations = False
            capabilities.browser_automation = False
            capabilities.notification_access = True
            capabilities.sms_access = True
            capabilities.local_inference = False
            capabilities.supports_multimodal = True
        elif device_type == DeviceType.SERVER:
            capabilities.available_tools = [
                "file_operations",
                "code_execution",
                "web_search",
                "api_calls",
                "database_operations",
            ]
            capabilities.screen_operations = False
            capabilities.browser_automation = True
            capabilities.notification_access = False
            capabilities.sms_access = False
            capabilities.local_inference = memory_gb >= 32
            capabilities.supports_multimodal = True
        elif device_type == DeviceType.EDGE:
            capabilities.available_tools = [
                "file_operations",
                "sensor_data",
                "local_processing",
            ]
            capabilities.screen_operations = False
            capabilities.browser_automation = False
            capabilities.notification_access = False
            capabilities.sms_access = False
            capabilities.local_inference = memory_gb >= 8
            capabilities.supports_multimodal = False

        return capabilities


@dataclass
class DeviceIDInfo:
    """设备ID信息

    v0.8.0: 扩展能力访问方法
    """
    device_id: str
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)
    domain_id: str = ""
    device_type: str = "pc"
    device_capabilities: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "created_at": self.created_at,
            "metadata": self.metadata,
            "domain_id": self.domain_id,
            "device_type": self.device_type,
            "device_capabilities": self.device_capabilities,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceIDInfo":
        return cls(
            device_id=data.get("device_id", ""),
            created_at=data.get("created_at", ""),
            metadata=data.get("metadata", {}),
            domain_id=data.get("domain_id", ""),
            device_type=data.get("device_type", "pc"),
            device_capabilities=data.get("device_capabilities", {}),
        )

    def get_device_type_enum(self) -> DeviceType:
        """获取设备类型枚举"""
        try:
            return DeviceType(self.device_type)
        except ValueError:
            return DeviceType.PC

    def get_capabilities(self) -> DeviceCapabilities:
        """获取设备能力对象"""
        return DeviceCapabilities.from_dict(self.device_capabilities)

    def has_capability(self, capability: str) -> bool:
        """检查是否具有指定能力

        Args:
            capability: 能力名称

        Returns:
            bool: 是否具有该能力
        """
        caps = self.get_capabilities()
        capability_map = {
            "screen_operations": caps.screen_operations,
            "browser_automation": caps.browser_automation,
            "notification_access": caps.notification_access,
            "sms_access": caps.sms_access,
            "local_inference": caps.local_inference,
            "supports_multimodal": caps.supports_multimodal,
            "supports_offline": caps.supports_offline,
        }
        return capability_map.get(capability, False)

    def has_tool(self, tool: str) -> bool:
        """检查是否具有指定工具

        Args:
            tool: 工具名称

        Returns:
            bool: 是否具有该工具
        """
        caps = self.get_capabilities()
        return tool in caps.available_tools

    def get_available_tools(self) -> list[str]:
        """获取可用工具列表

        Returns:
            list[str]: 可用工具列表
        """
        caps = self.get_capabilities()
        return caps.available_tools


class DeviceIDGenerator:
    """设备ID生成器

    生成规则：
    1. 获取当前日期 YYYYMMDD 格式
    2. 生成10位随机数字
    3. 将日期和随机数拼接后进行SHA256哈希
    4. 取哈希值的前16位作为设备ID
    """

    @staticmethod
    def generate() -> str:
        """生成设备ID

        Returns:
            str: 16位设备ID
        """
        date_str = datetime.now().strftime("%Y%m%d")
        random_digits = "".join([str(random.randint(0, 9)) for _ in range(10)])
        combined = f"{date_str}{random_digits}"
        hash_value = hashlib.sha256(combined.encode()).hexdigest()
        return hash_value[:16]

    @staticmethod
    def generate_domain_id() -> str:
        """生成域ID

        Returns:
            str: 16位域ID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_digits = "".join([str(random.randint(0, 9)) for _ in range(6)])
        combined = f"domain_{timestamp}_{random_digits}"
        hash_value = hashlib.sha256(combined.encode()).hexdigest()
        return f"d_{hash_value[:14]}"


class DeviceIDManager:
    """设备ID管理器（单例模式）

    负责设备ID的获取、创建和持久化存储。
    """

    _instance: "DeviceIDManager | None" = None
    _initialized: bool

    def __new__(cls, data_dir: str = "data/device") -> "DeviceIDManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, data_dir: str = "data/device"):
        if self._initialized:
            return

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._device_info: DeviceIDInfo | None = None
        self._storage_file = self.data_dir / "device_id.json"

        self._load_device_info()
        self._initialized = True

    def _load_device_info(self) -> None:
        """从文件加载设备ID信息"""
        if self._storage_file.exists():
            try:
                with open(self._storage_file, encoding="utf-8") as f:
                    data = json.load(f)
                    self._device_info = DeviceIDInfo.from_dict(data)
            except Exception:
                self._device_info = None

    def _save_device_info(self) -> None:
        """保存设备ID信息到文件"""
        if self._device_info is None:
            return

        try:
            with open(self._storage_file, "w", encoding="utf-8") as f:
                json.dump(self._device_info.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_device_id(self) -> str:
        """获取或创建设备ID

        如果设备ID已存在则返回现有ID，否则创建新的设备ID。

        Returns:
            str: 16位设备ID
        """
        if self._device_info is not None:
            return self._device_info.device_id

        device_id = DeviceIDGenerator.generate()
        device_type = DeviceType.auto_detect()
        capabilities = DeviceCapabilities.auto_detect(device_type)

        self._device_info = DeviceIDInfo(
            device_id=device_id,
            created_at=datetime.now().isoformat(),
            metadata={},
            domain_id="",
            device_type=device_type.value,
            device_capabilities=capabilities.to_dict(),
        )
        self._save_device_info()

        return device_id

    def get_device_info(self) -> DeviceIDInfo | None:
        """获取设备ID完整信息

        Returns:
            DeviceIDInfo | None: 设备ID信息，如果不存在返回None
        """
        return self._device_info

    def regenerate_device_id(self) -> str:
        """重新生成设备ID

        强制生成新的设备ID并覆盖原有ID。

        Returns:
            str: 新的16位设备ID
        """
        device_id = DeviceIDGenerator.generate()
        device_type = DeviceType.auto_detect()
        capabilities = DeviceCapabilities.auto_detect(device_type)

        self._device_info = DeviceIDInfo(
            device_id=device_id,
            created_at=datetime.now().isoformat(),
            metadata={},
            domain_id="",
            device_type=device_type.value,
            device_capabilities=capabilities.to_dict(),
        )
        self._save_device_info()

        return device_id

    def update_metadata(self, key: str, value: Any) -> None:
        """更新设备元数据

        Args:
            key: 元数据键
            value: 元数据值
        """
        if self._device_info is None:
            self.get_device_id()

        if self._device_info is not None:
            self._device_info.metadata[key] = value
            self._save_device_info()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取设备元数据

        Args:
            key: 元数据键
            default: 默认值

        Returns:
            Any: 元数据值
        """
        if self._device_info is None:
            return default
        return self._device_info.metadata.get(key, default)

    def set_domain_id(self, domain_id: str) -> None:
        """设置设备所属域ID

        Args:
            domain_id: 域ID
        """
        if self._device_info is None:
            self.get_device_id()

        if self._device_info is not None:
            self._device_info.domain_id = domain_id
            self._save_device_info()

    def get_domain_id(self) -> str:
        """获取设备所属域ID

        Returns:
            str: 域ID，如果未设置返回空字符串
        """
        if self._device_info is None:
            return ""
        return self._device_info.domain_id

    def set_device_type(self, device_type: DeviceType) -> None:
        """设置设备类型

        Args:
            device_type: 设备类型枚举
        """
        if self._device_info is None:
            self.get_device_id()

        if self._device_info is not None:
            self._device_info.device_type = device_type.value
            self._save_device_info()

    def get_device_type(self) -> DeviceType:
        """获取设备类型

        Returns:
            DeviceType: 设备类型枚举
        """
        if self._device_info is None:
            return DeviceType.PC
        return self._device_info.get_device_type_enum()

    def update_capabilities(self, capabilities: DeviceCapabilities) -> None:
        """更新设备能力

        Args:
            capabilities: 设备能力对象
        """
        if self._device_info is None:
            self.get_device_id()

        if self._device_info is not None:
            self._device_info.device_capabilities = capabilities.to_dict()
            self._save_device_info()

    def get_capabilities(self) -> DeviceCapabilities:
        """获取设备能力

        Returns:
            DeviceCapabilities: 设备能力对象
        """
        if self._device_info is None:
            return DeviceCapabilities()
        return self._device_info.get_capabilities()

    def clear_device_id(self) -> bool:
        """清除设备ID

        Returns:
            bool: 是否成功清除
        """
        self._device_info = None

        if self._storage_file.exists():
            try:
                self._storage_file.unlink()
            except Exception:
                return False

        return True

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例实例（仅用于测试）"""
        cls._instance = None


device_id_manager = DeviceIDManager()
