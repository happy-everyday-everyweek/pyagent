"""
PyAgent 分布式存储系统

提供跨设备的文件存储和同步功能。
v0.8.0: 新增分布式存储系统
"""

from .distributed import (
    DistributedStorage,
    distributed_storage,
    get_distributed_storage,
)
from .file_tracker import (
    FileLocation,
    FileMetadata,
    FileStatus,
    FileTracker,
)
from .sync_protocol import (
    FilePullRequest,
    FilePullResponse,
    SyncMessage,
    SyncMessageType,
    SyncProtocol,
)

__all__ = [
    "DistributedStorage",
    "FileLocation",
    "FileMetadata",
    "FilePullRequest",
    "FilePullResponse",
    "FileStatus",
    "FileTracker",
    "SyncMessage",
    "SyncMessageType",
    "SyncProtocol",
    "distributed_storage",
    "get_distributed_storage",
]
