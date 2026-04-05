"""
PyAgent 集成测试 - 存储系统集成测试

测试文件追踪器、同步协议和分布式存储。
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from storage.file_tracker import FileTracker, FileMetadata, FileStatus, FileLocation
from storage.sync_protocol import SyncProtocol


class TestFileTrackerIntegration:
    """文件追踪器集成测试"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.tracker = FileTracker(self.temp_dir)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_track_multiple_files(self):
        """测试追踪多个文件"""
        files = []
        for i in range(5):
            file_path = Path(self.temp_dir) / f"test_{i}.txt"
            file_path.write_text(f"content {i}")
            files.append(file_path)

        for file_path in files:
            metadata = self.tracker.track_file(str(file_path), "device_001")
            assert metadata is not None

        all_files = self.tracker.list_all_files()
        assert len(all_files) == 5

    def test_file_modification_tracking(self):
        """测试文件修改追踪"""
        file_path = Path(self.temp_dir) / "test.txt"
        file_path.write_text("original content")

        metadata1 = self.tracker.track_file(str(file_path), "device_001")
        assert metadata1 is not None

        import time
        time.sleep(0.1)

        file_path.write_text("modified content with more text")

        metadata2 = self.tracker.track_file(str(file_path), "device_001")
        assert metadata2 is not None
        assert metadata2.size != metadata1.size

    def test_file_deletion_tracking(self):
        """测试文件删除追踪"""
        file_path = Path(self.temp_dir) / "test.txt"
        file_path.write_text("content")

        metadata = self.tracker.track_file(str(file_path), "device_001")
        assert metadata is not None

        self.tracker.delete_file_metadata(metadata.file_id)

        all_files = self.tracker.list_all_files()
        assert metadata not in all_files

    def test_multi_device_tracking(self):
        """测试多设备追踪"""
        file_path = Path(self.temp_dir) / "test.txt"
        file_path.write_text("content")

        metadata = self.tracker.track_file(str(file_path), "device_001")
        self.tracker.add_file_location(metadata.file_id, "device_002", is_primary=False)

        locations = self.tracker.get_file_location(metadata.file_id)
        assert len(locations) == 2

    def test_file_status_management(self):
        """测试文件状态管理"""
        file_path = Path(self.temp_dir) / "test.txt"
        file_path.write_text("content")

        metadata = self.tracker.track_file(str(file_path), "device_001")

        self.tracker.update_file_status(metadata.file_id, FileStatus.SYNCING)

        retrieved = self.tracker.get_file_metadata(metadata.file_id)
        assert retrieved.status == FileStatus.SYNCING.value


