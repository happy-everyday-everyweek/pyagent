"""
PyAgent 人类任务管理系统

提供为人类设计的任务管理功能，包括：
- 任务创建、更新、删除
- 任务分类管理
- 任务提醒和通知
- 任务统计和查询

与AI Todo系统的区别：
- AI Todo系统：为AI智能体设计的任务管理，支持三级分类（阶段/任务/步骤）
- 人类任务系统：为人类用户设计的任务管理，支持截止日期、提醒、分类等
"""

from .category import Category, CategoryManager, category_manager
from .manager import TaskManager, task_manager
from .notification import (
    Notification,
    NotificationService,
    NotificationType,
    notification_service,
)
from .task import HumanTask, Priority, SubTask, TaskStatus

__all__ = [
    "Category",
    "CategoryManager",
    "HumanTask",
    "Notification",
    "NotificationService",
    "NotificationType",
    "Priority",
    "SubTask",
    "TaskManager",
    "TaskStatus",
    "category_manager",
    "notification_service",
    "task_manager",
]
