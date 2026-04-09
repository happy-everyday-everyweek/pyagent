"""
PyAgent IM平台适配器模块
"""

from .base import BaseIMAdapter, ChatType, IMMessage, IMReply, IMUser, MessageType
from .dingtalk import DingTalkAdapter
from .feishu import FeishuAdapter
from .intent_middleware import IntentMiddleware, ProcessedMessage, intent_middleware
from .kimi import KimiAdapter
from .onebot import OneBotAdapter
from .router import MessageRouter, message_router
from .verification import IMVerificationManager, VerifiedUser, verification_manager
from .verification.middleware import VerificationMiddleware, verification_middleware
from .wechat import WeChatAdapter
from .wecom import WeComAdapter

__all__ = [
    "BaseIMAdapter",
    "ChatType",
    "DingTalkAdapter",
    "FeishuAdapter",
    "IMMessage",
    "IMReply",
    "IMUser",
    "IMVerificationManager",
    "IntentMiddleware",
    "KimiAdapter",
    "MessageRouter",
    "MessageType",
    "OneBotAdapter",
    "ProcessedMessage",
    "VerificationMiddleware",
    "VerifiedUser",
    "WeChatAdapter",
    "WeComAdapter",
    "intent_middleware",
    "message_router",
    "verification_manager",
    "verification_middleware",
]
