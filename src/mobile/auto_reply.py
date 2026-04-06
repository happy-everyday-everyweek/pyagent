"""
PyAgent 移动端模块 - 自动回复管理器
移植自 OpenKiwi AutoReplyManager
"""

import logging
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .notification import Notification


class ReplyStatus(Enum):
    """回复状态"""
    SUCCESS = "success"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    NOT_ALLOWED = "not_allowed"
    NO_ACTION = "no_action"


@dataclass
class ReplyRecord:
    """回复记录"""
    notification_id: str
    package_name: str
    reply_text: str
    status: ReplyStatus
    timestamp: datetime = field(default_factory=datetime.now)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "notification_id": self.notification_id,
            "package_name": self.package_name,
            "reply_text": self.reply_text,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
        }


@dataclass
class ReplyTemplate:
    """回复模板"""
    name: str
    template: str
    keywords: list[str] = field(default_factory=list)
    packages: list[str] = field(default_factory=list)

    def matches(self, text: str, package_name: str) -> bool:
        """检查是否匹配"""
        if self.packages and package_name not in self.packages:
            return False

        text_lower = text.lower()
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                return True

        return False

    def render(self, **kwargs) -> str:
        """渲染模板"""
        return self.template.format(**kwargs)


class RateLimiter:
    """速率限制器

    限制每小时的回复次数。
    """

    def __init__(self, max_per_hour: int = 8):
        self._max_per_hour = max_per_hour
        self._records: list[float] = []
        self._logger = logging.getLogger(__name__)

    def check(self) -> bool:
        """检查是否可以继续"""
        now = time.time()
        cutoff = now - 3600

        self._records = [r for r in self._records if r > cutoff]

        if len(self._records) >= self._max_per_hour:
            self._logger.warning(
                f"Rate limit reached: {len(self._records)}/{self._max_per_hour} per hour"
            )
            return False

        return True

    def record(self) -> None:
        """记录一次操作"""
        self._records.append(time.time())

    @property
    def remaining(self) -> int:
        """剩余次数"""
        now = time.time()
        cutoff = now - 3600
        current = len([r for r in self._records if r > cutoff])
        return max(0, self._max_per_hour - current)


class ReplyWhitelist:
    """回复白名单

    管理允许自动回复的应用列表。
    """

    DEFAULT_PACKAGES = [
        "com.tencent.mm",
        "com.tencent.mobileqq",
        "org.telegram.messenger",
        "com.whatsapp",
        "com.facebook.orca",
        "com.instagram.android",
        "com.twitter.android",
    ]

    def __init__(self):
        self._packages: set[str] = set(self.DEFAULT_PACKAGES)
        self._logger = logging.getLogger(__name__)

    def add(self, package_name: str) -> None:
        """添加包名"""
        self._packages.add(package_name)

    def remove(self, package_name: str) -> None:
        """移除包名"""
        self._packages.discard(package_name)

    def contains(self, package_name: str) -> bool:
        """检查是否在白名单中"""
        return package_name in self._packages

    def get_all(self) -> list[str]:
        """获取所有包名"""
        return list(self._packages)


