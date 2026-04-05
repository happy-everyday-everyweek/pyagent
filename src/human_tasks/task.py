"""
PyAgent 人类任务管理系统 - 任务数据模型

提供人类任务的数据结构和状态管理。
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Priority(Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class SubTask:
    """子任务"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "completed": self.completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SubTask":
        """从字典创建子任务"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", ""),
            completed=data.get("completed", False),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )


@dataclass
class HumanTask:
    """
    人类任务数据模型
    
    表示一个为人类设计的任务，包含：
    - 基本信息（标题、描述、分类）
    - 状态和优先级
    - 时间管理（截止日期、提醒）
    - 子任务和附件
    - 标签系统
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    due_date: Optional[datetime] = None
    reminder: Optional[datetime] = None
    category: str = "default"
    tags: list[str] = field(default_factory=list)
    subtasks: list[SubTask] = field(default_factory=list)
    attachments: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def is_overdue(self) -> bool:
        """检查任务是否过期"""
        if self.due_date and self.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return datetime.now() > self.due_date
        return False

    def is_due_today(self) -> bool:
        """检查任务是否今天到期"""
        if self.due_date:
            today = datetime.now().date()
            return self.due_date.date() == today
        return False

    def is_completed(self) -> bool:
        """检查任务是否已完成"""
        return self.status == TaskStatus.COMPLETED

    def is_cancelled(self) -> bool:
        """检查任务是否已取消"""
        return self.status == TaskStatus.CANCELLED

    def is_pending(self) -> bool:
        """检查任务是否待处理"""
        return self.status == TaskStatus.PENDING

    def is_in_progress(self) -> bool:
        """检查任务是否进行中"""
        return self.status == TaskStatus.IN_PROGRESS

    def get_progress(self) -> float:
        """获取任务进度（基于子任务完成情况）"""
        if not self.subtasks:
            if self.status == TaskStatus.COMPLETED:
                return 100.0
            elif self.status == TaskStatus.IN_PROGRESS:
                return 50.0
            return 0.0
        
        completed = sum(1 for st in self.subtasks if st.completed)
        return (completed / len(self.subtasks)) * 100.0

    def complete_subtask(self, subtask_id: str) -> bool:
        """完成子任务"""
        for subtask in self.subtasks:
            if subtask.id == subtask_id:
                subtask.completed = True
                subtask.completed_at = datetime.now()
                self.updated_at = datetime.now()
                return True
        return False

    def add_subtask(self, title: str) -> SubTask:
        """添加子任务"""
        subtask = SubTask(title=title)
        self.subtasks.append(subtask)
        self.updated_at = datetime.now()
        return subtask

    def remove_subtask(self, subtask_id: str) -> bool:
        """移除子任务"""
        for i, subtask in enumerate(self.subtasks):
            if subtask.id == subtask_id:
                self.subtasks.pop(i)
                self.updated_at = datetime.now()
                return True
        return False

    def mark_completed(self) -> None:
        """标记任务为已完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
        for subtask in self.subtasks:
            if not subtask.completed:
                subtask.completed = True
                subtask.completed_at = datetime.now()

    def mark_cancelled(self) -> None:
        """标记任务为已取消"""
        self.status = TaskStatus.CANCELLED
        self.updated_at = datetime.now()

    def mark_in_progress(self) -> None:
        """标记任务为进行中"""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now()

    def update(self, **kwargs: Any) -> None:
        """更新任务属性"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "reminder": self.reminder.isoformat() if self.reminder else None,
            "category": self.category,
            "tags": self.tags,
            "subtasks": [st.to_dict() for st in self.subtasks],
            "attachments": self.attachments,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.get_progress(),
            "is_overdue": self.is_overdue(),
            "is_due_today": self.is_due_today(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HumanTask":
        """从字典创建任务"""
        subtasks = [SubTask.from_dict(st) for st in data.get("subtasks", [])]
        
        return cls(
            task_id=data.get("task_id", str(uuid.uuid4())),
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=TaskStatus(data.get("status", "pending")),
            priority=Priority(data.get("priority", "medium")),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            reminder=datetime.fromisoformat(data["reminder"]) if data.get("reminder") else None,
            category=data.get("category", "default"),
            tags=data.get("tags", []),
            subtasks=subtasks,
            attachments=data.get("attachments", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )
