"""
PyAgent 人类任务管理系统 - 任务管理器

提供任务的创建、更新、删除、查询和统计功能。
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .task import HumanTask, Priority, TaskStatus


class TaskManager:
    """
    任务管理器
    
    管理人类任务的完整生命周期，包括：
    - 创建、更新、删除任务
    - 任务状态管理
    - 任务查询和搜索
    - 任务统计
    """
    
    def __init__(self, data_dir: str = "data/human_tasks"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.tasks: dict[str, HumanTask] = {}
        self._load_data()

    def _get_storage_file(self) -> Path:
        """获取存储文件路径"""
        return self.data_dir / "tasks.json"

    def _load_data(self) -> None:
        """加载数据"""
        file_path = self._get_storage_file()
        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("tasks", []):
                        task = HumanTask.from_dict(item)
                        self.tasks[task.task_id] = task
            except Exception:
                pass

    def _save_data(self) -> None:
        """保存数据"""
        file_path = self._get_storage_file()
        try:
            data = {
                "tasks": [t.to_dict() for t in self.tasks.values()],
                "updated_at": datetime.now().isoformat(),
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _generate_id(self, prefix: str = "task") -> str:
        """生成唯一ID"""
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: Priority = Priority.MEDIUM,
        due_date: Optional[datetime] = None,
        reminder: Optional[datetime] = None,
        category: str = "default",
        tags: Optional[list[str]] = None,
        subtasks: Optional[list[str]] = None,
        attachments: Optional[list[str]] = None
    ) -> HumanTask:
        """
        创建新任务
        
        Args:
            title: 任务标题
            description: 任务描述
            priority: 任务优先级
            due_date: 截止日期
            reminder: 提醒时间
            category: 任务分类
            tags: 标签列表
            subtasks: 子任务标题列表
            attachments: 附件列表
            
        Returns:
            创建的任务对象
        """
        task = HumanTask(
            task_id=self._generate_id("htask"),
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            reminder=reminder,
            category=category,
            tags=tags or [],
            attachments=attachments or []
        )
        
        if subtasks:
            for subtask_title in subtasks:
                task.add_subtask(subtask_title)
        
        self.tasks[task.task_id] = task
        self._save_data()
        
        return task

    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[Priority] = None,
        due_date: Optional[datetime] = None,
        reminder: Optional[datetime] = None,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        attachments: Optional[list[str]] = None
    ) -> Optional[HumanTask]:
        """
        更新任务
        
        Args:
            task_id: 任务ID
            title: 新标题
            description: 新描述
            priority: 新优先级
            due_date: 新截止日期
            reminder: 新提醒时间
            category: 新分类
            tags: 新标签列表
            attachments: 新附件列表
            
        Returns:
            更新后的任务对象，如果任务不存在则返回None
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
        if priority is not None:
            update_data["priority"] = priority
        if due_date is not None:
            update_data["due_date"] = due_date
        if reminder is not None:
            update_data["reminder"] = reminder
        if category is not None:
            update_data["category"] = category
        if tags is not None:
            update_data["tags"] = tags
        if attachments is not None:
            update_data["attachments"] = attachments
        
        task.update(**update_data)
        self._save_data()
        
        return task

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_data()
            return True
        return False

    def complete_task(self, task_id: str) -> Optional[HumanTask]:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            完成后的任务对象，如果任务不存在则返回None
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        task.mark_completed()
        self._save_data()
        
        return task

    def cancel_task(self, task_id: str) -> Optional[HumanTask]:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            取消后的任务对象，如果任务不存在则返回None
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        task.mark_cancelled()
        self._save_data()
        
        return task

    def start_task(self, task_id: str) -> Optional[HumanTask]:
        """
        开始任务（标记为进行中）
        
        Args:
            task_id: 任务ID
            
        Returns:
            开始后的任务对象，如果任务不存在则返回None
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        task.mark_in_progress()
        self._save_data()
        
        return task

    def get_task(self, task_id: str) -> Optional[HumanTask]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在则返回None
        """
        return self.tasks.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        category: Optional[str] = None,
        priority: Optional[Priority] = None
    ) -> list[HumanTask]:
        """
        列出任务（支持过滤）
        
        Args:
            status: 任务状态过滤
            category: 分类过滤
            priority: 优先级过滤
            
        Returns:
            任务列表
        """
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        if category:
            tasks = [t for t in tasks if t.category == category]
        
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        
        return sorted(tasks, key=lambda x: x.created_at, reverse=True)

    def search_tasks(self, query: str) -> list[HumanTask]:
        """
        搜索任务
        
        Args:
            query: 搜索关键词
            
        Returns:
            匹配的任务列表
        """
        query_lower = query.lower()
        results = []
        
        for task in self.tasks.values():
            if (
                query_lower in task.title.lower() or
                query_lower in task.description.lower() or
                query_lower in task.category.lower() or
                any(query_lower in tag.lower() for tag in task.tags)
            ):
                results.append(task)
        
        return sorted(results, key=lambda x: x.created_at, reverse=True)

    def get_overdue_tasks(self) -> list[HumanTask]:
        """
        获取过期任务
        
        Returns:
            过期任务列表
        """
        overdue = [t for t in self.tasks.values() if t.is_overdue()]
        return sorted(overdue, key=lambda x: x.due_date or datetime.max)

    def get_tasks_due_today(self) -> list[HumanTask]:
        """
        获取今天到期的任务
        
        Returns:
            今天到期的任务列表
        """
        due_today = [t for t in self.tasks.values() if t.is_due_today()]
        return sorted(due_today, key=lambda x: x.due_date or datetime.max)

    def get_tasks_by_category(self, category: str) -> list[HumanTask]:
        """
        获取指定分类的任务
        
        Args:
            category: 分类名称
            
        Returns:
            该分类的任务列表
        """
        tasks = [t for t in self.tasks.values() if t.category == category]
        return sorted(tasks, key=lambda x: x.created_at, reverse=True)

    def get_statistics(self) -> dict[str, Any]:
        """
        获取任务统计信息
        
        Returns:
            统计信息字典
        """
        total = len(self.tasks)
        
        status_counts = {
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "cancelled": 0
        }
        
        priority_counts = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "urgent": 0
        }
        
        overdue_count = 0
        due_today_count = 0
        
        for task in self.tasks.values():
            status_counts[task.status.value] += 1
            priority_counts[task.priority.value] += 1
            
            if task.is_overdue():
                overdue_count += 1
            if task.is_due_today():
                due_today_count += 1
        
        return {
            "total_tasks": total,
            "status_distribution": status_counts,
            "priority_distribution": priority_counts,
            "overdue_tasks": overdue_count,
            "due_today_tasks": due_today_count,
            "completion_rate": status_counts["completed"] / max(total, 1) * 100,
        }

    def add_subtask(self, task_id: str, title: str) -> Optional[HumanTask]:
        """
        为任务添加子任务
        
        Args:
            task_id: 任务ID
            title: 子任务标题
            
        Returns:
            更新后的任务对象，如果任务不存在则返回None
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        task.add_subtask(title)
        self._save_data()
        
        return task

    def complete_subtask(self, task_id: str, subtask_id: str) -> Optional[HumanTask]:
        """
        完成子任务
        
        Args:
            task_id: 任务ID
            subtask_id: 子任务ID
            
        Returns:
            更新后的任务对象，如果任务或子任务不存在则返回None
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        if task.complete_subtask(subtask_id):
            self._save_data()
            return task
        
        return None

    def remove_subtask(self, task_id: str, subtask_id: str) -> Optional[HumanTask]:
        """
        移除子任务
        
        Args:
            task_id: 任务ID
            subtask_id: 子任务ID
            
        Returns:
            更新后的任务对象，如果任务或子任务不存在则返回None
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        if task.remove_subtask(subtask_id):
            self._save_data()
            return task
        
        return None


task_manager = TaskManager()
