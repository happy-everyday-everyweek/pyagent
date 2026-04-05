"""
PyAgent 执行模块核心 - 任务队列

管理异步任务的队列和状态。
"""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    task: str
    status: TaskStatus = TaskStatus.PENDING
    context: dict[str, Any] = field(default_factory=dict)
    result: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    callback: Callable | None = None


class TaskQueue:
    """任务队列"""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._queue: asyncio.Queue = asyncio.Queue()
        self._tasks: dict[str, TaskInfo] = {}
        self._lock = asyncio.Lock()

    async def add_task(
        self,
        task_id: str,
        task: str,
        context: dict[str, Any] | None = None,
        callback: Callable | None = None
    ) -> bool:
        """添加任务"""
        async with self._lock:
            if len(self._tasks) >= self.max_size:
                return False

            task_info = TaskInfo(
                task_id=task_id,
                task=task,
                context=context or {},
                callback=callback
            )

            self._tasks[task_id] = task_info
            await self._queue.put(task_id)

            return True

    def get_task(self, task_id: str) -> TaskInfo | None:
        """获取任务信息"""
        return self._tasks.get(task_id)

    def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: str = "",
        error: str = ""
    ) -> bool:
        """更新任务状态"""
        if task_id not in self._tasks:
            return False

        task_info = self._tasks[task_id]
        task_info.status = status

        if status == TaskStatus.RUNNING:
            task_info.started_at = time.time()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task_info.completed_at = time.time()

        if result:
            task_info.result = result
        if error:
            task_info.error = error

        return True

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        """获取任务状态"""
        task_info = self._tasks.get(task_id)
        if not task_info:
            return {
                "task_id": task_id,
                "status": "not_found",
                "error": "任务不存在"
            }

        return {
            "task_id": task_id,
            "task": task_info.task,
            "status": task_info.status.value,
            "result": task_info.result,
            "error": task_info.error,
            "created_at": task_info.created_at,
            "started_at": task_info.started_at,
            "completed_at": task_info.completed_at,
            "duration": (task_info.completed_at - task_info.started_at)
                       if task_info.started_at and task_info.completed_at else None
        }

    async def get_next_task(self) -> str | None:
        """获取下一个待处理任务"""
        try:
            task_id = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            return task_id
        except asyncio.TimeoutError:
            return None

    def get_pending_tasks(self) -> list[str]:
        """获取待处理任务列表"""
        return [
            task_id for task_id, info in self._tasks.items()
            if info.status == TaskStatus.PENDING
        ]

    def get_running_tasks(self) -> list[str]:
        """获取运行中任务列表"""
        return [
            task_id for task_id, info in self._tasks.items()
            if info.status == TaskStatus.RUNNING
        ]

    def get_completed_tasks(self) -> list[str]:
        """获取已完成任务列表"""
        return [
            task_id for task_id, info in self._tasks.items()
            if info.status == TaskStatus.COMPLETED
        ]

    def get_failed_tasks(self) -> list[str]:
        """获取失败任务列表"""
        return [
            task_id for task_id, info in self._tasks.items()
            if info.status == TaskStatus.FAILED
        ]

    def size(self) -> int:
        """获取队列大小"""
        return len(self._tasks)

    def clear_completed(self) -> int:
        """清理已完成任务"""
        completed_ids = self.get_completed_tasks() + self.get_failed_tasks()
        for task_id in completed_ids:
            del self._tasks[task_id]
        return len(completed_ids)

    def clear_all(self) -> None:
        """清空所有任务"""
        self._tasks.clear()
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
