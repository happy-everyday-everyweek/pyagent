"""
PyAgent 聊天Agent核心 - 回复生成器类型定义

定义回复生成器的类型系统。
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class ReplyContentType(Enum):
    """回复内容类型"""
    TEXT = auto()
    IMAGE = auto()
    AUDIO = auto()
    VIDEO = auto()
    FILE = auto()
    CARD = auto()


@dataclass
class ReplyContent:
    """回复内容"""
    content_type: ReplyContentType = ReplyContentType.TEXT
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReplySet:
    """回复集合"""
    reply_data: list[ReplyContent] = field(default_factory=list)
    selected_expressions: list[int] = field(default_factory=list)
    quote_message: bool = False


@dataclass
class ReplyConfig:
    """回复配置"""
    max_length: int = 500
    enable_quote: bool = True
    enable_expression: bool = True
    temperature: float = 0.8
    think_level: int = 0
