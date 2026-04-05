"""
PyAgent 文件跟踪器 - 文件元数据跟踪

实现文件元数据的跟踪、存储和查询功能。
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4


class FileStatus(Enum):
    """文件同步状态"""
    LOCAL_ONLY = "local_only"
    SYNCING = "syncing"
    SYNCED = "synced"
    CONFLICT = "conflict"
    DELETED = "deleted"


@dataclass
class FileMetadata:
    """文件元数据"""
    file_id: str
    file_name: str
    file_path: str
    device_id: str
    size: int
    created_at: str
    modified_at: str
    checksum: str
    status: str = FileStatus.LOCAL_ONLY.value
    content_type: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_id": self.file_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "device_id": self.device_id,
            "size": self.size,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "checksum": self.checksum,
            "status": self.status,
            "content_type": self.content_type,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileMetadata":
        return cls(
            file_id=data.get("file_id", ""),
            file_name=data.get("file_name", ""),
            file_path=data.get("file_path", ""),
            device_id=data.get("device_id", ""),
            size=data.get("size", 0),
            created_at=data.get("created_at", ""),
            modified_at=data.get("modified_at", ""),
            checksum=data.get("checksum", ""),
            status=data.get("status", FileStatus.LOCAL_ONLY.value),
            content_type=data.get("content_type", ""),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class FileLocation:
    """文件位置信息"""
    file_id: str
    device_id: str
    is_primary: bool
    last_sync: str
    is_available: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_id": self.file_id,
            "device_id": self.device_id,
            "is_primary": self.is_primary,
            "last_sync": self.last_sync,
            "is_available": self.is_available,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileLocation":
        return cls(
            file_id=data.get("file_id", ""),
            device_id=data.get("device_id", ""),
            is_primary=data.get("is_primary", False),
            last_sync=data.get("last_sync", ""),
            is_available=data.get("is_available", True),
        )


class FileTracker:
    """文件跟踪器

    负责跟踪文件元数据、位置信息和访问记录。
    """

    def __init__(self, data_dir: str = "data/storage/tracker"):
        self.data_dir = Path(data_dir)
        self.metadata_dir = self.data_dir / "metadata"
        self.locations_dir = self.data_dir / "locations"
        self.access_dir = self.data_dir / "access"

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.locations_dir.mkdir(parents=True, exist_ok=True)
        self.access_dir.mkdir(parents=True, exist_ok=True)

        self._metadata_cache: dict[str, FileMetadata] = {}
        self._location_cache: dict[str, list[FileLocation]] = {}
        self._access_history: list[dict[str, Any]] = []

        self._load_cache()

    def _load_cache(self) -> None:
        """加载缓存"""
        for metadata_file in self.metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, encoding="utf-8") as f:
                    data = json.load(f)
                    metadata = FileMetadata.from_dict(data)
                    self._metadata_cache[metadata.file_id] = metadata
            except Exception:
                pass

        for location_file in self.locations_dir.glob("*.json"):
            try:
                with open(location_file, encoding="utf-8") as f:
                    data = json.load(f)
                    file_id = location_file.stem
                    locations = [FileLocation.from_dict(loc) for loc in data]
                    self._location_cache[file_id] = locations
            except Exception:
                pass

    def _save_metadata(self, metadata: FileMetadata) -> None:
        """保存元数据"""
        metadata_file = self.metadata_dir / f"{metadata.file_id}.json"
        try:
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _save_locations(self, file_id: str, locations: list[FileLocation]) -> None:
        """保存位置信息"""
        location_file = self.locations_dir / f"{file_id}.json"
        try:
            with open(location_file, "w", encoding="utf-8") as f:
                json.dump([loc.to_dict() for loc in locations], f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _record_access(self, file_id: str, action: str) -> None:
        """记录访问"""
        access_record = {
            "file_id": file_id,
            "action": action,
            "timestamp": datetime.now().isoformat(),
        }
        self._access_history.append(access_record)

        access_file = self.access_dir / f"{datetime.now().strftime('%Y%m%d')}.json"
        try:
            records = []
            if access_file.exists():
                with open(access_file, encoding="utf-8") as f:
                    records = json.load(f)
            records.append(access_record)
            with open(access_file, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @staticmethod
    def calculate_checksum(file_path: str) -> str:
        """计算文件校验和"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    @staticmethod
    def generate_file_id() -> str:
        """生成文件ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid4())[:8]
        return f"file_{timestamp}_{random_suffix}"

    def track_file(self, file_path: str, device_id: str) -> FileMetadata | None:
        """跟踪文件元数据

        Args:
            file_path: 文件路径
            device_id: 设备ID

        Returns:
            FileMetadata | None: 文件元数据
        """
        path = Path(file_path)
        if not path.exists():
            return None

        stat = path.stat()
        checksum = self.calculate_checksum(file_path)

        existing = self.get_file_by_path(file_path)
        if existing is not None:
            existing.size = stat.st_size
            existing.modified_at = datetime.now().isoformat()
            existing.checksum = checksum
            existing.device_id = device_id
            self._save_metadata(existing)
            self._metadata_cache[existing.file_id] = existing
            self._record_access(existing.file_id, "update")
            return existing

        metadata = FileMetadata(
            file_id=self.generate_file_id(),
            file_name=path.name,
            file_path=str(path.absolute()),
            device_id=device_id,
            size=stat.st_size,
            created_at=datetime.now().isoformat(),
            modified_at=datetime.now().isoformat(),
            checksum=checksum,
            status=FileStatus.LOCAL_ONLY.value,
        )

        self._save_metadata(metadata)
        self._metadata_cache[metadata.file_id] = metadata

        location = FileLocation(
            file_id=metadata.file_id,
            device_id=device_id,
            is_primary=True,
            last_sync=datetime.now().isoformat(),
        )
        self._location_cache[metadata.file_id] = [location]
        self._save_locations(metadata.file_id, [location])

        self._record_access(metadata.file_id, "create")

        return metadata

    def get_file_metadata(self, file_id: str) -> FileMetadata | None:
        """获取文件元数据

        Args:
            file_id: 文件ID

        Returns:
            FileMetadata | None: 文件元数据
        """
        return self._metadata_cache.get(file_id)

    def get_file_by_path(self, file_path: str) -> FileMetadata | None:
        """根据路径获取文件元数据

        Args:
            file_path: 文件路径

        Returns:
            FileMetadata | None: 文件元数据
        """
        abs_path = str(Path(file_path).absolute())
        for metadata in self._metadata_cache.values():
            if metadata.file_path == abs_path:
                return metadata
        return None

    def get_file_location(self, file_id: str) -> list[FileLocation]:
        """获取文件位置信息

        Args:
            file_id: 文件ID

        Returns:
            list[FileLocation]: 位置信息列表
        """
        return self._location_cache.get(file_id, [])

    def get_primary_device(self, file_id: str) -> str | None:
        """获取文件主设备ID

        Args:
            file_id: 文件ID

        Returns:
            str | None: 设备ID
        """
        locations = self.get_file_location(file_id)
        for loc in locations:
            if loc.is_primary:
                return loc.device_id
        return None

    def update_file_status(self, file_id: str, status: FileStatus) -> bool:
        """更新文件同步状态

        Args:
            file_id: 文件ID
            status: 新状态

        Returns:
            bool: 是否成功更新
        """
        metadata = self._metadata_cache.get(file_id)
        if metadata is None:
            return False

        metadata.status = status.value
        self._save_metadata(metadata)
        self._record_access(file_id, f"status_{status.value}")

        return True

    def add_file_location(self, file_id: str, device_id: str, is_primary: bool = False) -> bool:
        """添加文件位置

        Args:
            file_id: 文件ID
            device_id: 设备ID
            is_primary: 是否为主设备

        Returns:
            bool: 是否成功添加
        """
        if file_id not in self._metadata_cache:
            return False

        locations = self._location_cache.get(file_id, [])

        for loc in locations:
            if loc.device_id == device_id:
                loc.last_sync = datetime.now().isoformat()
                loc.is_primary = is_primary
                self._save_locations(file_id, locations)
                return True

        location = FileLocation(
            file_id=file_id,
            device_id=device_id,
            is_primary=is_primary,
            last_sync=datetime.now().isoformat(),
        )
        locations.append(location)
        self._location_cache[file_id] = locations
        self._save_locations(file_id, locations)

        return True

    def remove_file_location(self, file_id: str, device_id: str) -> bool:
        """移除文件位置

        Args:
            file_id: 文件ID
            device_id: 设备ID

        Returns:
            bool: 是否成功移除
        """
        locations = self._location_cache.get(file_id, [])
        new_locations = [loc for loc in locations if loc.device_id != device_id]

        if len(new_locations) == len(locations):
            return False

        self._location_cache[file_id] = new_locations
        self._save_locations(file_id, new_locations)

        return True

    def get_recent_files(self, limit: int = 3) -> list[FileMetadata]:
        """获取最近访问的文件

        Args:
            limit: 最大返回数量

        Returns:
            list[FileMetadata]: 文件元数据列表
        """
        recent_access: list[dict[str, Any]] = []
        access_files = sorted(self.access_dir.glob("*.json"), reverse=True)

        for access_file in access_files:
            try:
                with open(access_file, encoding="utf-8") as f:
                    records = json.load(f)
                    recent_access.extend(records)
            except Exception:
                pass

        recent_access.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        seen_files: set[str] = set()
        result: list[FileMetadata] = []

        for record in recent_access:
            file_id = record.get("file_id", "")
            if file_id and file_id not in seen_files:
                metadata = self._metadata_cache.get(file_id)
                if metadata and metadata.status != FileStatus.DELETED.value:
                    result.append(metadata)
                    seen_files.add(file_id)
                    if len(result) >= limit:
                        break

        return result

    def list_all_files(self) -> list[FileMetadata]:
        """列出所有文件

        Returns:
            list[FileMetadata]: 所有文件元数据
        """
        return [
            m for m in self._metadata_cache.values()
            if m.status != FileStatus.DELETED.value
        ]

    def list_files_by_device(self, device_id: str) -> list[FileMetadata]:
        """列出设备的所有文件

        Args:
            device_id: 设备ID

        Returns:
            list[FileMetadata]: 文件元数据列表
        """
        return [
            m for m in self._metadata_cache.values()
            if m.device_id == device_id and m.status != FileStatus.DELETED.value
        ]

    def delete_file_metadata(self, file_id: str) -> bool:
        """删除文件元数据

        Args:
            file_id: 文件ID

        Returns:
            bool: 是否成功删除
        """
        metadata = self._metadata_cache.get(file_id)
        if metadata is None:
            return False

        metadata.status = FileStatus.DELETED.value
        self._save_metadata(metadata)
        self._record_access(file_id, "delete")

        return True

    def get_files_by_status(self, status: FileStatus) -> list[FileMetadata]:
        """根据状态获取文件

        Args:
            status: 文件状态

        Returns:
            list[FileMetadata]: 文件元数据列表
        """
        return [
            m for m in self._metadata_cache.values()
            if m.status == status.value
        ]

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            dict[str, Any]: 统计信息
        """
        files = self.list_all_files()
        total_size = sum(f.size for f in files)

        status_counts: dict[str, int] = {}
        for status in FileStatus:
            status_counts[status.value] = len([
                f for f in files if f.status == status.value
            ])

        return {
            "total_files": len(files),
            "total_size": total_size,
            "status_counts": status_counts,
            "devices_with_files": len({f.device_id for f in files}),
        }
