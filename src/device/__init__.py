"""
PyAgent 设备ID系统

提供设备唯一标识符的生成和持久化管理。
v0.7.0: 新增域系统、设备类型、同步引擎和冲突解决机制
"""

from .conflict_resolver import (
    Conflict,
    ConflictResolver,
    ConflictStatus,
    ConflictType,
    MergeResult,
    ResolutionStrategy,
    ThreeWayMerger,
)
from .device_id import (
    DeviceCapabilities,
    DeviceIDGenerator,
    DeviceIDInfo,
    DeviceIDManager,
    DeviceType,
    device_id_manager,
)
from .domain_manager import (
    DeviceRecord,
    DomainInfo,
    DomainManager,
    domain_manager,
)
from .sync_engine import (
    Branch,
    ChangeType,
    Commit,
    DataChange,
    SyncEngine,
    SyncMode,
)

__all__ = [
    "DeviceIDGenerator",
    "DeviceIDManager",
    "DeviceIDInfo",
    "DeviceType",
    "DeviceCapabilities",
    "device_id_manager",
    "DomainInfo",
    "DeviceRecord",
    "DomainManager",
    "domain_manager",
    "SyncMode",
    "ChangeType",
    "DataChange",
    "Commit",
    "Branch",
    "SyncEngine",
    "ConflictType",
    "ConflictStatus",
    "ResolutionStrategy",
    "Conflict",
    "MergeResult",
    "ThreeWayMerger",
    "ConflictResolver",
]
