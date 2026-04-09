"""
PyAgent IM平台适配器 - 基类

定义IM平台适配器的基类和统一消息格式。
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessageType(Enum):
    """消息类型"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"
    CARD = "card"
    SYSTEM = "system"


class ChatType(Enum):
    """聊天类型"""
    PRIVATE = "private"
    GROUP = "group"


@dataclass
class IMUser:
    """IM用户"""
    user_id: str
    name: str = ""
    nickname: str = ""
    avatar: str = ""
    is_bot: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class IMMessage:
    """统一消息格式"""
    message_id: str
    platform: str
    chat_id: str
    chat_type: ChatType
    sender: IMUser
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: float = 0.0
    reply_to: str | None = None
    at_users: list[str] = field(default_factory=list)
    is_at_bot: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class IMReply:
    """回复消息"""
    content: str
    message_type: MessageType = MessageType.TEXT
    reply_to: str | None = None
    at_users: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


class BaseIMAdapter(ABC):
    """IM平台适配器基类"""

    platform: str = "unknown"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self._message_handlers: list[Callable] = []
        self._connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """连接到IM平台"""

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""

    @abstractmethod
    async def send_message(
        self,
        chat_id: str,
        reply: IMReply
    ) -> bool:
        """发送消息"""

    @abstractmethod
    async def get_user_info(self, user_id: str) -> IMUser | None:
        """获取用户信息"""

    @abstractmethod
    async def get_chat_info(self, chat_id: str) -> dict[str, Any] | None:
        """获取聊天信息"""

    def register_message_handler(self, handler: Callable) -> None:
        """注册消息处理器"""
        self._message_handlers.append(handler)

    def unregister_message_handler(self, handler: Callable) -> None:
        """注销消息处理器"""
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)

    async def _dispatch_message(self, message: IMMessage) -> None:
        """分发消息到处理器"""
        for handler in self._message_handlers:
            try:
                await handler(message)
            except Exception as e:
                print(f"Message handler error: {e}")

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected

    def get_platform_name(self) -> str:
        """获取平台名称"""
        return self.platform
