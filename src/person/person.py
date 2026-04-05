"""
PyAgent 用户信息系统 - 用户类

参考MaiBot的Person设计，管理用户信息。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MemoryPoint:
    """记忆点"""
    content: str
    timestamp: float
    source: str = ""
    importance: int = 1


@dataclass
class Person:
    """用户类"""

    user_id: str
    platform: str = "unknown"
    nickname: str = ""
    alias: str = ""

    memory_points: list[MemoryPoint] = field(default_factory=list)
    group_nicknames: dict[str, str] = field(default_factory=dict)

    first_seen: float = field(default_factory=lambda: datetime.now().timestamp())
    last_seen: float = field(default_factory=lambda: datetime.now().timestamp())
    message_count: int = 0

    preferences: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def add_memory_point(
        self,
        content: str,
        source: str = "",
        importance: int = 1
    ) -> None:
        """添加记忆点"""
        memory = MemoryPoint(
            content=content,
            timestamp=datetime.now().timestamp(),
            source=source,
            importance=importance
        )
        self.memory_points.append(memory)

        if len(self.memory_points) > 100:
            self.memory_points.sort(key=lambda x: x.importance, reverse=True)
            self.memory_points = self.memory_points[:50]

    def get_memory_points(self, limit: int = 10) -> list[MemoryPoint]:
        """获取记忆点"""
        sorted_memories = sorted(
            self.memory_points,
            key=lambda x: (x.importance, x.timestamp),
            reverse=True
        )
        return sorted_memories[:limit]

    def search_memory_points(self, keyword: str) -> list[MemoryPoint]:
        """搜索记忆点"""
        return [
            m for m in self.memory_points
            if keyword.lower() in m.content.lower()
        ]

    def set_group_nickname(self, group_id: str, nickname: str) -> None:
        """设置群昵称"""
        self.group_nicknames[group_id] = nickname

    def get_group_nickname(self, group_id: str) -> str:
        """获取群昵称"""
        return self.group_nicknames.get(group_id, self.nickname)

    def update_seen(self) -> None:
        """更新最后见到时间"""
        self.last_seen = datetime.now().timestamp()
        self.message_count += 1

    def build_relationship(self) -> str:
        """构建用户关系信息"""
        parts = []

        if self.nickname:
            parts.append(f"昵称: {self.nickname}")

        if self.alias:
            parts.append(f"别名: {self.alias}")

        days_known = (datetime.now().timestamp() - self.first_seen) / 86400
        parts.append(f"认识天数: {int(days_known)}天")

        parts.append(f"消息数: {self.message_count}")

        if self.memory_points:
            parts.append(f"记忆点: {len(self.memory_points)}个")

        return " | ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "platform": self.platform,
            "nickname": self.nickname,
            "alias": self.alias,
            "memory_points": [
                {
                    "content": m.content,
                    "timestamp": m.timestamp,
                    "source": m.source,
                    "importance": m.importance
                }
                for m in self.memory_points
            ],
            "group_nicknames": self.group_nicknames,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "message_count": self.message_count,
            "preferences": self.preferences,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Person":
        """从字典创建"""
        person = cls(
            user_id=data.get("user_id", ""),
            platform=data.get("platform", "unknown"),
            nickname=data.get("nickname", ""),
            alias=data.get("alias", "")
        )

        person.memory_points = [
            MemoryPoint(
                content=m.get("content", ""),
                timestamp=m.get("timestamp", 0),
                source=m.get("source", ""),
                importance=m.get("importance", 1)
            )
            for m in data.get("memory_points", [])
        ]

        person.group_nicknames = data.get("group_nicknames", {})
        person.first_seen = data.get("first_seen", datetime.now().timestamp())
        person.last_seen = data.get("last_seen", datetime.now().timestamp())
        person.message_count = data.get("message_count", 0)
        person.preferences = data.get("preferences", {})
        person.notes = data.get("notes", [])

        return person
