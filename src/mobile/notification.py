"""
PyAgent 移动端模块 - 通知读取

提供移动设备通知的读取和监听功能。
v0.8.0: 新增移动端支持
"""

import asyncio
import logging
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class NotificationPriority(Enum):
    """通知优先级"""
    LOW = "low"
    DEFAULT = "default"
    HIGH = "high"
    MAX = "max"


class NotificationCategory(Enum):
    """通知类别"""
    MESSAGE = "message"
    CALL = "call"
    EMAIL = "email"
    SOCIAL = "social"
    SYSTEM = "system"
    OTHER = "other"


@dataclass
class Notification:
    """通知数据结构"""
    id: str
    package_name: str
    title: str
    text: str
    timestamp: datetime
    priority: NotificationPriority = NotificationPriority.DEFAULT
    category: NotificationCategory = NotificationCategory.OTHER
    is_removable: bool = True
    is_ongoing: bool = False
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "package_name": self.package_name,
            "title": self.title,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "category": self.category.value,
            "is_removable": self.is_removable,
            "is_ongoing": self.is_ongoing,
            "extras": self.extras,
        }


@dataclass
class NotificationFilter:
    """通知过滤器"""
    packages: list[str] | None = None
    categories: list[NotificationCategory] | None = None
    priorities: list[NotificationPriority] | None = None
    exclude_ongoing: bool = True
    exclude_system: bool = False

    def matches(self, notification: Notification) -> bool:
        """检查通知是否匹配过滤器"""
        if self.packages and notification.package_name not in self.packages:
            return False

        if self.categories and notification.category not in self.categories:
            return False

        if self.priorities and notification.priority not in self.priorities:
            return False

        if self.exclude_ongoing and notification.is_ongoing:
            return False

        return True


