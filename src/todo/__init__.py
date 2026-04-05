"""
PyAgent AI原生Todo列表系统

实现三级分类的任务管理：
- 阶段（Phase）：最高级别，代表一个大的工作阶段
- 任务（Task）：中间级别，代表具体的工作任务
- 步骤（Step）：最低级别，代表具体的执行步骤

功能：
- 每完成一个步骤，自动更新任务列表
- 每个任务自动创建验收文档
- 每完成一个阶段，进行2-5轮反思
- Mate模式：推理显示和反思
"""

from .mate_mode import MateModeManager, mate_mode_manager
from .todo_manager import TodoManager, todo_manager
from .types import (
    MateModeState,
    ReflectionResult,
    TodoLevel,
    TodoPhase,
    TodoPriority,
    TodoStatus,
    TodoStep,
    TodoTask,
    VerificationDocument,
)

__all__ = [
    "MateModeManager",
    "MateModeState",
    "ReflectionResult",
    "TodoLevel",
    "TodoManager",
    "TodoPhase",
    "TodoPriority",
    "TodoStatus",
    "TodoStep",
    "TodoTask",
    "VerificationDocument",
    "mate_mode_manager",
    "todo_manager",
]
