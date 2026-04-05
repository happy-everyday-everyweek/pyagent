"""
PyAgent 分布式存储 - 分布式存储核心

实现跨设备的文件上传、下载、同步和管理功能。
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from src.device.domain_manager import domain_manager

from .file_tracker import FileMetadata, FileStatus, FileTracker
from .sync_protocol import SyncProtocol

logger = logging.getLogger(__name__)


class DistributedStorage:
    """分布式存储核心类

    提供跨设备的文件存储和同步功能。
    """

    def __init__(
        self,
        data_dir: str = "data/storage",
        local_storage_dir: str = "data/storage/files",
    ):
        self.data_dir = Path(data_dir)
        self.local_storage_dir = Path(local_storage_dir)
        self.cache_dir = self.data_dir / "cache"

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.local_storage_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._file_tracker = FileTracker(str(self.data_dir / "tracker"))
        self._sync_protocol = SyncProtocol(str(self.data_dir / "sync"))

        self._device_id = ""
        self._initialized = False

    def initialize(self) -> None:
        """初始化分布式存储"""
        if self._initialized:
            return

        device_info = domain_manager._device_id_manager.get_device_info()
        if device_info:
            self._device_id = device_info.device_id
            self._sync_protocol.set_device_id(self._device_id)

        self._initialized = True
        logger.info(f"Distributed storage initialized for device: {self._device_id}")

    def _ensure_initialized(self) -> None:
        """确保已初始化"""
        if not self._initialized:
            self.initialize()

    def _get_local_file_path(self, file_id: str, file_name: str) -> Path:
        """获取本地存储路径"""
        file_dir = self.local_storage_dir / file_id[:2]
        file_dir.mkdir(parents=True, exist_ok=True)
        return file_dir / file_name

    def upload_file(self, file_path: str, broadcast: bool = True) -> FileMetadata | None:
        """上传文件并广播元数据到域

        Args:
            file_path: 文件路径
            broadcast: 是否广播元数据

        Returns:
            FileMetadata | None: 文件元数据
        """
        self._ensure_initialized()

        source_path = Path(file_path)
        if not source_path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        metadata = self._file_tracker.track_file(file_path, self._device_id)
        if metadata is None:
            logger.error(f"Failed to track file: {file_path}")
            return None

        local_path = self._get_local_file_path(metadata.file_id, metadata.file_name)
        if not local_path.exists():
            try:
                shutil.copy2(source_path, local_path)
                metadata.file_path = str(local_path)
                metadata.status = FileStatus.SYNCED.value
            except Exception as e:
                logger.error(f"Failed to copy file to local storage: {e}")
                metadata.status = FileStatus.LOCAL_ONLY.value

        self._file_tracker._save_metadata(metadata)

        if broadcast:
            domain_info = domain_manager.get_domain_info()
            if domain_info:
                target_devices = [
                    d for d in domain_info.devices
                    if d != self._device_id
                ]
                if target_devices:
                    self._sync_protocol.broadcast_file_metadata(
                        metadata.to_dict(),
                        target_devices
                    )

        logger.info(f"File uploaded: {metadata.file_id} ({metadata.file_name})")
        return metadata

    def get_file(self, file_id: str, pull_from_remote: bool = True) -> tuple[bytes | None, FileMetadata | None]:
        """获取文件，如果需要从远程设备拉取

        Args:
            file_id: 文件ID
            pull_from_remote: 是否从远程拉取

        Returns:
            tuple[bytes | None, FileMetadata | None]: (文件内容, 文件元数据)
        """
        self._ensure_initialized()

        metadata = self._file_tracker.get_file_metadata(file_id)
        if metadata is None:
            logger.error(f"File metadata not found: {file_id}")
            return None, None

        file_path = Path(metadata.file_path)
        if file_path.exists():
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                logger.info(f"File retrieved from local: {file_id}")
                return content, metadata
            except Exception as e:
                logger.error(f"Failed to read local file: {e}")

        if pull_from_remote:
            locations = self._file_tracker.get_file_location(file_id)
            for loc in locations:
                if loc.device_id != self._device_id and loc.is_available:
                    request_id = self._sync_protocol.request_file_pull(
                        file_id=file_id,
                        from_device=loc.device_id,
                        file_name=metadata.file_name,
                        checksum=metadata.checksum,
                    )
                    logger.info(f"File pull requested: {file_id} from {loc.device_id}, request_id: {request_id}")
                    break

        return None, metadata

    def get_file_path(self, file_id: str) -> Path | None:
        """获取文件路径

        Args:
            file_id: 文件ID

        Returns:
            Path | None: 文件路径
        """
        self._ensure_initialized()

        metadata = self._file_tracker.get_file_metadata(file_id)
        if metadata is None:
            return None

        file_path = Path(metadata.file_path)
        if file_path.exists():
            return file_path

        return None

    def list_files(self, device_id: str | None = None) -> list[FileMetadata]:
        """列出所有文件

        Args:
            device_id: 设备ID，None表示所有设备

        Returns:
            list[FileMetadata]: 文件元数据列表
        """
        self._ensure_initialized()

        if device_id:
            return self._file_tracker.list_files_by_device(device_id)
        return self._file_tracker.list_all_files()

    def delete_file(self, file_id: str, sync: bool = True) -> bool:
        """删除文件并同步

        Args:
            file_id: 文件ID
            sync: 是否同步删除通知

        Returns:
            bool: 是否成功删除
        """
        self._ensure_initialized()

        metadata = self._file_tracker.get_file_metadata(file_id)
        if metadata is None:
            logger.error(f"File not found: {file_id}")
            return False

        file_path = Path(metadata.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete file: {e}")

        self._file_tracker.delete_file_metadata(file_id)

        if sync:
            domain_info = domain_manager.get_domain_info()
            if domain_info:
                target_devices = [
                    d for d in domain_info.devices
                    if d != self._device_id
                ]
                if target_devices:
                    self._sync_protocol.notify_file_delete(file_id, target_devices)

        logger.info(f"File deleted: {file_id}")
        return True

    def sync_file_from_metadata(self, file_info: dict[str, Any]) -> bool:
        """根据元数据同步文件

        Args:
            file_info: 文件元数据

        Returns:
            bool: 是否成功
        """
        self._ensure_initialized()

        metadata = FileMetadata.from_dict(file_info)

        existing = self._file_tracker.get_file_metadata(metadata.file_id)
        if existing is not None:
            if existing.checksum == metadata.checksum:
                return True

            if existing.modified_at >= metadata.modified_at:
                return True

        self._file_tracker._metadata_cache[metadata.file_id] = metadata
        self._file_tracker._save_metadata(metadata)

        self._file_tracker.add_file_location(
            metadata.file_id,
            metadata.device_id,
            is_primary=True
        )

        logger.info(f"File metadata synced: {metadata.file_id}")
        return True

    def receive_file_pull_request(self, request_id: str, file_id: str, requester_device_id: str) -> bool:
        """处理文件拉取请求

        Args:
            request_id: 请求ID
            file_id: 文件ID
            requester_device_id: 请求者设备ID

        Returns:
            bool: 是否成功
        """
        self._ensure_initialized()

        metadata = self._file_tracker.get_file_metadata(file_id)
        if metadata is None:
            logger.error(f"File not found for pull request: {file_id}")
            return False

        file_path = Path(metadata.file_path)
        if not file_path.exists():
            logger.error(f"File not available: {file_path}")
            return False

        logger.info(f"File pull request processed: {file_id} to {requester_device_id}")
        return True

    def get_file_info(self, file_id: str) -> dict[str, Any] | None:
        """获取文件信息

        Args:
            file_id: 文件ID

        Returns:
            dict[str, Any] | None: 文件信息
        """
        self._ensure_initialized()

        metadata = self._file_tracker.get_file_metadata(file_id)
        if metadata is None:
            return None

        locations = self._file_tracker.get_file_location(file_id)

        return {
            "metadata": metadata.to_dict(),
            "locations": [loc.to_dict() for loc in locations],
        }

    def get_recent_files(self, limit: int = 3) -> list[FileMetadata]:
        """获取最近访问的文件

        Args:
            limit: 最大返回数量

        Returns:
            list[FileMetadata]: 文件元数据列表
        """
        self._ensure_initialized()
        return self._file_tracker.get_recent_files(limit)

    def get_storage_stats(self) -> dict[str, Any]:
        """获取存储统计信息

        Returns:
            dict[str, Any]: 统计信息
        """
        self._ensure_initialized()

        tracker_stats = self._file_tracker.get_stats()
        sync_stats = self._sync_protocol.get_sync_stats()

        local_files = list(self.local_storage_dir.rglob("*"))
        local_size = sum(f.stat().st_size for f in local_files if f.is_file())

        return {
            "device_id": self._device_id,
            "tracker": tracker_stats,
            "sync": sync_stats,
            "local_storage": {
                "file_count": len([f for f in local_files if f.is_file()]),
                "total_size": local_size,
                "storage_dir": str(self.local_storage_dir),
            },
        }

    def check_file_exists(self, file_id: str) -> bool:
        """检查文件是否存在

        Args:
            file_id: 文件ID

        Returns:
            bool: 是否存在
        """
        self._ensure_initialized()

        metadata = self._file_tracker.get_file_metadata(file_id)
        if metadata is None:
            return False

        return Path(metadata.file_path).exists()

    def get_file_checksum(self, file_id: str) -> str | None:
        """获取文件校验和

        Args:
            file_id: 文件ID

        Returns:
            str | None: 校验和
        """
        self._ensure_initialized()

        metadata = self._file_tracker.get_file_metadata(file_id)
        if metadata is None:
            return None

        return metadata.checksum

    def update_file_tags(self, file_id: str, tags: list[str]) -> bool:
        """更新文件标签

        Args:
            file_id: 文件ID
            tags: 标签列表

        Returns:
            bool: 是否成功
        """
        self._ensure_initialized()

        metadata = self._file_tracker.get_file_metadata(file_id)
        if metadata is None:
            return False

        metadata.tags = tags
        self._file_tracker._save_metadata(metadata)

        logger.info(f"File tags updated: {file_id}")
        return True

    def search_files(self, query: str) -> list[FileMetadata]:
        """搜索文件

        Args:
            query: 搜索关键词

        Returns:
            list[FileMetadata]: 匹配的文件列表
        """
        self._ensure_initialized()

        all_files = self._file_tracker.list_all_files()
        query_lower = query.lower()

        return [
            f for f in all_files
            if query_lower in f.file_name.lower()
            or query_lower in f.file_path.lower()
            or any(query_lower in tag.lower() for tag in f.tags)
        ]

    def export_metadata(self, file_path: str) -> bool:
        """导出元数据

        Args:
            file_path: 导出文件路径

        Returns:
            bool: 是否成功
        """
        self._ensure_initialized()

        all_files = self._file_tracker.list_all_files()
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "device_id": self._device_id,
            "files": [f.to_dict() for f in all_files],
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Metadata exported to: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export metadata: {e}")
            return False

    def import_metadata(self, file_path: str) -> int:
        """导入元数据

        Args:
            file_path: 导入文件路径

        Returns:
            int: 导入的文件数量
        """
        self._ensure_initialized()

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            files = data.get("files", [])
            imported_count = 0

            for file_data in files:
                metadata = FileMetadata.from_dict(file_data)
                existing = self._file_tracker.get_file_metadata(metadata.file_id)

                if existing is None:
                    self._file_tracker._metadata_cache[metadata.file_id] = metadata
                    self._file_tracker._save_metadata(metadata)
                    imported_count += 1

            logger.info(f"Imported {imported_count} files from: {file_path}")
            return imported_count
        except Exception as e:
            logger.error(f"Failed to import metadata: {e}")
            return 0


distributed_storage: DistributedStorage | None = None


def get_distributed_storage() -> DistributedStorage:
    """获取分布式存储实例"""
    global distributed_storage
    if distributed_storage is None:
        distributed_storage = DistributedStorage()
        distributed_storage.initialize()
    return distributed_storage
