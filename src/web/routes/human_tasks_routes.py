"""
PyAgent Web服务 - 人类任务管理API路由

提供人类任务管理的REST API接口。
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.human_tasks import (
    NotificationType,
    Priority,
    TaskStatus,
    category_manager,
    notification_service,
    task_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/human-tasks", tags=["human-tasks"])


class CreateTaskRequest(BaseModel):
    """创建任务请求"""
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: str | None = None
    reminder: str | None = None
    category: str = "default"
    tags: list[str] = []
    subtasks: list[str] = []
    attachments: list[str] = []


class UpdateTaskRequest(BaseModel):
    """更新任务请求"""
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    due_date: str | None = None
    reminder: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    attachments: list[str] | None = None


class CreateCategoryRequest(BaseModel):
    """创建分类请求"""
    name: str
    color: str = "#3498db"
    icon: str = ""
    description: str = ""


class UpdateCategoryRequest(BaseModel):
    """更新分类请求"""
    name: str | None = None
    color: str | None = None
    icon: str | None = None
    description: str | None = None


class AddSubtaskRequest(BaseModel):
    """添加子任务请求"""
    title: str


class ScheduleReminderRequest(BaseModel):
    """安排提醒请求"""
    remind_at: str
    custom_message: str | None = None


class SendNotificationRequest(BaseModel):
    """发送通知请求"""
    notification_type: str
    custom_message: str | None = None


@router.post("/tasks")
async def create_task(request: CreateTaskRequest) -> dict[str, Any]:
    """创建任务"""
    priority = Priority(request.priority)

    due_date = None
    if request.due_date:
        try:
            due_date = datetime.fromisoformat(request.due_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid due_date format")

    reminder = None
    if request.reminder:
        try:
            reminder = datetime.fromisoformat(request.reminder)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid reminder format")

    task = task_manager.create_task(
        title=request.title,
        description=request.description,
        priority=priority,
        due_date=due_date,
        reminder=reminder,
        category=request.category,
        tags=request.tags,
        subtasks=request.subtasks,
        attachments=request.attachments
    )

    return task.to_dict()


@router.get("/tasks")
async def list_tasks(
    status: str | None = None,
    category: str | None = None,
    priority: str | None = None
) -> list[dict[str, Any]]:
    """列出任务"""
    task_status = TaskStatus(status) if status else None
    task_priority = Priority(priority) if priority else None

    tasks = task_manager.list_tasks(
        status=task_status,
        category=category,
        priority=task_priority
    )

    return [t.to_dict() for t in tasks]


@router.get("/tasks/{task_id}")
async def get_task(task_id: str) -> dict[str, Any]:
    """获取任务详情"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.put("/tasks/{task_id}")
async def update_task(task_id: str, request: UpdateTaskRequest) -> dict[str, Any]:
    """更新任务"""
    priority = Priority(request.priority) if request.priority else None

    due_date = None
    if request.due_date:
        try:
            due_date = datetime.fromisoformat(request.due_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid due_date format")

    reminder = None
    if request.reminder:
        try:
            reminder = datetime.fromisoformat(request.reminder)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid reminder format")

    task = task_manager.update_task(
        task_id=task_id,
        title=request.title,
        description=request.description,
        priority=priority,
        due_date=due_date,
        reminder=reminder,
        category=request.category,
        tags=request.tags,
        attachments=request.attachments
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task.to_dict()


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str) -> dict[str, bool]:
    """删除任务"""
    success = task_manager.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}


@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str) -> dict[str, Any]:
    """完成任务"""
    task = task_manager.complete_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    notification_service.send_notification(task, NotificationType.COMPLETED)

    return task.to_dict()


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str) -> dict[str, Any]:
    """取消任务"""
    task = task_manager.cancel_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    notification_service.cancel_reminder(task_id)
    notification_service.send_notification(task, NotificationType.CANCELLED)

    return task.to_dict()


@router.post("/tasks/{task_id}/start")
async def start_task(task_id: str) -> dict[str, Any]:
    """开始任务"""
    task = task_manager.start_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.post("/tasks/{task_id}/subtasks")
async def add_subtask(task_id: str, request: AddSubtaskRequest) -> dict[str, Any]:
    """添加子任务"""
    task = task_manager.add_subtask(task_id, request.title)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.post("/tasks/{task_id}/subtasks/{subtask_id}/complete")
