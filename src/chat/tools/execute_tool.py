"""
PyAgent 聊天Agent工具集 - 执行工具

通过模块间通信调用执行Agent。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ExecutionMode(Enum):
    """执行模式"""
    SYNC = "sync"
    ASYNC = "async"


@dataclass
class ExecuteToolResult:
    """执行工具结果"""
    success: bool
    result: str = ""
    error: str = ""
    task_id: str | None = None
    mode: ExecutionMode = ExecutionMode.SYNC
    status: str = "completed"


class ExecuteTool:
    """执行工具 - 模块间通信调用执行Agent"""

    def __init__(self, executor_agent: Any | None = None):
        self.executor_agent = executor_agent
        self.name = "execute"
        self.description = "执行任务（支持同步和异步模式）"

    async def execute(
        self,
        task: str,
        async_mode: bool = False,
        timeout: int = 300,
        **kwargs
    ) -> ExecuteToolResult:
        """执行任务"""
        if not task:
            return ExecuteToolResult(
                success=False,
                error="任务不能为空"
            )

        if self.executor_agent:
            try:
                if async_mode:
                    task_id = await self.executor_agent.submit_async_task(task)
                    return ExecuteToolResult(
                        success=True,
                        result="任务已提交",
                        task_id=task_id,
                        mode=ExecutionMode.ASYNC,
                        status="pending"
                    )
                result = await self.executor_agent.execute_sync(task, timeout)
                return ExecuteToolResult(
                    success=True,
                    result=result,
                    mode=ExecutionMode.SYNC,
                    status="completed"
                )
            except Exception as e:
                return ExecuteToolResult(
                    success=False,
                    error=str(e)
                )

        return ExecuteToolResult(
            success=True,
            result=f"模拟执行任务: {task}",
            mode=ExecutionMode.SYNC if not async_mode else ExecutionMode.ASYNC,
            task_id="mock-task-id" if async_mode else None,
            status="completed"
        )

    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """获取异步任务状态"""
        if self.executor_agent:
            return await self.executor_agent.get_task_status(task_id)

        return {
            "task_id": task_id,
            "status": "completed",
            "result": "模拟任务结果"
        }

    async def cancel_task(self, task_id: str) -> bool:
        """取消异步任务"""
        if self.executor_agent:
            return await self.executor_agent.cancel_task(task_id)

        return True

    def get_description(self) -> str:
        """获取工具描述"""
        return self.description

    def get_parameters(self) -> dict[str, Any]:
        """获取参数定义"""
        return {
            "task": {
                "type": "string",
                "description": "要执行的任务描述"
            },
            "async_mode": {
                "type": "boolean",
                "description": "是否异步执行",
                "default": False
            },
            "timeout": {
                "type": "integer",
                "description": "超时时间（秒）",
                "default": 300
            }
        }
