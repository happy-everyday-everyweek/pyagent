"""
PyAgent 交互模块 - 意图类型定义

定义意图识别的类型系统。
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional


class IntentType(Enum):
    """意图类型枚举"""
    CHAT = auto()
    TASK = auto()
    QUERY = auto()
    COMMAND = auto()
    OPEN_FILE = auto()
    OPEN_APP = auto()
    CREATE_EVENT = auto()
    CREATE_TODO = auto()
    MODIFY_SETTINGS = auto()
    UNKNOWN = auto()


@dataclass
class Intent:
    """
    意图定义
    
    表示用户输入的意图信息，包含：
    - 意图类型
    - 置信度
    - 内容
    - 实体信息
    - 元数据
    """
    type: IntentType
    confidence: float = 0.0
    content: str = ""
    entities: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_input: str = ""
    
    def is_chat(self) -> bool:
        """检查是否为聊天意图"""
        return self.type == IntentType.CHAT
    
    def is_task(self) -> bool:
        """检查是否为任务意图"""
        return self.type == IntentType.TASK
    
    def is_query(self) -> bool:
        """检查是否为查询意图"""
        return self.type == IntentType.QUERY
    
    def is_command(self) -> bool:
        """检查是否为命令意图"""
        return self.type == IntentType.COMMAND
    
    def is_unknown(self) -> bool:
        """检查是否为未知意图"""
        return self.type == IntentType.UNKNOWN
    
    def is_open_file(self) -> bool:
        """检查是否为打开文件意图"""
        return self.type == IntentType.OPEN_FILE
    
    def is_open_app(self) -> bool:
        """检查是否为打开应用意图"""
        return self.type == IntentType.OPEN_APP
    
    def is_create_event(self) -> bool:
        """检查是否为创建日程意图"""
        return self.type == IntentType.CREATE_EVENT
    
    def is_create_todo(self) -> bool:
        """检查是否为创建待办意图"""
        return self.type == IntentType.CREATE_TODO
    
    def is_modify_settings(self) -> bool:
        """检查是否为修改设置意图"""
        return self.type == IntentType.MODIFY_SETTINGS
    
    def needs_redirect(self) -> bool:
        """检查是否需要重定向到其他模块（不发送到聊天模块）"""
        return self.type in (
            IntentType.OPEN_FILE,
            IntentType.OPEN_APP,
            IntentType.CREATE_EVENT,
            IntentType.CREATE_TODO,
            IntentType.MODIFY_SETTINGS
        )
    
    def get_entity(self, key: str, default: Any = None) -> Any:
        """获取实体值"""
        return self.entities.get(key, default)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.name,
            "confidence": self.confidence,
            "content": self.content,
            "entities": self.entities,
            "metadata": self.metadata,
            "raw_input": self.raw_input
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Intent":
        """从字典创建意图"""
        intent_type = IntentType[data.get("type", "UNKNOWN")]
        return cls(
            type=intent_type,
            confidence=data.get("confidence", 0.0),
            content=data.get("content", ""),
            entities=data.get("entities", {}),
            metadata=data.get("metadata", {}),
            raw_input=data.get("raw_input", "")
        )


@dataclass
class EntityInfo:
    """
    实体信息
    
    表示从用户输入中提取的实体。
    """
    name: str
    value: Any
    entity_type: str = "generic"
    confidence: float = 1.0
    position: tuple[int, int] = (0, 0)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "value": self.value,
            "entity_type": self.entity_type,
            "confidence": self.confidence,
            "position": self.position
        }


@dataclass
class IntentContext:
    """
    意图上下文
    
    包含意图识别所需的上下文信息。
    """
    user_id: str = ""
    chat_id: str = ""
    message_id: str = ""
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    user_preferences: dict[str, Any] = field(default_factory=dict)
    session_data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "message_id": self.message_id,
            "conversation_history": self.conversation_history,
            "user_preferences": self.user_preferences,
            "session_data": self.session_data,
            "timestamp": self.timestamp
        }