async def complete_subtask(task_id: str, subtask_id: str) -> dict[str, Any]:
    """完成子任务"""
    task = task_manager.complete_subtask(task_id, subtask_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task or subtask not found")
    return task.to_dict()


@router.delete("/tasks/{task_id}/subtasks/{subtask_id}")
async def remove_subtask(task_id: str, subtask_id: str) -> dict[str, Any]:
    """移除子任务"""
    task = task_manager.remove_subtask(task_id, subtask_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task or subtask not found")
    return task.to_dict()


@router.get("/tasks/search/{query}")
async def search_tasks(query: str) -> list[dict[str, Any]]:
    """搜索任务"""
    tasks = task_manager.search_tasks(query)
    return [t.to_dict() for t in tasks]


@router.get("/tasks/overdue")
async def get_overdue_tasks() -> list[dict[str, Any]]:
    """获取过期任务"""
    tasks = task_manager.get_overdue_tasks()
    return [t.to_dict() for t in tasks]


@router.get("/tasks/due-today")
async def get_tasks_due_today() -> list[dict[str, Any]]:
    """获取今天到期的任务"""
    tasks = task_manager.get_tasks_due_today()
    return [t.to_dict() for t in tasks]


@router.get("/statistics")
async def get_statistics() -> dict[str, Any]:
    """获取统计信息"""
    return task_manager.get_statistics()


@router.post("/categories")
async def create_category(request: CreateCategoryRequest) -> dict[str, Any]:
    """创建分类"""
    category = category_manager.create_category(
        name=request.name,
        color=request.color,
        icon=request.icon,
        description=request.description
    )
    return category.to_dict()


@router.get("/categories")
async def list_categories() -> list[dict[str, Any]]:
    """列出所有分类"""
    categories = category_manager.list_categories()
    return [c.to_dict() for c in categories]


@router.get("/categories/{category_id}")
async def get_category(category_id: str) -> dict[str, Any]:
    """获取分类详情"""
    category = category_manager.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category.to_dict()


@router.put("/categories/{category_id}")
async def update_category(category_id: str, request: UpdateCategoryRequest) -> dict[str, Any]:
    """更新分类"""
    category = category_manager.update_category(
        category_id=category_id,
        name=request.name,
        color=request.color,
        icon=request.icon,
        description=request.description
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category.to_dict()


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str) -> dict[str, bool]:
    """删除分类"""
    success = category_manager.delete_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"success": True}


@router.get("/categories/{category_id}/tasks")
async def get_tasks_by_category(category_id: str) -> list[dict[str, Any]]:
    """获取分类下的任务"""
    category = category_manager.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    tasks = task_manager.get_tasks_by_category(category.name)
    return [t.to_dict() for t in tasks]


@router.post("/tasks/{task_id}/reminders")
async def schedule_reminder(task_id: str, request: ScheduleReminderRequest) -> dict[str, Any]:
    """安排提醒"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        remind_at = datetime.fromisoformat(request.remind_at)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid remind_at format")

    notification = notification_service.schedule_reminder(
        task=task,
        remind_at=remind_at,
        custom_message=request.custom_message
    )

    return notification.to_dict()


@router.delete("/tasks/{task_id}/reminders")
async def cancel_reminder(task_id: str) -> dict[str, bool]:
    """取消提醒"""
    success = notification_service.cancel_reminder(task_id)
    return {"success": success}


@router.post("/tasks/{task_id}/notifications")
async def send_notification(task_id: str, request: SendNotificationRequest) -> dict[str, Any]:
    """发送通知"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        notification_type = NotificationType(request.notification_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid notification_type")

    notification = notification_service.send_notification(
        task=task,
        notification_type=notification_type,
        custom_message=request.custom_message
    )

    return notification.to_dict()


@router.get("/notifications/pending")
async def get_pending_notifications() -> list[dict[str, Any]]:
    """获取待发送的通知"""
    notifications = notification_service.get_pending_notifications()
    return [n.to_dict() for n in notifications]


@router.post("/notifications/check")
async def check_due_reminders() -> list[dict[str, Any]]:
    """检查并发送到期的提醒"""
    notifications = await notification_service.check_due_reminders()
    return [n.to_dict() for n in notifications]