class AutoReplyManager:
    """自动回复管理器

    管理通知的自动回复功能。
    移植自 OpenKiwi 的 AutoReplyManager。
    """

    DEFAULT_TEMPLATES = [
        ReplyTemplate(
            name="busy",
            template="我现在有点忙，稍后回复你。",
            keywords=["在吗", "在不在", "忙吗"],
        ),
        ReplyTemplate(
            name="driving",
            template="正在开车，不方便回复，稍后联系。",
            keywords=["在哪", "什么时候"],
        ),
        ReplyTemplate(
            name="meeting",
            template="正在开会，会后回复。",
            keywords=["急", "紧急", "urgent"],
        ),
    ]

    def __init__(self, adb_path: str = "adb"):
        self._adb_path = adb_path
        self._whitelist = ReplyWhitelist()
        self._rate_limiter = RateLimiter(max_per_hour=8)
        self._templates: list[ReplyTemplate] = list(self.DEFAULT_TEMPLATES)
        self._history: list[ReplyRecord] = []
        self._enabled = False
        self._callbacks: list[Callable[[ReplyRecord], None]] = []
        self._logger = logging.getLogger(__name__)

    @property
    def enabled(self) -> bool:
        """是否启用"""
        return self._enabled

    def enable(self) -> None:
        """启用自动回复"""
        self._enabled = True
        self._logger.info("Auto reply enabled")

    def disable(self) -> None:
        """禁用自动回复"""
        self._enabled = False
        self._logger.info("Auto reply disabled")

    @property
    def whitelist(self) -> ReplyWhitelist:
        """获取白名单"""
        return self._whitelist

    @property
    def rate_limiter(self) -> RateLimiter:
        """获取速率限制器"""
        return self._rate_limiter

    def add_template(self, template: ReplyTemplate) -> None:
        """添加回复模板"""
        self._templates.append(template)

    def remove_template(self, name: str) -> bool:
        """移除回复模板"""
        for i, t in enumerate(self._templates):
            if t.name == name:
                self._templates.pop(i)
                return True
        return False

    def add_callback(self, callback: Callable[[ReplyRecord], None]) -> None:
        """添加回调函数"""
        self._callbacks.append(callback)

    def can_reply(self, notification: Notification) -> tuple[bool, str]:
        """检查是否可以回复

        Returns:
            (can_reply, reason)
        """
        if not self._enabled:
            return False, "Auto reply is disabled"

        if not self._whitelist.contains(notification.package_name):
            return False, f"Package {notification.package_name} not in whitelist"

        if not self._rate_limiter.check():
            return False, "Rate limit reached"

        return True, "OK"

    def find_template(self, notification: Notification) -> ReplyTemplate | None:
        """查找匹配的模板"""
        text = f"{notification.title} {notification.text}"

        for template in self._templates:
            if template.matches(text, notification.package_name):
                return template

        return None

    async def reply(
        self,
        notification: Notification,
        reply_text: str | None = None
    ) -> ReplyRecord:
        """回复通知

        Args:
            notification: 通知对象
            reply_text: 回复文本（可选，默认使用模板）

        Returns:
            ReplyRecord: 回复记录
        """
        can_reply, reason = self.can_reply(notification)

        if not can_reply:
            record = ReplyRecord(
                notification_id=notification.id,
                package_name=notification.package_name,
                reply_text=reply_text or "",
                status=ReplyStatus.NOT_ALLOWED if "not in whitelist" in reason
                else ReplyStatus.RATE_LIMITED,
                error=reason,
            )
            self._history.append(record)
            return record

        if reply_text is None:
            template = self.find_template(notification)
            if template:
                reply_text = template.render()
            else:
                record = ReplyRecord(
                    notification_id=notification.id,
                    package_name=notification.package_name,
                    reply_text="",
                    status=ReplyStatus.NO_ACTION,
                    error="No matching template",
                )
                self._history.append(record)
                return record

        try:
            success = await self._send_reply(notification, reply_text)

            if success:
                self._rate_limiter.record()
                record = ReplyRecord(
                    notification_id=notification.id,
                    package_name=notification.package_name,
                    reply_text=reply_text,
                    status=ReplyStatus.SUCCESS,
                )
            else:
                record = ReplyRecord(
                    notification_id=notification.id,
                    package_name=notification.package_name,
                    reply_text=reply_text,
                    status=ReplyStatus.FAILED,
                    error="Failed to send reply",
                )

        except Exception as e:
            self._logger.error(f"Failed to send reply: {e}")
            record = ReplyRecord(
                notification_id=notification.id,
                package_name=notification.package_name,
                reply_text=reply_text,
                status=ReplyStatus.FAILED,
                error=str(e),
            )

        self._history.append(record)

        for callback in self._callbacks:
            try:
                callback(record)
            except Exception as e:
                self._logger.error(f"Callback error: {e}")

        return record

    async def _send_reply(self, notification: Notification, reply_text: str) -> bool:
        """发送回复

        使用 ADB 发送回复。实际实现需要根据具体的通知类型和 RemoteInput。
        """
        try:
            escaped_text = reply_text.replace(" ", "%s").replace("'", "\\'")

            result = subprocess.run(
                [
                    self._adb_path, "shell",
                    "am", "broadcast",
                    "-a", "android.intent.action.REPLY",
                    "--es", "android.text", escaped_text,
                    "--es", "package", notification.package_name,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            return result.returncode == 0

        except Exception as e:
            self._logger.error(f"Failed to send reply via ADB: {e}")
            return False

    def get_history(self, limit: int = 100) -> list[ReplyRecord]:
        """获取回复历史"""
        return self._history[-limit:]

    def clear_history(self) -> None:
        """清空回复历史"""
        self._history.clear()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total = len(self._history)
        success = sum(1 for r in self._history if r.status == ReplyStatus.SUCCESS)
        failed = sum(1 for r in self._history if r.status == ReplyStatus.FAILED)
        rate_limited = sum(1 for r in self._history if r.status == ReplyStatus.RATE_LIMITED)

        return {
            "enabled": self._enabled,
            "total_replies": total,
            "successful": success,
            "failed": failed,
            "rate_limited": rate_limited,
            "remaining": self._rate_limiter.remaining,
            "whitelist_count": len(self._whitelist.get_all()),
            "template_count": len(self._templates),
        }


auto_reply_manager = AutoReplyManager()
