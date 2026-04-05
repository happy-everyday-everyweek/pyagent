"""
PyAgent 人类任务管理系统 - 通知服务

提供任务提醒和通知功能。
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from .task import HumanTask

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """通知类型"""
    REMINDER = "reminder"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Notification:
    """
    通知对象
    
    属性：
    - id: 通知ID
    - task_id: 关联的任务ID
    - type: 通知类型
    - title: 通知标题
    - message: 通知消息
    - scheduled_at: 计划发送时间
    - sent_at: 实际发送时间
    - sent: 是否已发送
    """
    id: str = field(default_factory=lambda: str(id(Notification)))
    task_id: str = ""
    type: NotificationType = NotificationType.REMINDER
    title: str = ""
    message: str = ""
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    sent: bool = False

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "sent": self.sent,
        }


class NotificationService:
    """
    通知服务
    
    提供任务提醒和通知功能：
    - 安排提醒
    - 取消提醒
    - 发送通知
    - 检查到期提醒
    """
    
    def __init__(self, data_dir: str = "data/human_tasks"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.notifications: dict[str, Notification] = {}
        self._handlers: list[Callable[[Notification], None]] = []
        self._check_task: Optional[asyncio.Task] = None
        self._running = False
        
        self._load_data()

    def _get_storage_file(self) -> Path:
        """获取存储文件路径"""
        return self.data_dir / "notifications.json"

    def _load_data(self) -> None:
        """加载数据"""
        file_path = self._get_storage_file()
        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("notifications", []):
                        notification = Notification(
                            id=item.get("id", ""),
                            task_id=item.get("task_id", ""),
                            type=NotificationType(item.get("type", "reminder")),
                            title=item.get("title", ""),
                            message=item.get("message", ""),
                            scheduled_at=datetime.fromisoformat(item["scheduled_at"]) if item.get("scheduled_at") else None,
                            sent_at=datetime.fromisoformat(item["sent_at"]) if item.get("sent_at") else None,
                            sent=item.get("sent", False),
                        )
                        if not notification.sent:
                            self.notifications[notification.id] = notification
            except Exception:
                pass

    def _save_data(self) -> None:
        """保存数据"""
        file_path = self._get_storage_file()
        try:
            data = {
                "notifications": [n.to_dict() for n in self.notifications.values()],
                "updated_at": datetime.now().isoformat(),
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def register_handler(self, handler: Callable[[Notification], None]) -> None:
        """
        注册通知处理器
        
        Args:
            handler: 通知处理函数
        """
        self._handlers.append(handler)

    def unregister_handler(self, handler: Callable[[Notification], None]) -> None:
        """
        注销通知处理器
        
        Args:
            handler: 通知处理函数
        """
        if handler in self._handlers:
            self._handlers.remove(handler)

    def schedule_reminder(
        self,
        task: HumanTask,
        remind_at: datetime,
        custom_message: Optional[str] = None
    ) -> Notification:
        """
        安排提醒
        
        Args:
            task: 关联的任务
            remind_at: 提醒时间
            custom_message: 自定义消息
            
        Returns:
            创建的通知对象
        """
        notification = Notification(
            task_id=task.task_id,
            type=NotificationType.REMINDER,
            title=f"任务提醒: {task.title}",
            message=custom_message or f"任务 '{task.title}' 将在指定时间到期",
            scheduled_at=remind_at
        )
        
        self.notifications[notification.id] = notification
        self._save_data()
        
        logger.info(f"Scheduled reminder for task {task.task_id} at {remind_at}")
        
        return notification

    def cancel_reminder(self, task_id: str) -> bool:
        """
        取消提醒
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否取消成功
        """
        to_remove = [
            nid for nid, notif in self.notifications.items()
            if notif.task_id == task_id and not notif.sent
        ]
        
        for nid in to_remove:
            del self.notifications[nid]
        
        if to_remove:
            self._save_data()
            logger.info(f"Cancelled {len(to_remove)} reminders for task {task_id}")
        
        return len(to_remove) > 0

    def send_notification(
        self,
        task: HumanTask,
        notification_type: NotificationType,
        custom_message: Optional[str] = None
    ) -> Notification:
        """
        发送通知
        
        Args:
            task: 关联的任务
            notification_type: 通知类型
            custom_message: 自定义消息
            
        Returns:
            创建的通知对象
        """
        title_map = {
            NotificationType.REMINDER: f"任务提醒: {task.title}",
            NotificationType.DUE_SOON: f"任务即将到期: {task.title}",
            NotificationType.OVERDUE: f"任务已过期: {task.title}",
            NotificationType.COMPLETED: f"任务已完成: {task.title}",
            NotificationType.CANCELLED: f"任务已取消: {task.title}",
        }
        
        message_map = {
            NotificationType.REMINDER: f"任务 '{task.title}' 需要您的关注",
            NotificationType.DUE_SOON: f"任务 '{task.title}' 即将到期，请及时处理",
            NotificationType.OVERDUE: f"任务 '{task.title}' 已过期，请尽快处理",
            NotificationType.COMPLETED: f"任务 '{task.title}' 已完成",
            NotificationType.CANCELLED: f"任务 '{task.title}' 已取消",
        }
        
        notification = Notification(
            task_id=task.task_id,
            type=notification_type,
            title=title_map.get(notification_type, task.title),
            message=custom_message or message_map.get(notification_type, ""),
            scheduled_at=datetime.now(),
            sent_at=datetime.now(),
            sent=True
        )
        
        self._deliver_notification(notification)
        
        logger.info(f"Sent {notification_type.value} notification for task {task.task_id}")
        
        return notification

    def _deliver_notification(self, notification: Notification) -> None:
        """
        投递通知
        
        Args:
            notification: 通知对象
        """
        for handler in self._handlers:
            try:
                handler(notification)
            except Exception as e:
                logger.error(f"Error in notification handler: {e}")

    async def check_due_reminders(self) -> list[Notification]:
        """
        检查并发送到期的提醒
        
        Returns:
            已发送的通知列表
        """
        now = datetime.now()
        due_notifications = []
        
        for notification in list(self.notifications.values()):
            if notification.sent:
                continue
            
            if notification.scheduled_at and notification.scheduled_at <= now:
                notification.sent = True
                notification.sent_at = now
                
                self._deliver_notification(notification)
                due_notifications.append(notification)
                
                logger.info(f"Sent due reminder for task {notification.task_id}")
        
        if due_notifications:
            self._save_data()
        
        return due_notifications

    async def start_background_check(self, interval: int = 60) -> None:
        """
        启动后台检查任务
        
        Args:
            interval: 检查间隔（秒）
        """
        if self._running:
            return
        
        self._running = True
        
        async def check_loop():
            while self._running:
                try:
                    await self.check_due_reminders()
                except Exception as e:
                    logger.error(f"Error in reminder check: {e}")
                
                await asyncio.sleep(interval)
        
        self._check_task = asyncio.create_task(check_loop())
        logger.info(f"Started background reminder check with interval {interval}s")

    async def stop_background_check(self) -> None:
        """停止后台检查任务"""
        self._running = False
        
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
            
            self._check_task = None
        
        logger.info("Stopped background reminder check")

    def get_pending_notifications(self) -> list[Notification]:
        """
        获取待发送的通知
        
        Returns:
            待发送的通知列表
        """
        return [n for n in self.notifications.values() if not n.sent]

    def get_task_notifications(self, task_id: str) -> list[Notification]:
        """
        获取任务的所有通知
        
        Args:
            task_id: 任务ID
            
        Returns:
            通知列表
        """
        return [n for n in self.notifications.values() if n.task_id == task_id]

    def clear_sent_notifications(self, older_than: Optional[timedelta] = None) -> int:
        """
        清理已发送的通知
        
        Args:
            older_than: 清理多少时间前的通知
            
        Returns:
            清理的通知数量
        """
        to_remove = []
        
        for nid, notification in self.notifications.items():
            if not notification.sent:
                continue
            
            if older_than and notification.sent_at:
                if datetime.now() - notification.sent_at < older_than:
                    continue
            
            to_remove.append(nid)
        
        for nid in to_remove:
            del self.notifications[nid]
        
        if to_remove:
            self._save_data()
        
        return len(to_remove)


notification_service = NotificationService()
