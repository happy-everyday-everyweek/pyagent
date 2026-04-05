"""
PyAgent AI原生Todo列表系统

实现三级分类的任务管理：
- 阶段（Phase）：最高级别，代表一个大的工作阶段
- 任务（Task）：中间级别，代表具体的工作任务
- 步骤（Step）：最低级别，代表具体的执行步骤

特点：
- 每完成一个步骤，自动更新任务列表
- 每个任务自动创建验收文档
- 每完成一个阶段，进行2-5轮反思
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TodoStatus(Enum):
    """Todo状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class TodoPriority(Enum):
    """Todo优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TodoLevel(Enum):
    """Todo级别"""
    PHASE = "phase"
    TASK = "task"
    STEP = "step"


@dataclass
class VerificationDocument:
    """验收文档"""
    id: str
    task_id: str
    title: str
    description: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    verification_results: list[str] = field(default_factory=list)
    is_verified: bool = False
    verified_at: float | None = None
    verified_by: str = "system"
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now().timestamp())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "verification_results": self.verification_results,
            "is_verified": self.is_verified,
            "verified_at": self.verified_at,
            "verified_by": self.verified_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VerificationDocument":
        return cls(
            id=data["id"],
            task_id=data["task_id"],
            title=data["title"],
            description=data.get("description", ""),
            acceptance_criteria=data.get("acceptance_criteria", []),
            verification_results=data.get("verification_results", []),
            is_verified=data.get("is_verified", False),
            verified_at=data.get("verified_at"),
            verified_by=data.get("verified_by", "system"),
            created_at=data.get("created_at", datetime.now().timestamp()),
            updated_at=data.get("updated_at", datetime.now().timestamp()),
        )


@dataclass
class ReflectionResult:
    """反思结果"""
    id: str
    phase_id: str
    round_number: int
    content: str
    insights: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "phase_id": self.phase_id,
            "round_number": self.round_number,
            "content": self.content,
            "insights": self.insights,
            "improvements": self.improvements,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReflectionResult":
        return cls(
            id=data["id"],
            phase_id=data["phase_id"],
            round_number=data["round_number"],
            content=data["content"],
            insights=data.get("insights", []),
            improvements=data.get("improvements", []),
            created_at=data.get("created_at", datetime.now().timestamp()),
        )


@dataclass
class TodoStep:
    """步骤"""
    id: str
    task_id: str
    content: str
    status: TodoStatus = TodoStatus.PENDING
    priority: TodoPriority = TodoPriority.MEDIUM
    order: int = 0
    estimated_time: int | None = None
    actual_time: int | None = None
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    started_at: float | None = None
    completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "content": self.content,
            "status": self.status.value,
            "priority": self.priority.value,
            "order": self.order,
            "estimated_time": self.estimated_time,
            "actual_time": self.actual_time,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TodoStep":
        return cls(
            id=data["id"],
            task_id=data["task_id"],
            content=data["content"],
            status=TodoStatus(data.get("status", "pending")),
            priority=TodoPriority(data.get("priority", "medium")),
            order=data.get("order", 0),
            estimated_time=data.get("estimated_time"),
            actual_time=data.get("actual_time"),
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now().timestamp()),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
        )


@dataclass
class TodoTask:
    """任务"""
    id: str
    phase_id: str
    title: str
    description: str = ""
    status: TodoStatus = TodoStatus.PENDING
    priority: TodoPriority = TodoPriority.MEDIUM
    order: int = 0
    steps: list[TodoStep] = field(default_factory=list)
    verification_document: VerificationDocument | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    started_at: float | None = None
    completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "phase_id": self.phase_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "order": self.order,
            "steps": [s.to_dict() for s in self.steps],
            "verification_document": self.verification_document.to_dict() if self.verification_document else None,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TodoTask":
        steps = [TodoStep.from_dict(s) for s in data.get("steps", [])]
        verification = None
        if data.get("verification_document"):
            verification = VerificationDocument.from_dict(data["verification_document"])
        return cls(
            id=data["id"],
            phase_id=data["phase_id"],
            title=data["title"],
            description=data.get("description", ""),
            status=TodoStatus(data.get("status", "pending")),
            priority=TodoPriority(data.get("priority", "medium")),
            order=data.get("order", 0),
            steps=steps,
            verification_document=verification,
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now().timestamp()),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
        )

    def get_progress(self) -> float:
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.status == TodoStatus.COMPLETED)
        return completed / len(self.steps)


@dataclass
class TodoPhase:
    """阶段"""
    id: str
    title: str
    description: str = ""
    status: TodoStatus = TodoStatus.PENDING
    priority: TodoPriority = TodoPriority.MEDIUM
    order: int = 0
    tasks: list[TodoTask] = field(default_factory=list)
    reflections: list[ReflectionResult] = field(default_factory=list)
    reflection_count: int = 0
    min_reflections: int = 2
    max_reflections: int = 5
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    started_at: float | None = None
    completed_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "order": self.order,
            "tasks": [t.to_dict() for t in self.tasks],
            "reflections": [r.to_dict() for r in self.reflections],
            "reflection_count": self.reflection_count,
            "min_reflections": self.min_reflections,
            "max_reflections": self.max_reflections,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TodoPhase":
        tasks = [TodoTask.from_dict(t) for t in data.get("tasks", [])]
        reflections = [ReflectionResult.from_dict(r) for r in data.get("reflections", [])]
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            status=TodoStatus(data.get("status", "pending")),
            priority=TodoPriority(data.get("priority", "medium")),
            order=data.get("order", 0),
            tasks=tasks,
            reflections=reflections,
            reflection_count=data.get("reflection_count", 0),
            min_reflections=data.get("min_reflections", 2),
            max_reflections=data.get("max_reflections", 5),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now().timestamp()),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
        )

    def get_progress(self) -> float:
        if not self.tasks:
            return 0.0
        completed = sum(1 for t in self.tasks if t.status == TodoStatus.COMPLETED)
        return completed / len(self.tasks)

    def needs_reflection(self) -> bool:
        return self.status == TodoStatus.COMPLETED and self.reflection_count < self.min_reflections

    def can_add_reflection(self) -> bool:
        return self.reflection_count < self.max_reflections


@dataclass
class MateModeState:
    """Mate模式状态"""
    enabled: bool = False
    current_reasoning: str = ""
    reflection_rounds: int = 0
    max_reflection_rounds: int = 3
    reflections: list[str] = field(default_factory=list)
    is_reflecting: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "current_reasoning": self.current_reasoning,
            "reflection_rounds": self.reflection_rounds,
            "max_reflection_rounds": self.max_reflection_rounds,
            "reflections": self.reflections,
            "is_reflecting": self.is_reflecting,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MateModeState":
        return cls(
            enabled=data.get("enabled", False),
            current_reasoning=data.get("current_reasoning", ""),
            reflection_rounds=data.get("reflection_rounds", 0),
            max_reflection_rounds=data.get("max_reflection_rounds", 3),
            reflections=data.get("reflections", []),
            is_reflecting=data.get("is_reflecting", False),
        )
