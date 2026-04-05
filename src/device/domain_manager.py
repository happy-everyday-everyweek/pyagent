"""
PyAgent 域管理器 - 多设备域管理

实现设备域的创建、加入和设备管理功能。
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .device_id import DeviceIDGenerator, DeviceIDManager


@dataclass
class DomainInfo:
    """域信息"""
    domain_id: str
    name: str
    created_at: str
    owner_device_id: str
    devices: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "name": self.name,
            "created_at": self.created_at,
            "owner_device_id": self.owner_device_id,
            "devices": self.devices,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainInfo":
        return cls(
            domain_id=data.get("domain_id", ""),
            name=data.get("name", "default"),
            created_at=data.get("created_at", ""),
            owner_device_id=data.get("owner_device_id", ""),
            devices=data.get("devices", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class DeviceRecord:
    """设备记录"""
    device_id: str
    device_type: str
    joined_at: str
    last_seen: str
    capabilities: dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "joined_at": self.joined_at,
            "last_seen": self.last_seen,
            "capabilities": self.capabilities,
            "status": self.status,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceRecord":
        return cls(
            device_id=data.get("device_id", ""),
            device_type=data.get("device_type", "pc"),
            joined_at=data.get("joined_at", ""),
            last_seen=data.get("last_seen", ""),
            capabilities=data.get("capabilities", {}),
            status=data.get("status", "active"),
            metadata=data.get("metadata", {}),
        )


class DomainManager:
    """域管理器（单例模式）

    负责设备域的创建、加入和设备管理。
    """

    _instance: "DomainManager | None" = None

    def __new__(cls, data_dir: str = "data/domain") -> "DomainManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, data_dir: str = "data/domain"):
        if self._initialized:
            return

        self.data_dir = Path(data_dir)
        self.devices_dir = self.data_dir / "devices"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.devices_dir.mkdir(parents=True, exist_ok=True)

        self._domain_info: DomainInfo | None = None
        self._domain_file = self.data_dir / "domain.json"
        self._device_id_manager = DeviceIDManager()

        self._load_domain_info()
        self._initialized = True

    def _load_domain_info(self) -> None:
        """从文件加载域信息"""
        if self._domain_file.exists():
            try:
                with open(self._domain_file, encoding="utf-8") as f:
                    data = json.load(f)
                    self._domain_info = DomainInfo.from_dict(data)
            except Exception:
                self._domain_info = None

    def _save_domain_info(self) -> None:
        """保存域信息到文件"""
        if self._domain_info is None:
            return

        try:
            with open(self._domain_file, "w", encoding="utf-8") as f:
                json.dump(self._domain_info.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _get_device_record_file(self, device_id: str) -> Path:
        """获取设备记录文件路径"""
        return self.devices_dir / f"{device_id}.json"

    def _save_device_record(self, record: DeviceRecord) -> None:
        """保存设备记录"""
        record_file = self._get_device_record_file(record.device_id)
        try:
            with open(record_file, "w", encoding="utf-8") as f:
                json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_device_record(self, device_id: str) -> DeviceRecord | None:
        """加载设备记录"""
        record_file = self._get_device_record_file(device_id)
        if record_file.exists():
            try:
                with open(record_file, encoding="utf-8") as f:
                    data = json.load(f)
                    return DeviceRecord.from_dict(data)
            except Exception:
                return None
        return None

    def create_domain(self, name: str = "default") -> str:
        """创建新域

        Args:
            name: 域名称

        Returns:
            str: 新创建的域ID
        """
        domain_id = DeviceIDGenerator.generate_domain_id()
        device_id = self._device_id_manager.get_device_id()
        device_info = self._device_id_manager.get_device_info()

        self._domain_info = DomainInfo(
            domain_id=domain_id,
            name=name,
            created_at=datetime.now().isoformat(),
            owner_device_id=device_id,
            devices=[device_id],
            metadata={},
        )
        self._save_domain_info()

        self._device_id_manager.set_domain_id(domain_id)

        device_record = DeviceRecord(
            device_id=device_id,
            device_type=device_info.device_type if device_info else "pc",
            joined_at=datetime.now().isoformat(),
            last_seen=datetime.now().isoformat(),
            capabilities=device_info.device_capabilities if device_info else {},
            status="active",
            metadata={},
        )
        self._save_device_record(device_record)

        return domain_id

    def join_domain(self, domain_id: str) -> bool:
        """加入现有域

        Args:
            domain_id: 要加入的域ID

        Returns:
            bool: 是否成功加入
        """
        if self._domain_info is not None:
            if self._domain_info.domain_id == domain_id:
                return True

        domain_file = self.data_dir.parent / f"domain_{domain_id}" / "domain.json"
        if not domain_file.exists():
            return False

        try:
            with open(domain_file, encoding="utf-8") as f:
                data = json.load(f)
                domain_info = DomainInfo.from_dict(data)
        except Exception:
            return False

        device_id = self._device_id_manager.get_device_id()
        device_info = self._device_id_manager.get_device_info()

        if device_id not in domain_info.devices:
            domain_info.devices.append(device_id)
            try:
                with open(domain_file, "w", encoding="utf-8") as f:
                    json.dump(domain_info.to_dict(), f, ensure_ascii=False, indent=2)
            except Exception:
                return False

        self._domain_info = domain_info
        self._domain_file = domain_file
        self._save_domain_info()

        self._device_id_manager.set_domain_id(domain_id)

        existing_record = self._load_device_record(device_id)
        if existing_record is None:
            device_record = DeviceRecord(
                device_id=device_id,
                device_type=device_info.device_type if device_info else "pc",
                joined_at=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
                capabilities=device_info.device_capabilities if device_info else {},
                status="active",
                metadata={},
            )
        else:
            device_record = DeviceRecord(
                device_id=existing_record.device_id,
                device_type=existing_record.device_type,
                joined_at=existing_record.joined_at,
                last_seen=datetime.now().isoformat(),
                capabilities=device_info.device_capabilities if device_info else existing_record.capabilities,
                status="active",
                metadata=existing_record.metadata,
            )
        self._save_device_record(device_record)

        return True

    def get_domain_info(self) -> DomainInfo | None:
        """获取当前域信息

        Returns:
            DomainInfo | None: 域信息，如果未加入域返回None
        """
        return self._domain_info

    def get_domain_id(self) -> str:
        """获取当前域ID

        Returns:
            str: 域ID，如果未加入域返回空字符串
        """
        if self._domain_info is None:
            return ""
        return self._domain_info.domain_id

    def get_domain_devices(self) -> list[DeviceRecord]:
        """获取域内设备列表

        Returns:
            list[DeviceRecord]: 设备记录列表
        """
        if self._domain_info is None:
            return []

        devices: list[DeviceRecord] = []
        for device_id in self._domain_info.devices:
            record = self._load_device_record(device_id)
            if record is not None:
                devices.append(record)

        return devices

    def get_device_record(self, device_id: str) -> DeviceRecord | None:
        """获取指定设备的记录

        Args:
            device_id: 设备ID

        Returns:
            DeviceRecord | None: 设备记录，如果不存在返回None
        """
        return self._load_device_record(device_id)

    def update_device_status(self, device_id: str, status: str) -> bool:
        """更新设备状态

        Args:
            device_id: 设备ID
            status: 新状态（active/inactive/offline）

        Returns:
            bool: 是否成功更新
        """
        record = self._load_device_record(device_id)
        if record is None:
            return False

        record.status = status
        record.last_seen = datetime.now().isoformat()
        self._save_device_record(record)
        return True

    def update_device_last_seen(self, device_id: str) -> bool:
        """更新设备最后在线时间

        Args:
            device_id: 设备ID

        Returns:
            bool: 是否成功更新
        """
        record = self._load_device_record(device_id)
        if record is None:
            return False

        record.last_seen = datetime.now().isoformat()
        self._save_device_record(record)
        return True

    def remove_device(self, device_id: str) -> bool:
        """从域中移除设备

        Args:
            device_id: 设备ID

        Returns:
            bool: 是否成功移除
        """
        if self._domain_info is None:
            return False

        if device_id not in self._domain_info.devices:
            return False

        self._domain_info.devices.remove(device_id)
        self._save_domain_info()

        record_file = self._get_device_record_file(device_id)
        if record_file.exists():
            try:
                record_file.unlink()
            except Exception:
                pass

        return True

    def leave_domain(self) -> bool:
        """离开当前域

        Returns:
            bool: 是否成功离开
        """
        if self._domain_info is None:
            return True

        device_id = self._device_id_manager.get_device_id()
        self.remove_device(device_id)

        self._device_id_manager.set_domain_id("")
        self._domain_info = None

        if self._domain_file.exists():
            try:
                self._domain_file.unlink()
            except Exception:
                pass

        return True

    def is_domain_owner(self) -> bool:
        """检查当前设备是否为域所有者

        Returns:
            bool: 是否为域所有者
        """
        if self._domain_info is None:
            return False

        device_id = self._device_id_manager.get_device_id()
        return self._domain_info.owner_device_id == device_id

    def get_device_count(self) -> int:
        """获取域内设备数量

        Returns:
            int: 设备数量
        """
        if self._domain_info is None:
            return 0
        return len(self._domain_info.devices)

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例实例（仅用于测试）"""
        cls._instance = None


domain_manager = DomainManager()