class NotificationReader:
    """通知读取器

    提供读取移动设备通知的功能，支持通过ADB或NotificationListenerService。
    """

    def __init__(self, adb_path: str = "adb"):
        self._adb_path = adb_path
        self._notifications: list[Notification] = []
        self._last_update: datetime | None = None
        self._logger = logging.getLogger(__name__)

    async def get_notifications(
        self,
        filter_obj: NotificationFilter | None = None
    ) -> list[dict[str, Any]]:
        """获取所有通知

        Args:
            filter_obj: 通知过滤器

        Returns:
            通知列表
        """
        try:
            raw_notifications = await self._fetch_notifications()

            notifications = []
            for raw in raw_notifications:
                notification = self._parse_notification(raw)

                if notification:
                    if filter_obj is None or filter_obj.matches(notification):
                        notifications.append(notification)

            self._notifications = notifications
            self._last_update = datetime.now()

            return [n.to_dict() for n in notifications]

        except Exception as e:
            self._logger.error(f"Failed to get notifications: {e}")
            return []

    async def _fetch_notifications(self) -> list[dict[str, Any]]:
        """从设备获取通知数据"""
        try:
            script = (
                "service call notification 1 "
                "| toybox sed -e 's/\\(\\s*\\)/\\n/g' "
                "| toybox grep -E 'NotificationRecord|android'"
            )

            result = subprocess.run(
                [self._adb_path, "shell", script],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self._logger.warning(f"Failed to fetch notifications: {result.stderr}")
                return []

            return self._parse_notification_output(result.stdout)

        except Exception as e:
            self._logger.error(f"Error fetching notifications: {e}")
            return []

    def _parse_notification_output(self, output: str) -> list[dict[str, Any]]:
        """解析通知输出"""
        notifications = []

        try:
            result = subprocess.run(
                [
                    self._adb_path, "shell",
                    "dumpsys notification --noredact"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                current_notification = {}
                lines = result.stdout.splitlines()

                for line in lines:
                    line = line.strip()

                    if "NotificationRecord" in line:
                        if current_notification:
                            notifications.append(current_notification)
                        current_notification = {}

                    elif "pkg=" in line:
                        pkg_start = line.find("pkg=") + 4
                        pkg_end = line.find(" ", pkg_start)
                        if pkg_end == -1:
                            pkg_end = len(line)
                        current_notification["package_name"] = line[pkg_start:pkg_end]

                    elif "id=" in line and "notification" not in current_notification:
                        id_start = line.find("id=") + 3
                        id_end = line.find(" ", id_start)
                        if id_end == -1:
                            id_end = len(line)
                        current_notification["id"] = line[id_start:id_end]

                    elif "android.title=" in line:
                        title_start = line.find("android.title=") + 14
                        current_notification["title"] = line[title_start:].strip('", ')

                    elif "android.text=" in line:
                        text_start = line.find("android.text=") + 13
                        current_notification["text"] = line[text_start:].strip('", ')

                if current_notification:
                    notifications.append(current_notification)

        except Exception as e:
            self._logger.error(f"Error parsing notification output: {e}")

        return notifications

    def _parse_notification(self, raw: dict[str, Any]) -> Notification | None:
        """解析单个通知"""
        try:
            package_name = raw.get("package_name", "")
            if not package_name:
                return None

            notification_id = raw.get("id", "unknown")
            title = raw.get("title", "")
            text = raw.get("text", "")

            category = self._detect_category(package_name)
            priority = self._detect_priority(raw)

            return Notification(
                id=f"{package_name}_{notification_id}",
                package_name=package_name,
                title=title,
                text=text,
                timestamp=datetime.now(),
                priority=priority,
                category=category,
                is_removable=raw.get("flags", 0) & 0x00000010 == 0,
                is_ongoing=raw.get("flags", 0) & 0x00000002 != 0,
                extras=raw,
            )

        except Exception as e:
            self._logger.error(f"Error parsing notification: {e}")
            return None

    def _detect_category(self, package_name: str) -> NotificationCategory:
        """根据包名检测通知类别"""
        package_lower = package_name.lower()

        if any(app in package_lower for app in ["sms", "mms", "message", "messenger"]):
            return NotificationCategory.MESSAGE

        if any(app in package_lower for app in ["phone", "dialer", "call"]):
            return NotificationCategory.CALL

        if any(app in package_lower for app in ["email", "mail", "gmail"]):
            return NotificationCategory.EMAIL

        if any(app in package_lower for app in ["whatsapp", "telegram", "wechat", "qq", "facebook", "twitter", "instagram"]):
            return NotificationCategory.SOCIAL

        if any(app in package_lower for app in ["system", "android", "settings"]):
            return NotificationCategory.SYSTEM

        return NotificationCategory.OTHER

    def _detect_priority(self, raw: dict[str, Any]) -> NotificationPriority:
        """检测通知优先级"""
        priority = raw.get("priority", 0)

        if priority >= 2:
            return NotificationPriority.MAX
        if priority >= 1:
            return NotificationPriority.HIGH
        if priority <= -2:
            return NotificationPriority.LOW
        return NotificationPriority.DEFAULT

    async def get_notification_count(self) -> int:
        """获取通知数量"""
        notifications = await self.get_notifications()
        return len(notifications)

    async def clear_notification(self, notification_id: str) -> bool:
        """清除指定通知

        Args:
            notification_id: 通知ID

        Returns:
            是否成功清除
        """
        try:
            parts = notification_id.split("_", 1)
            if len(parts) != 2:
                return False

            package_name, notif_id = parts

            result = subprocess.run(
                [
                    self._adb_path, "shell",
                    "service call notification 10",
                    "s16", package_name,
                    "i32", notif_id
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            return result.returncode == 0

        except Exception as e:
            self._logger.error(f"Failed to clear notification: {e}")
            return False

    async def clear_all_notifications(self) -> bool:
        """清除所有通知"""
        try:
            result = subprocess.run(
                [self._adb_path, "shell", "service call notification 1"],
                capture_output=True,
                text=True,
                timeout=10
            )

            return result.returncode == 0

        except Exception as e:
            self._logger.error(f"Failed to clear all notifications: {e}")
            return False


class NotificationListener:
    """通知监听器

    提供实时监听新通知的功能。
    """

    def __init__(
        self,
        reader: NotificationReader | None = None,
        adb_path: str = "adb"
    ):
        self._reader = reader or NotificationReader(adb_path)
        self._adb_path = adb_path
        self._running = False
        self._callbacks: list[Callable[[Notification], None]] = []
        self._seen_ids: set[str] = set()
        self._logger = logging.getLogger(__name__)

    def add_callback(self, callback: Callable[[Notification], None]) -> None:
        """添加通知回调函数"""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[Notification], None]) -> None:
        """移除通知回调函数"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def listen(
        self,
        interval: float = 5.0,
        filter_obj: NotificationFilter | None = None
    ) -> None:
        """开始监听新通知

        Args:
            interval: 检查间隔（秒）
            filter_obj: 通知过滤器
        """
        self._running = True
        self._logger.info("Starting notification listener...")

        notifications = await self._reader.get_notifications(filter_obj)
        self._seen_ids = {n["id"] for n in notifications}

        while self._running:
            try:
                await asyncio.sleep(interval)

                notifications = await self._reader.get_notifications(filter_obj)
                current_ids = {n["id"] for n in notifications}

                new_ids = current_ids - self._seen_ids

                for notif_dict in notifications:
                    if notif_dict["id"] in new_ids:
                        notification = Notification(
                            id=notif_dict["id"],
                            package_name=notif_dict["package_name"],
                            title=notif_dict["title"],
                            text=notif_dict["text"],
                            timestamp=datetime.fromisoformat(notif_dict["timestamp"]),
                            priority=NotificationPriority(notif_dict["priority"]),
                            category=NotificationCategory(notif_dict["category"]),
                            is_removable=notif_dict["is_removable"],
                            is_ongoing=notif_dict["is_ongoing"],
                            extras=notif_dict["extras"],
                        )

                        for callback in self._callbacks:
                            try:
                                callback(notification)
                            except Exception as e:
                                self._logger.error(f"Callback error: {e}")

                self._seen_ids = current_ids

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Listener error: {e}")
                await asyncio.sleep(interval)

        self._logger.info("Notification listener stopped")

    def stop(self) -> None:
        """停止监听"""
        self._running = False

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running
