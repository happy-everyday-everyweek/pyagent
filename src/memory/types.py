"""
PyAgent 记忆系统 - 类型定义

实现记忆隔离和四级记忆架构：
- 聊天智能体记忆：初级/周级/月级/季度级
- 工作智能体记忆：项目记忆/偏好记忆
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MemoryLevel(Enum):
    """聊天智能体记忆级别"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class WorkMemoryType(Enum):
    """工作智能体记忆类型"""
    PROJECT = "project"
    PREFERENCE = "preference"


class MemoryPriority(Enum):
    """记忆优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PERMANENT = "permanent"


@dataclass
class ChatMemoryEntry:
    """聊天智能体记忆条目"""
    id: str
    content: str
    level: MemoryLevel = MemoryLevel.DAILY
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    source: str = ""
    importance: float = 0.5
    access_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    consolidated_from: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "level": self.level.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "importance": self.importance,
            "access_count": self.access_count,
            "metadata": self.metadata,
            "consolidated_from": self.consolidated_from,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatMemoryEntry":
        return cls(
            id=data["id"],
            content=data["content"],
            level=MemoryLevel(data.get("level", "daily")),
            timestamp=data.get("timestamp", datetime.now().timestamp()),
            source=data.get("source", ""),
            importance=data.get("importance", 0.5),
            access_count=data.get("access_count", 0),
            metadata=data.get("metadata", {}),
            consolidated_from=data.get("consolidated_from", []),
            created_at=data.get("created_at", datetime.now().timestamp()),
        )


@dataclass
class ProjectMemoryDomain:
    """项目记忆域"""
    id: str
    name: str
    description: str = ""
    project_path: str = ""
    keywords: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now().timestamp())
    memories: list["ProjectMemoryEntry"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "project_path": self.project_path,
            "keywords": self.keywords,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "memories": [m.to_dict() for m in self.memories],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectMemoryDomain":
        memories = [ProjectMemoryEntry.from_dict(m) for m in data.get("memories", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            project_path=data.get("project_path", ""),
            keywords=data.get("keywords", []),
            created_at=data.get("created_at", datetime.now().timestamp()),
            updated_at=data.get("updated_at", datetime.now().timestamp()),
            memories=memories,
        )


@dataclass
class ProjectMemoryEntry:
    """项目记忆条目"""
    id: str
    domain_id: str
    content: str
    memory_type: str = "fact"
    priority: MemoryPriority = MemoryPriority.MEDIUM
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    importance: float = 0.5
    access_count: int = 0
    decay_rate: float = 0.01
    last_accessed_at: float | None = None
    expires_at: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "domain_id": self.domain_id,
            "content": self.content,
            "memory_type": self.memory_type,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "importance": self.importance,
            "access_count": self.access_count,
            "decay_rate": self.decay_rate,
            "last_accessed_at": self.last_accessed_at,
            "expires_at": self.expires_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectMemoryEntry":
        return cls(
            id=data["id"],
            domain_id=data["domain_id"],
            content=data["content"],
            memory_type=data.get("memory_type", "fact"),
            priority=MemoryPriority(data.get("priority", "medium")),
            timestamp=data.get("timestamp", datetime.now().timestamp()),
            importance=data.get("importance", 0.5),
            access_count=data.get("access_count", 0),
            decay_rate=data.get("decay_rate", 0.01),
            last_accessed_at=data.get("last_accessed_at"),
            expires_at=data.get("expires_at"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class PreferenceMemory:
    """偏好记忆"""
    id: str
    content: str
    category: str = "general"
    priority: MemoryPriority = MemoryPriority.HIGH
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    importance: float = 0.8
    access_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "importance": self.importance,
            "access_count": self.access_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PreferenceMemory":
        return cls(
            id=data["id"],
            content=data["content"],
            category=data.get("category", "general"),
            priority=MemoryPriority(data.get("priority", "high")),
            timestamp=data.get("timestamp", datetime.now().timestamp()),
            importance=data.get("importance", 0.8),
            access_count=data.get("access_count", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MemoryConsolidationResult:
    """记忆整理结果"""
    source_level: MemoryLevel
    target_level: MemoryLevel
    source_count: int
    consolidated_count: int
    consolidated_ids: list[str] = field(default_factory=list)
    new_entry_id: str | None = None
