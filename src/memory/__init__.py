"""
PyAgent 记忆系统

实现记忆隔离和四级记忆架构：
- 聊天智能体记忆：初级/周级/月级/季度级（全部召回，不删除）
- 工作智能体记忆：项目记忆（创建项目记忆域）+ 偏好记忆（加入系统提示词）
"""

from .chat_memory import ChatMemoryStorage, chat_memory_storage
from .types import (
    ChatMemoryEntry,
    MemoryConsolidationResult,
    MemoryLevel,
    MemoryPriority,
    PreferenceMemory,
    ProjectMemoryDomain,
    ProjectMemoryEntry,
    WorkMemoryType,
)
from .types import (
    MemoryPriority as WorkMemoryPriority,
)
from .unified_store import UnifiedMemoryStore, unified_memory_store
from .work_memory import WorkMemoryStorage, work_memory_storage

__all__ = [
    "ChatMemoryEntry",
    "ChatMemoryStorage",
    "chat_memory_storage",
    "MemoryConsolidationResult",
    "MemoryLevel",
    "MemoryPriority",
    "WorkMemoryPriority",
    "PreferenceMemory",
    "ProjectMemoryDomain",
    "ProjectMemoryEntry",
    "WorkMemoryType",
    "UnifiedMemoryStore",
    "unified_memory_store",
    "WorkMemoryStorage",
    "work_memory_storage",
]
