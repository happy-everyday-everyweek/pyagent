"""
PyAgent IM平台适配器 - 微信适配器模块

导出微信适配器相关的类和类型。
"""

from .adapter import WeChatAdapter
from .api import WeChatAPI, WeChatAPIError
from .types import (
    CDNMedia,
    SendResult,
    UploadResult,
    WeChatAccount,
    WeChatContact,
    WeChatGroup,
    WeChatMessage,
    WeChatMessageSource,
    WeChatMessageType,
)

__all__ = [
    "CDNMedia",
    "SendResult",
    "UploadResult",
    "WeChatAPI",
    "WeChatAPIError",
    "WeChatAccount",
    "WeChatAdapter",
    "WeChatContact",
    "WeChatGroup",
    "WeChatMessage",
    "WeChatMessageSource",
    "WeChatMessageType",
]
