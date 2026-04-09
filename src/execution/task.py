"""
PyAgent 执行模块 - 任务定义

提供任务的标准化定义和状态管理。
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(Enum):
    """任务执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskState(Enum):
    """任务运行状态
    
    ACTIVE: 活跃状态（默认），任务正常运行
    PAUSED: 暂停状态，任务暂停执行
    ERROR: 异常状态，多次重试后仍无法完成
    WAITING: 等待状态，等待用户操作
    """
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    WAITING = "waiting"


class WaitingType(Enum):
    """等待用户操作类型"""
    CONFIRM = "confirm"    # 须您确认
    ASSIST = "assist"      # 须您协助


@dataclass
class Task:
    """
    任务定义
    
    表示一个可执行的任务单元，包含：
    - 唯一标识符
    - 任务提示词
    - 执行上下文
    - 当前状态（执行状态和运行状态）
    - 执行结果
    - 进度信息
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    state: TaskState = TaskState.ACTIVE
    result: Any | None = None
    error: str | None = None
    priority: int = 0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    progress: float = 0.0
    retry_count: int = 0
    max_retries: int = 5
    waiting_type: WaitingType | None = None
    waiting_message: str | None = None
    _state_change_callbacks: list = field(default_factory=list, repr=False)

    def is_pending(self) -> bool:
        """检查任务是否待执行"""
        return self.status == TaskStatus.PENDING

    def is_running(self) -> bool:
        """检查任务是否正在执行"""
        return self.status == TaskStatus.RUNNING

    def is_completed(self) -> bool:
        """检查任务是否已完成"""
        return self.status == TaskStatus.COMPLETED

    def is_failed(self) -> bool:
        """检查任务是否失败"""
        return self.status == TaskStatus.FAILED

    def is_cancelled(self) -> bool:
        """检查任务是否已取消"""
        return self.status == TaskStatus.CANCELLED

    def is_active(self) -> bool:
        """检查任务是否活跃"""
        return self.state == TaskState.ACTIVE

    def is_paused(self) -> bool:
        """检查任务是否暂停"""
        return self.state == TaskState.PAUSED

    def is_error(self) -> bool:
        """检查任务是否异常"""
        return self.state == TaskState.ERROR

    def is_waiting(self) -> bool:
        """检查任务是否等待用户操作"""
        return self.state == TaskState.WAITING

    def mark_running(self) -> None:
        """标记任务为运行中"""
        self.status = TaskStatus.RUNNING

    def mark_completed(self, result: Any = None) -> None:
        """标记任务为已完成"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.progress = 100.0

    def mark_failed(self, error: str) -> None:
        """标记任务为失败"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            self._set_state(TaskState.ERROR)

    def mark_cancelled(self) -> None:
        """标记任务为已取消"""
        self.status = TaskStatus.CANCELLED

    def pause(self) -> None:
        """暂停任务"""
        self._set_state(TaskState.PAUSED)

    def resume(self) -> None:
        """恢复任务"""
        if self.state == TaskState.PAUSED:
            self._set_state(TaskState.ACTIVE)

    def mark_error(self) -> None:
        """标记任务为异常"""
        self._set_state(TaskState.ERROR)

    def wait_for_user(self, waiting_type: WaitingType, message: str = None) -> None:
        """等待用户操作"""
        self.waiting_type = waiting_type
        self.waiting_message = message
        self._set_state(TaskState.WAITING)

    def user_responded(self) -> None:
        """用户已响应，恢复活跃状态"""
        self.waiting_type = None
        self.waiting_message = None
        self._set_state(TaskState.ACTIVE)

    def set_progress(self, progress: float) -> None:
        """设置进度（0-100）"""
        self.progress = max(0.0, min(100.0, progress))

    def get_display_status(self) -> str:
        """获取显示状态文本"""
        if self.status == TaskStatus.COMPLETED:
            return "执行｜完成"
        if self.status == TaskStatus.FAILED:
            return "执行｜失败"
        if self.state == TaskState.PAUSED:
            return "执行｜已暂停"
        if self.state == TaskState.ERROR:
            return "执行｜异常"
        if self.state == TaskState.WAITING:
            if self.waiting_type == WaitingType.CONFIRM:
                return "执行｜须您确认"
            if self.waiting_type == WaitingType.ASSIST:
                return "执行｜须您协助"
            return "执行｜等待中"
        if self.status == TaskStatus.RUNNING:
            if self.progress > 0:
                return f"执行｜{int(self.progress)}%"
            return "执行｜规划中"
        return "执行｜待处理"

    def on_state_change(self, callback) -> None:
        """注册状态变更回调"""
        self._state_change_callbacks.append(callback)

    def _set_state(self, new_state: TaskState) -> None:
        """设置状态并触发回调"""
        old_state = self.state
        self.state = new_state
        for callback in self._state_change_callbacks:
            try:
                callback(self, old_state, new_state)
            except Exception:
                pass

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "prompt": self.prompt,
            "context": self.context,
            "status": self.status.value,
            "state": self.state.value,
            "result": self.result,
            "error": self.error,
            "priority": self.priority,
            "tags": self.tags,
            "metadata": self.metadata,
            "progress": self.progress,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "waiting_type": self.waiting_type.value if self.waiting_type else None,
            "waiting_message": self.waiting_message,
            "display_status": self.get_display_status()
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """从字典创建任务"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            prompt=data.get("prompt", ""),
            context=data.get("context", {}),
            status=TaskStatus(data.get("status", "pending")),
            state=TaskState(data.get("state", "active")),
            result=data.get("result"),
            error=data.get("error"),
            priority=data.get("priority", 0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            progress=data.get("progress", 0.0),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 5),
            waiting_type=WaitingType(data["waiting_type"]) if data.get("waiting_type") else None,
            waiting_message=data.get("waiting_message")
        )


@dataclass
class TaskResult:
    """
    任务执行结果
    
    封装任务执行的结果数据。
    """
    success: bool
    data: Any = None
    error: str | None = None
    duration: float = 0.0
    steps: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "duration": self.duration,
            "steps": self.steps,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskResult":
        """从字典创建结果"""
        return cls(
            success=data.get("success", False),
            data=data.get("data"),
            error=data.get("error"),
            duration=data.get("duration", 0.0),
            steps=data.get("steps", []),
            metadata=data.get("metadata", {})
        )
