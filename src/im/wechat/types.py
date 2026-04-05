"""
PyAgent IM平台适配器 - 微信适配器类型定义

定义微信适配器专用的数据类型。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WeChatMessageType(Enum):
    """微信消息类型"""
    TEXT = 1
    IMAGE = 2
    VOICE = 3
    FILE = 4
    VIDEO = 5
    LINK = 6
    MINI_PROGRAM = 7
    LOCATION = 8
    SYSTEM = 9


class WeChatMessageSource(Enum):
    """微信消息来源"""
    PRIVATE = "private"
    GROUP = "group"


@dataclass
class WeChatMessage:
    """微信消息"""
    msg_id: str
    sender_id: str
    receiver_id: str
    msg_type: WeChatMessageType
    content: str = ""
    media_url: str | None = None
    source: WeChatMessageSource = WeChatMessageSource.PRIVATE
    group_id: str | None = None
    timestamp: int = 0
    at_users: list[str] = field(default_factory=list)
    is_at_bot: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class WeChatAccount:
    """微信账号信息"""
    account_id: str
    nickname: str = ""
    avatar: str = ""
    login_status: bool = False
    qrcode_url: str | None = None
    wxid: str = ""
    alias: str = ""
    device_id: str = ""


@dataclass
class CDNMedia:
    """CDN媒体信息"""
    aes_key: str
    file_size: int
    file_md5: str
    file_type: str
    cdn_url: str = ""
    file_name: str = ""


@dataclass
class SendResult:
    """发送结果"""
    success: bool
    msg_id: str | None = None
    error: str | None = None
    timestamp: int = 0


@dataclass
class WeChatContact:
    """微信联系人"""
    wxid: str
    nickname: str = ""
    alias: str = ""
    avatar: str = ""
    remark: str = ""
    is_friend: bool = False
    is_group: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class WeChatGroup:
    """微信群组"""
    group_id: str
    group_name: str = ""
    member_count: int = 0
    owner_id: str = ""
    members: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class UploadResult:
    """上传结果"""
    success: bool
    cdn_key: str | None = None
    aes_key: str | None = None
    file_md5: str | None = None
    file_size: int = 0
    error: str | None = None