class TestSyncProtocolIntegration:
    """同步协议集成测试"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.protocol = SyncProtocol(self.temp_dir)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_device_registration(self):
        """测试设备注册"""
        self.protocol.set_device_id("device_001")
        assert self.protocol._device_id == "device_001"

    def test_file_metadata_broadcast(self):
        """测试文件元数据广播"""
        metadata = {
            "file_id": "file_001",
            "file_name": "test.txt",
            "checksum": "abc123"
        }

        result = self.protocol.broadcast_file_metadata(
            metadata,
            ["device_002", "device_003"]
        )
        assert isinstance(result, list)
        assert len(result) == 2

    def test_pull_request_flow(self):
        """测试拉取请求流程"""
        request_id = self.protocol.request_file_pull(
            file_id="file_001",
            from_device="device_002",
            file_name="test.txt",
            checksum="abc123"
        )

        assert request_id is not None
        assert len(request_id) > 0

    def test_delete_notification(self):
        """测试删除通知"""
        result = self.protocol.notify_file_delete(
            "file_001",
            ["device_002", "device_003"]
        )
        assert isinstance(result, list)
        assert len(result) == 2

    def test_sync_statistics(self):
        """测试同步统计"""
        stats = self.protocol.get_sync_stats()
        assert "pending_requests" in stats
        assert "device_id" in stats


class TestDistributedStorageIntegration:
    """分布式存储集成测试"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.tracker = FileTracker(self.temp_dir)
        self.protocol = SyncProtocol(self.temp_dir)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_sync_workflow(self):
        """测试完整同步工作流"""
        self.protocol.set_device_id("device_001")

        file_path = Path(self.temp_dir) / "test.txt"
        file_path.write_text("content")

        metadata = self.tracker.track_file(str(file_path), "device_001")
        assert metadata is not None

        result = self.protocol.broadcast_file_metadata(
            metadata.to_dict(),
            ["device_002"]
        )
        assert isinstance(result, list)
        assert len(result) == 1

        self.tracker.add_file_location(
            metadata.file_id,
            "device_002",
            is_primary=False
        )

        locations = self.tracker.get_file_location(metadata.file_id)
        assert len(locations) == 2

    def test_conflict_detection(self):
        """测试冲突检测"""
        file_path = Path(self.temp_dir) / "test.txt"
        file_path.write_text("original")

        metadata = self.tracker.track_file(str(file_path), "device_001")

        import time
        time.sleep(0.1)

        file_path.write_text("modified with more content")
        metadata2 = self.tracker.track_file(str(file_path), "device_001")

        assert metadata.size != metadata2.size

    def test_version_tracking(self):
        """测试版本追踪"""
        file_path = Path(self.temp_dir) / "test.txt"

        sizes = []
        for i in range(3):
            file_path.write_text(f"version {i} with some content")
            metadata = self.tracker.track_file(str(file_path), "device_001")
            sizes.append(metadata.size)

        assert sizes[0] > 0
        assert sizes[1] > 0
        assert sizes[2] > 0


class TestFileLocationIntegration:
    """文件位置集成测试"""

    def test_location_management(self):
        """测试位置管理"""
        location = FileLocation(
            file_id="file_001",
            device_id="device_001",
            is_primary=True,
            last_sync="2024-01-01T00:00:00"
        )

        assert location.device_id == "device_001"
        assert location.is_primary is True

    def test_location_serialization(self):
        """测试位置序列化"""
        location = FileLocation(
            file_id="file_001",
            device_id="device_001",
            is_primary=True,
            last_sync="2024-01-01T00:00:00"
        )

        data = location.to_dict()
        new_location = FileLocation.from_dict(data)

        assert new_location.device_id == location.device_id
        assert new_location.is_primary == location.is_primary


class TestFileMetadataIntegration:
    """文件元数据集成测试"""

    def test_metadata_creation(self):
        """测试元数据创建"""
        metadata = FileMetadata(
            file_id="file_001",
            file_name="test.txt",
            file_path="/path/to/test.txt",
            device_id="device_001",
            checksum="abc123",
            size=1024,
            created_at="2024-01-01T00:00:00",
            modified_at="2024-01-01T00:00:00"
        )

        assert metadata.file_id == "file_001"
        assert metadata.status == FileStatus.LOCAL_ONLY.value

    def test_metadata_serialization(self):
        """测试元数据序列化"""
        metadata = FileMetadata(
            file_id="file_001",
            file_name="test.txt",
            file_path="/path/to/test.txt",
            device_id="device_001",
            checksum="abc123",
            size=1024,
            created_at="2024-01-01T00:00:00",
            modified_at="2024-01-01T00:00:00",
            tags=["important", "work"]
        )

        data = metadata.to_dict()
        new_metadata = FileMetadata.from_dict(data)

        assert new_metadata.file_id == metadata.file_id
        assert new_metadata.tags == metadata.tags

    def test_metadata_status_transition(self):
        """测试元数据状态转换"""
        metadata = FileMetadata(
            file_id="file_001",
            file_name="test.txt",
            file_path="/path/to/test.txt",
            device_id="device_001",
            checksum="abc123",
            size=1024,
            created_at="2024-01-01T00:00:00",
            modified_at="2024-01-01T00:00:00"
        )

        assert metadata.status == FileStatus.LOCAL_ONLY.value

        metadata.status = FileStatus.SYNCING.value
        assert metadata.status == FileStatus.SYNCING.value

        metadata.status = FileStatus.SYNCED.value
        assert metadata.status == FileStatus.SYNCED.value
