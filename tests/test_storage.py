"""
PyAgent 分布式存储测试
"""

import pytest
from pathlib import Path
from datetime import datetime

from storage.file_tracker import FileMetadata, FileStatus, FileLocation, FileTracker
from storage.sync_protocol import SyncProtocol


class TestFileStatus:
    """测试文件状态枚举"""

    def test_status_values(self):
        assert FileStatus.LOCAL_ONLY.value == "local_only"
        assert FileStatus.SYNCING.value == "syncing"
        assert FileStatus.SYNCED.value == "synced"
        assert FileStatus.CONFLICT.value == "conflict"

    def test_status_count(self):
        assert len(FileStatus) == 4


class TestFileLocation:
    """测试文件位置"""

    def test_location_creation(self):
        location = FileLocation(
            device_id="device_001",
            is_primary=True,
            is_available=True
        )
        assert location.device_id == "device_001"
        assert location.is_primary is True
        assert location.is_available is True

    def test_location_defaults(self):
        location = FileLocation(device_id="device_001")
        assert location.is_primary is False
        assert location.is_available is True
        assert location.last_sync is None

    def test_location_to_dict(self):
        location = FileLocation(
            device_id="device_001",
            is_primary=True
        )
        data = location.to_dict()
        assert data["device_id"] == "device_001"
        assert data["is_primary"] is True

    def test_location_from_dict(self):
        data = {
            "device_id": "device_001",
            "is_primary": True,
            "is_available": False,
            "last_sync": "2024-01-01T00:00:00"
        }
        location = FileLocation.from_dict(data)
        assert location.device_id == "device_001"
        assert location.is_primary is True
        assert location.is_available is False


class TestFileMetadata:
    """测试文件元数据"""

    def test_metadata_creation(self):
        metadata = FileMetadata(
            file_id="file_001",
            file_name="test.txt",
            file_path="/path/to/test.txt",
            device_id="device_001",
            checksum="abc123",
            size=1024
        )
        assert metadata.file_id == "file_001"
        assert metadata.file_name == "test.txt"
        assert metadata.size == 1024

    def test_metadata_defaults(self):
        metadata = FileMetadata(
            file_id="file_001",
            file_name="test.txt",
            file_path="/path/to/test.txt",
            device_id="device_001",
            checksum="abc123",
            size=1024
        )
        assert metadata.status == FileStatus.LOCAL_ONLY.value
        assert metadata.tags == []
        assert metadata.version == 1

    def test_metadata_to_dict(self):
        metadata = FileMetadata(
            file_id="file_001",
            file_name="test.txt",
            file_path="/path/to/test.txt",
            device_id="device_001",
            checksum="abc123",
            size=1024,
            tags=["important"]
        )
        data = metadata.to_dict()
        assert data["file_id"] == "file_001"
        assert data["file_name"] == "test.txt"
        assert data["tags"] == ["important"]

    def test_metadata_from_dict(self):
        data = {
            "file_id": "file_001",
            "file_name": "test.txt",
            "file_path": "/path/to/test.txt",
            "device_id": "device_001",
            "checksum": "abc123",
            "size": 1024,
            "status": "synced",
            "created_at": "2024-01-01T00:00:00",
            "modified_at": "2024-01-02T00:00:00",
            "tags": ["tag1"],
            "version": 2
        }
        metadata = FileMetadata.from_dict(data)
        assert metadata.file_id == "file_001"
        assert metadata.status == "synced"
        assert metadata.version == 2


