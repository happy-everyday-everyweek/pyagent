"""PyAgent v0.7.0 域系统测试"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from device import (
    ChangeType,
    ConflictResolver,
    DeviceCapabilities,
    DeviceIDManager,
    DeviceType,
    DomainManager,
    ResolutionStrategy,
    SyncEngine,
    SyncMode,
    ThreeWayMerger,
)


def test_device_id_system():
    DeviceIDManager.reset_instance()
    manager = DeviceIDManager(data_dir="test_device")

    device_id = manager.get_device_id()
    assert len(device_id) == 16, f"Device ID should be 16 chars, got {len(device_id)}"
    print(f"Device ID: {device_id}")

    device_type = manager.get_device_type()
    assert isinstance(device_type, DeviceType), f"Device type should be DeviceType enum, got {type(device_type)}"
    print(f"Device Type: {device_type}")

    domain_id = manager.get_domain_id()
    assert domain_id == "", f"Initial domain ID should be empty, got {domain_id}"
    print(f"Domain ID: {domain_id}")

    caps = manager.get_capabilities()
    assert isinstance(caps, DeviceCapabilities), f"Capabilities should be DeviceCapabilities, got {type(caps)}"
    print(f"Capabilities: cpu_cores={caps.cpu_cores}, memory_gb={caps.memory_gb}")

    print("Device ID system test passed!")


def test_domain_manager():
    DeviceIDManager.reset_instance()
    DomainManager.reset_instance()

    device_mgr = DeviceIDManager(data_dir="test_domain_device")
    domain_mgr = DomainManager(data_dir="test_domain")

    domain_id = domain_mgr.create_domain("test_domain")
    assert domain_id.startswith("d_"), f"Domain ID should start with 'd_', got {domain_id}"
    print(f"Created Domain ID: {domain_id}")

    devices = domain_mgr.get_domain_devices()
    assert len(devices) == 1, f"Should have 1 device, got {len(devices)}"
    print(f"Domain Devices: {len(devices)}")

    domain_info = domain_mgr.get_domain_info()
    assert domain_info is not None, "Domain info should not be None"
    assert domain_info.name == "test_domain", f"Domain name should be 'test_domain', got {domain_info.name}"
    print(f"Domain Name: {domain_info.name}")

    is_owner = domain_mgr.is_domain_owner()
    assert is_owner, "Current device should be domain owner"
    print(f"Is Owner: {is_owner}")

    print("Domain manager test passed!")


def test_sync_engine():
    DeviceIDManager.reset_instance()

    sync = SyncEngine(data_dir="test_sync", sync_mode=SyncMode.REALTIME)
    sync.set_device_id("test_device_001")

    change_id = sync.track_change(
        ChangeType.CREATE,
        "test_type",
        "test_key",
        None,
        {"value": 1},
    )
    assert change_id, "Change ID should not be empty"
    print(f"Tracked Change ID: {change_id}")

    pending = sync.get_pending_changes()
    assert len(pending) == 1, f"Should have 1 pending change, got {len(pending)}"
    print(f"Pending Changes: {len(pending)}")

    commit_id = sync.commit("Initial commit")
    assert commit_id, "Commit ID should not be empty"
    print(f"Commit ID: {commit_id}")

    head = sync.get_head_commit_id()
    assert head == commit_id, f"Head should be {commit_id}, got {head}"
    print(f"Head Commit: {head}")

    pending_after = sync.get_pending_changes()
    assert len(pending_after) == 0, f"Should have 0 pending changes after commit, got {len(pending_after)}"

    branch_created = sync.create_branch("feature")
    assert branch_created, "Branch creation should succeed"
    print(f"Created branch: feature")

    branches = sync.get_branches()
    assert "main" in branches and "feature" in branches, f"Should have main and feature branches, got {branches}"
    print(f"Branches: {branches}")

    print("Sync engine test passed!")


def test_conflict_resolver():
    resolver = ConflictResolver(data_dir="test_conflicts")

    stats = resolver.get_statistics()
    assert "total_conflicts" in stats, "Stats should have total_conflicts"
    print(f"Conflict Stats: {stats}")

    print("Conflict resolver test passed!")


def test_three_way_merge():
    merger = ThreeWayMerger()

    result1 = merger.merge({"a": 1}, {"a": 2}, {"a": 2})
    assert result1.success, "Same local and remote should merge successfully"
    assert result1.merged_value == {"a": 2}, f"Merged value should be {{'a': 2}}, got {result1.merged_value}"
    print(f"Merge Test 1: success={result1.success}, merged={result1.merged_value}")

    result2 = merger.merge({"a": 1}, {"a": 2}, {"a": 3})
    assert result2.has_conflicts, "Different local and remote should have conflicts"
    print(f"Merge Test 2: success={result2.success}, has_conflicts={result2.has_conflicts}")

    result3 = merger.merge({"a": 1, "b": 1}, {"a": 2, "b": 1}, {"a": 1, "b": 2})
    assert result3.success, "Non-overlapping changes should merge successfully"
    assert result3.merged_value == {"a": 2, "b": 2}, f"Merged value should be {{'a': 2, 'b': 2}}, got {result3.merged_value}"
    print(f"Merge Test 3: success={result3.success}, merged={result3.merged_value}")

    print("Three-way merge test passed!")


def test_backward_compatibility():
    import json
    from pathlib import Path

    test_dir = Path(tempfile.mkdtemp())
    device_file = test_dir / "device_id.json"

    old_format = {
        "device_id": "abc123def456",
        "created_at": "2025-01-01T00:00:00",
        "metadata": {"key": "value"},
    }

    with open(device_file, "w", encoding="utf-8") as f:
        json.dump(old_format, f)

    DeviceIDManager.reset_instance()
    manager = DeviceIDManager(data_dir=str(test_dir))

    info = manager.get_device_info()
    assert info is not None, "Device info should not be None"
    assert info.device_id == "abc123def456", f"Device ID should be 'abc123def456', got {info.device_id}"
    assert info.domain_id == "", "Domain ID should default to empty string"
    assert info.device_type == "pc", "Device type should default to 'pc'"
    print(f"Backward compatibility test passed! Old format loaded: {info.to_dict()}")


if __name__ == "__main__":
    print("=" * 60)
    print("PyAgent v0.7.0 Domain System Tests")
    print("=" * 60)

    test_device_id_system()
    print()

    test_domain_manager()
    print()

    test_sync_engine()
    print()

    test_conflict_resolver()
    print()

    test_three_way_merge()
    print()

    test_backward_compatibility()
    print()

    print("=" * 60)
    print("All tests passed!")
    print("=" * 60)
