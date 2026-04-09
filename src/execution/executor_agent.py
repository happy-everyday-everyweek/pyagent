"""
PyAgent 执行模块核心 - 执行Agent

参考OpenAkita的Agent设计，实现支持内部多智能体协作的执行Agent。
"""

import asyncio
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .react_engine import ReActEngine
from .task import Task, TaskResult, TaskStatus
from .task_context import TaskContext
from .task_queue import TaskQueue
from .task_queue import TaskStatus as QueueTaskStatus


class ExecutionMode(Enum):
    """执行模式"""
    SYNC = "sync"
    ASYNC = "async"


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    result: str = ""
    error: str = ""
    task_id: str | None = None
    steps: list[dict[str, Any]] = field(default_factory=list)
    duration: float = 0.0


class ExecutorAgent:
    """
    执行Agent

    负责执行具体任务，支持：
    - ReAct推理引擎
    - 同步/异步执行模式
    - 内部子Agent协作
    - 任务队列管理
    """

    def __init__(
        self,
        llm_client: Any | None = None,
        tool_registry: Any | None = None,
        security_policy: Any | None = None,
        config: dict[str, Any] | None = None
    ):
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.security_policy = security_policy
        self.config = config or {}

        self.task_queue = TaskQueue()
        self.react_engine = ReActEngine(
            llm_client=llm_client,
            tool_registry=tool_registry,
            security_policy=security_policy
        )

        self._sub_agents: dict[str, Any] = {}
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._current_task: Task | None = None
        self._context: TaskContext | None = None

        self.max_concurrent_tasks = self.config.get("max_concurrent_tasks", 5)
        self.default_timeout = self.config.get("default_timeout", 300)

    def register_sub_agent(self, name: str, agent: Any) -> None:
        """注册子Agent"""
        self._sub_agents[name] = agent

    def unregister_sub_agent(self, name: str) -> None:
        """注销子Agent"""
        if name in self._sub_agents:
            del self._sub_agents[name]

    def get_sub_agent(self, name: str) -> Any | None:
        """获取子Agent"""
        return self._sub_agents.get(name)

    async def execute(self, task: Task) -> TaskResult:
        """
        执行任务（主入口）
        
        Args:
            task: 要执行的任务对象
            
        Returns:
            TaskResult: 任务执行结果
        """
        self._current_task = task
        self._context = TaskContext(
            task_id=task.id,
            data=task.context.copy()
        )

        start_time = time.time()
        steps: list[dict[str, Any]] = []

        try:
            task.status = TaskStatus.RUNNING

            result = await self._do_execute(task)

            task.status = TaskStatus.COMPLETED
            task.result = result

            return TaskResult(
                success=True,
                data=result,
                duration=time.time() - start_time,
                steps=steps
            )

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)

            return TaskResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time,
                steps=steps
            )

    async def _do_execute(self, task: Task) -> Any:
        """
        实际执行逻辑
        
        Args:
            task: 要执行的任务
            
        Returns:
            执行结果
        """
        context_data = self._context.to_dict() if self._context else {}

        result = await self.react_engine.run(
            task=task.prompt,
            context=context_data
        )

        if result.get("success"):
            return result.get("result")
        raise Exception(result.get("result", "执行失败"))

    def get_context(self) -> TaskContext | None:
        """获取当前任务上下文"""
        return self._context

    def update_context(self, key: str, value: Any) -> None:
        """
        更新任务上下文
        
        Args:
            key: 数据键
            value: 数据值
        """
        if self._context:
            self._context.set(key, value)

    def get_current_task(self) -> Task | None:
        """获取当前正在执行的任务"""
        return self._current_task

    async def execute_sync(
        self,
        task: str,
        timeout: int = None,
        context: dict[str, Any] | None = None
    ) -> str:
        """同步执行任务"""
        timeout = timeout or self.default_timeout

        try:
            result = await asyncio.wait_for(
                self.react_engine.run(task, context),
                timeout=timeout
            )

            return result.get("result", "任务完成")

        except asyncio.TimeoutError:
            return f"任务执行超时（{timeout}秒）"
        except Exception as e:
            return f"任务执行失败: {e!s}"

    async def submit_async_task(
        self,
        task: str,
        context: dict[str, Any] | None = None,
        callback: Callable | None = None
    ) -> str:
        """提交异步任务"""
        task_id = str(uuid.uuid4())[:8]

        self.task_queue.add_task(
            task_id=task_id,
            task=task,
            context=context,
            callback=callback
        )

        asyncio.create_task(self._process_async_task(task_id))

        return task_id

    async def _process_async_task(self, task_id: str) -> None:
        """处理异步任务"""
        task_info = self.task_queue.get_task(task_id)
        if not task_info:
            return

        self.task_queue.update_status(task_id, QueueTaskStatus.RUNNING)

        try:
            result = await self.react_engine.run(
                task_info.task,
                task_info.context
            )

            self.task_queue.update_status(
                task_id,
                QueueTaskStatus.COMPLETED,
                result=result.get("result", "任务完成")
            )

            if callback := task_info.callback:
                await callback(task_id, result)

        except Exception as e:
            self.task_queue.update_status(
                task_id,
                QueueTaskStatus.FAILED,
                error=str(e)
            )

    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """获取任务状态"""
        return self.task_queue.get_task_status(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            task.cancel()
            del self._running_tasks[task_id]

        return self.task_queue.update_status(task_id, QueueTaskStatus.CANCELLED)

    async def delegate_to_sub_agent(
        self,
        agent_name: str,
        task: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """委派任务给子Agent"""
        agent = self._sub_agents.get(agent_name)
        if not agent:
            return {
                "success": False,
                "error": f"子Agent '{agent_name}' 不存在"
            }

        try:
            result = await agent.execute(task, context)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def aggregate_results(
        self,
        results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """聚合多个结果"""
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        aggregated = {
            "total": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "results": successful,
            "errors": [r.get("error") for r in failed]
        }

        return aggregated

    def get_running_tasks(self) -> list[str]:
        """获取正在运行的任务列表"""
        return list(self._running_tasks.keys())

    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.task_queue.size()