class TestFileTracker:
    """测试文件追踪器"""

    def setup_method(self):
        import tempfile
        import shutil
        self.temp_dir = tempfile.mkdtemp()
        self.tracker = FileTracker(self.temp_dir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_tracker_creation(self):
        assert self.tracker.data_dir == Path(self.temp_dir)
        assert self.tracker._metadata_cache == {}

    def test_track_file(self):
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("test content")

        metadata = self.tracker.track_file(str(test_file), "device_001")
        assert metadata is not None
        assert metadata.file_name == "test.txt"
        assert metadata.size > 0

    def test_track_nonexistent_file(self):
        metadata = self.tracker.track_file("/nonexistent/file.txt", "device_001")
        assert metadata is None

    def test_get_file_metadata(self):
        metadata = FileMetadata(
            file_id="file_001",
            file_name="test.txt",
            file_path="/path/to/test.txt",
            device_id="device_001",
            checksum="abc123",
            size=1024
        )
        self.tracker._metadata_cache["file_001"] = metadata
        self.tracker._save_metadata(metadata)

        retrieved = self.tracker.get_file_metadata("file_001")
        assert retrieved is not None
        assert retrieved.file_id == "file_001"

    def test_get_nonexistent_metadata(self):
        retrieved = self.tracker.get_file_metadata("nonexistent")
        assert retrieved is None

    def test_delete_file_metadata(self):
        metadata = FileMetadata(
            file_id="file_001",
            file_name="test.txt",
            file_path="/path/to/test.txt",
            device_id="device_001",
            checksum="abc123",
            size=1024
        )
        self.tracker._metadata_cache["file_001"] = metadata

        self.tracker.delete_file_metadata("file_001")
        assert "file_001" not in self.tracker._metadata_cache

    def test_add_file_location(self):
        self.tracker.add_file_location("file_001", "device_001", is_primary=True)

        locations = self.tracker.get_file_location("file_001")
        assert len(locations) == 1
        assert locations[0].device_id == "device_001"

    def test_list_all_files(self):
        metadata1 = FileMetadata(
            file_id="file_001",
            file_name="test1.txt",
            file_path="/path/to/test1.txt",
            device_id="device_001",
            checksum="abc123",
            size=1024
        )
        metadata2 = FileMetadata(
            file_id="file_002",
            file_name="test2.txt",
            file_path="/path/to/test2.txt",
            device_id="device_001",
            checksum="def456",
            size=2048
        )
        self.tracker._metadata_cache["file_001"] = metadata1
        self.tracker._metadata_cache["file_002"] = metadata2

        files = self.tracker.list_all_files()
        assert len(files) == 2

    def test_list_files_by_device(self):
        metadata1 = FileMetadata(
            file_id="file_001",
            file_name="test1.txt",
            file_path="/path/to/test1.txt",
            device_id="device_001",
            checksum="abc123",
            size=1024
        )
        metadata2 = FileMetadata(
            file_id="file_002",
            file_name="test2.txt",
            file_path="/path/to/test2.txt",
            device_id="device_002",
            checksum="def456",
            size=2048
        )
        self.tracker._metadata_cache["file_001"] = metadata1
        self.tracker._metadata_cache["file_002"] = metadata2

        files = self.tracker.list_files_by_device("device_001")
        assert len(files) == 1

    def test_get_stats(self):
        metadata = FileMetadata(
            file_id="file_001",
            file_name="test.txt",
            file_path="/path/to/test.txt",
            device_id="device_001",
            checksum="abc123",
            size=1024
        )
        self.tracker._metadata_cache["file_001"] = metadata

        stats = self.tracker.get_stats()
        assert stats["total_files"] == 1
        assert stats["total_size"] == 1024


class TestSyncProtocol:
    """测试同步协议"""

    def setup_method(self):
        import tempfile
        import shutil
        self.temp_dir = tempfile.mkdtemp()
        self.protocol = SyncProtocol(self.temp_dir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_protocol_creation(self):
        assert self.protocol.data_dir == Path(self.temp_dir)

    def test_set_device_id(self):
        self.protocol.set_device_id("device_001")
        assert self.protocol._device_id == "device_001"

    def test_broadcast_file_metadata(self):
        metadata = {
            "file_id": "file_001",
            "file_name": "test.txt"
        }
        result = self.protocol.broadcast_file_metadata(metadata, ["device_002"])
        assert result is True

    def test_request_file_pull(self):
        request_id = self.protocol.request_file_pull(
            file_id="file_001",
            from_device="device_002",
            file_name="test.txt",
            checksum="abc123"
        )
        assert request_id is not None
        assert request_id.startswith("pull_")

    def test_notify_file_delete(self):
        result = self.protocol.notify_file_delete("file_001", ["device_002"])
        assert result is True

    def test_get_sync_stats(self):
        stats = self.protocol.get_sync_stats()
        assert "pending_requests" in stats
        assert "completed_syncs" in stats
