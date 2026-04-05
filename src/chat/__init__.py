"""
PyAgent 聊天模块

提供聊天相关的功能。
"""

from typing import Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ChatMessage:
    """聊天消息"""
    role: str
    content: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatMessage":
        return cls(
            role=data.get("role", ""),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", datetime.now().timestamp()),
            metadata=data.get("metadata", {}),
        )

@dataclass
class ChatSession:
    """聊天会话"""
    session_id: str
    messages: list[ChatMessage] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, metadata: dict[str, Any] | None = None) -> ChatMessage:
        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.messages.append(message)
        self.updated_at = datetime.now().timestamp()
        return message
    
    def get_messages(self, limit: int | None = None) -> list[ChatMessage]:
        if limit is None:
            return self.messages.copy()
        return self.messages[-limit:]
    
    def clear(self) -> None:
        self.messages.clear()
        self.updated_at = datetime.now().timestamp()
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatSession":
        return cls(
            session_id=data.get("session_id", ""),
            messages=[ChatMessage.from_dict(m) for m in data.get("messages", [])],
            created_at=data.get("created_at", datetime.now().timestamp()),
            updated_at=data.get("updated_at", datetime.now().timestamp()),
            metadata=data.get("metadata", {}),
        )

__all__ = [
    "ChatMessage",
    "ChatSession",
]
