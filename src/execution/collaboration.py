"""
PyAgent 执行模块 - 多智能体协作管理器

实现多智能体协作模式，支持：
- 协作模式开关
- 并行执行
- 串行执行
- 故障切换机制
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .executor_agent import ExecutorAgent
from .planner import (
    DecompositionStrategy,
    ExecutionPlan,
    PlannerAgent,
    SubTask,
    SubTaskStatus,
)
from .task import Task, TaskResult


class CollaborationMode(Enum):
    """协作模式"""
    SINGLE = "single"
    MULTI = "multi"


@dataclass
class CollaborationConfig:
    """协作配置"""
    mode: CollaborationMode = CollaborationMode.SINGLE
    max_agents: int = 3
    parallel_timeout: float = 300.0
    retry_count: int = 2
    failover_enabled: bool = True
    enable_parallel: bool = True
    auto_assign: bool = True

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "mode": self.mode.value,
            "max_agents": self.max_agents,
            "parallel_timeout": self.parallel_timeout,
            "retry_count": self.retry_count,
            "failover_enabled": self.failover_enabled,
            "enable_parallel": self.enable_parallel,
            "auto_assign": self.auto_assign
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CollaborationConfig":
        """从字典创建"""
        return cls(
            mode=CollaborationMode(data.get("mode", "single")),
            max_agents=data.get("max_agents", 3),
            parallel_timeout=data.get("parallel_timeout", 300.0),
            retry_count=data.get("retry_count", 2),
            failover_enabled=data.get("failover_enabled", True),
            enable_parallel=data.get("enable_parallel", True),
            auto_assign=data.get("auto_assign", True)
        )


@dataclass
class ExecutionStatistics:
    """执行统计信息"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_duration: float = 0.0
    parallel_tasks: int = 0
    sequential_tasks: int = 0
    failover_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "total_duration": self.total_duration,
            "parallel_tasks": self.parallel_tasks,
            "sequential_tasks": self.sequential_tasks,
            "failover_count": self.failover_count
        }


class CollaborationManager:
    """
    多智能体协作管理器

    负责：
    - 管理协作模式开关
    - 协调多个执行智能体
    - 并行/串行执行子任务
    - 故障切换和重试
    """

    def __init__(
        self,
        llm_client: Any | None = None,
        tool_registry: Any | None = None,
        security_policy: Any | None = None,
        config: CollaborationConfig | None = None
    ):
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.security_policy = security_policy
        self.config = config or CollaborationConfig()

        self.planner = PlannerAgent(
            llm_client=llm_client,
            config={
                "enable_parallel": self.config.enable_parallel,
                "auto_assign": self.config.auto_assign
            }
        )

        self._executors: dict[str, ExecutorAgent] = {}
        self._executor_pool: ThreadPoolExecutor | None = None
        self._execution_plans: dict[str, ExecutionPlan] = {}
        self._statistics = ExecutionStatistics()

    def set_mode(self, mode: CollaborationMode) -> None:
        """设置协作模式"""
        self.config.mode = mode

    def is_multi_agent_enabled(self) -> bool:
        """检查是否启用多智能体模式"""
        return self.config.mode == CollaborationMode.MULTI

    def get_config(self) -> CollaborationConfig:
        """获取当前配置"""
        return self.config

    def get_statistics(self) -> ExecutionStatistics:
        """获取执行统计信息"""
        return self._statistics

    def reset_statistics(self) -> None:
        """重置统计信息"""
        self._statistics = ExecutionStatistics()

    async def execute(self, task: Task) -> TaskResult:
        """
        执行任务（根据模式选择执行方式）

        Args:
            task: 要执行的任务

        Returns:
            TaskResult: 任务执行结果
        """
        start_time = time.time()
        self._statistics.total_tasks += 1

        try:
            if self.is_multi_agent_enabled():
                result = await self._execute_multi(task)
            else:
                result = await self._execute_single(task)

            if result.success:
                self._statistics.completed_tasks += 1
            else:
                self._statistics.failed_tasks += 1

            self._statistics.total_duration += time.time() - start_time
            return result

        except Exception as e:
            self._statistics.failed_tasks += 1
            self._statistics.total_duration += time.time() - start_time
            return TaskResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )

    async def _execute_single(self, task: Task) -> TaskResult:
        """单智能体执行"""
        executor = self._get_or_create_executor("default")
        return await executor.execute(task)

    async def _execute_multi(self, task: Task) -> TaskResult:
        """多智能体协作执行"""
        plan = await self.planner.analyze_task(task)
        self._execution_plans[task.id] = plan

        results: dict[str, TaskResult] = {}

        if plan.strategy == DecompositionStrategy.PARALLEL:
            self._statistics.parallel_tasks += len(plan.subtasks)
            results = await self._execute_parallel(plan)
        elif plan.strategy == DecompositionStrategy.SEQUENTIAL:
            self._statistics.sequential_tasks += len(plan.subtasks)
            results = await self._execute_sequential(plan)
        else:
            parallel_count = sum(1 for s in plan.subtasks if not s.dependencies)
            sequential_count = len(plan.subtasks) - parallel_count
            self._statistics.parallel_tasks += parallel_count
            self._statistics.sequential_tasks += sequential_count
            results = await self._execute_hybrid(plan)

        return self.planner.aggregate_results(results)

    async def _execute_parallel(self, plan: ExecutionPlan) -> dict[str, TaskResult]:
        """
        并行执行子任务

        Args:
            plan: 执行计划

        Returns:
            dict[str, TaskResult]: 子任务ID到结果的映射
        """
        results: dict[str, TaskResult] = {}
        subtasks = plan.subtasks

        if not subtasks:
            return results

        async def execute_subtask(subtask: SubTask) -> tuple[str, TaskResult]:
            """执行单个子任务"""
            subtask.status = SubTaskStatus.RUNNING
            start_time = time.time()

            try:
                executor = self._get_or_create_executor(
                    subtask.assigned_agent or "default"
                )

                task = Task(
                    id=subtask.id,
                    prompt=subtask.prompt,
                    context=subtask.context
                )

                result = await asyncio.wait_for(
                    executor.execute(task),
                    timeout=self.config.parallel_timeout
                )

                subtask.status = SubTaskStatus.COMPLETED
                subtask.result = result
                return subtask.id, result

            except asyncio.TimeoutError:
                error_result = TaskResult(
                    success=False,
                    error=f"子任务执行超时（{self.config.parallel_timeout}秒）",
                    duration=time.time() - start_time
                )
                subtask.status = SubTaskStatus.FAILED
                subtask.result = error_result

                if self.config.failover_enabled:
                    failover_result = await self._handle_failure(subtask, TimeoutError("执行超时"))
                    if failover_result.success:
                        return subtask.id, failover_result

                return subtask.id, error_result

            except Exception as e:
                error_result = TaskResult(
                    success=False,
                    error=str(e),
                    duration=time.time() - start_time
                )
                subtask.status = SubTaskStatus.FAILED
                subtask.result = error_result

                if self.config.failover_enabled:
                    failover_result = await self._handle_failure(subtask, e)
                    if failover_result.success:
                        return subtask.id, failover_result

                return subtask.id, error_result

        tasks = [execute_subtask(subtask) for subtask in subtasks]
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        for item in task_results:
            if isinstance(item, Exception):
                continue
            subtask_id, result = item
            results[subtask_id] = result

        return results

    async def _execute_sequential(self, plan: ExecutionPlan) -> dict[str, TaskResult]:
        """
        串行执行子任务

        Args:
            plan: 执行计划

        Returns:
            dict[str, TaskResult]: 子任务ID到结果的映射
        """
        results: dict[str, TaskResult] = {}
        context_data: dict[str, Any] = {}

        for subtask in plan.subtasks:
            subtask.status = SubTaskStatus.RUNNING
            start_time = time.time()

            try:
                executor = self._get_or_create_executor(
                    subtask.assigned_agent or "default"
                )

                merged_context = {**subtask.context, **context_data}

                task = Task(
                    id=subtask.id,
                    prompt=subtask.prompt,
                    context=merged_context
                )

                result = await executor.execute(task)

                if result.success:
                    subtask.status = SubTaskStatus.COMPLETED
                    subtask.result = result

                    if result.data:
                        if isinstance(result.data, dict):
                            context_data.update(result.data)
                        else:
                            context_data[subtask.id] = result.data
                elif self.config.failover_enabled:
                    failover_result = await self._handle_failure(subtask, Exception(result.error))
                    if failover_result.success:
                        result = failover_result
                        subtask.status = SubTaskStatus.COMPLETED
                    else:
                        subtask.status = SubTaskStatus.FAILED
                else:
                    subtask.status = SubTaskStatus.FAILED

                results[subtask.id] = result

            except Exception as e:
                error_result = TaskResult(
                    success=False,
                    error=str(e),
                    duration=time.time() - start_time
                )
                subtask.status = SubTaskStatus.FAILED
                subtask.result = error_result

                if self.config.failover_enabled:
                    failover_result = await self._handle_failure(subtask, e)
                    if failover_result.success:
                        error_result = failover_result
                        subtask.status = SubTaskStatus.COMPLETED

                results[subtask.id] = error_result

        return results

    async def _execute_hybrid(self, plan: ExecutionPlan) -> dict[str, TaskResult]:
        """
        混合执行（考虑依赖关系）

        Args:
            plan: 执行计划

        Returns:
            dict[str, TaskResult]: 子任务ID到结果的映射
        """
        results: dict[str, TaskResult] = {}
        context_data: dict[str, Any] = {}

        while not plan.is_complete():
            ready_subtasks = plan.get_ready_subtasks()

            if not ready_subtasks:
                for subtask in plan.subtasks:
                    if subtask.status == SubTaskStatus.PENDING:
                        ready_subtasks.append(subtask)
                        break

                if not ready_subtasks:
                    break

            batch_results = await self._execute_batch(
                ready_subtasks,
                context_data
            )

            for subtask_id, result in batch_results.items():
                results[subtask_id] = result

                if result.success and result.data:
                    if isinstance(result.data, dict):
                        context_data.update(result.data)
                    else:
                        context_data[subtask_id] = result.data

        return results

    async def _execute_batch(
        self,
        subtasks: list[SubTask],
        context_data: dict[str, Any]
    ) -> dict[str, TaskResult]:
        """
        批量执行子任务（并行执行一批）

        Args:
            subtasks: 子任务列表
            context_data: 共享上下文数据

        Returns:
            dict[str, TaskResult]: 执行结果
        """
        async def execute_single(subtask: SubTask) -> tuple[str, TaskResult]:
            """执行单个子任务"""
            subtask.status = SubTaskStatus.RUNNING
            start_time = time.time()

            try:
                executor = self._get_or_create_executor(
                    subtask.assigned_agent or "default"
                )

                merged_context = {**subtask.context, **context_data}

                task = Task(
                    id=subtask.id,
                    prompt=subtask.prompt,
                    context=merged_context
                )

                result = await asyncio.wait_for(
                    executor.execute(task),
                    timeout=self.config.parallel_timeout
                )

                if result.success:
                    subtask.status = SubTaskStatus.COMPLETED
                elif self.config.failover_enabled:
                    failover_result = await self._handle_failure(subtask, Exception(result.error))
                    if failover_result.success:
                        result = failover_result
                        subtask.status = SubTaskStatus.COMPLETED
                    else:
                        subtask.status = SubTaskStatus.FAILED
                else:
                    subtask.status = SubTaskStatus.FAILED

                subtask.result = result
                return subtask.id, result

            except asyncio.TimeoutError:
                error_result = TaskResult(
                    success=False,
                    error=f"子任务执行超时（{self.config.parallel_timeout}秒）",
                    duration=time.time() - start_time
                )
                subtask.status = SubTaskStatus.FAILED
                subtask.result = error_result

                if self.config.failover_enabled:
                    failover_result = await self._handle_failure(subtask, TimeoutError("执行超时"))
                    if failover_result.success:
                        return subtask.id, failover_result

                return subtask.id, error_result

            except Exception as e:
                error_result = TaskResult(
                    success=False,
                    error=str(e),
                    duration=time.time() - start_time
                )
                subtask.status = SubTaskStatus.FAILED
                subtask.result = error_result

                if self.config.failover_enabled:
                    failover_result = await self._handle_failure(subtask, e)
                    if failover_result.success:
                        return subtask.id, failover_result

                return subtask.id, error_result

        tasks = [execute_single(subtask) for subtask in subtasks]
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        results: dict[str, TaskResult] = {}
        for item in task_results:
            if isinstance(item, Exception):
                continue
            subtask_id, result = item
            results[subtask_id] = result

        return results

    def _get_or_create_executor(self, agent_id: str) -> ExecutorAgent:
        """
        获取或创建执行智能体

        Args:
            agent_id: 智能体ID

        Returns:
            ExecutorAgent: 执行智能体实例
        """
        if agent_id not in self._executors:
            if len(self._executors) >= self.config.max_agents:
                min_tasks = float("inf")
                least_busy = None

                for eid, executor in self._executors.items():
                    task_count = len(executor.get_running_tasks())
                    if task_count < min_tasks:
                        min_tasks = task_count
                        least_busy = eid

                if least_busy:
                    return self._executors[least_busy]

            executor = ExecutorAgent(
                llm_client=self.llm_client,
                tool_registry=self.tool_registry,
                security_policy=self.security_policy
            )
            self._executors[agent_id] = executor

        return self._executors[agent_id]

    async def _handle_failure(
        self,
        subtask: SubTask,
        error: Exception
    ) -> TaskResult:
        """
        故障处理和切换

        Args:
            subtask: 失败的子任务
            error: 错误信息

        Returns:
            TaskResult: 重试后的结果
        """
        self._statistics.failover_count += 1

        for retry in range(self.config.retry_count):
            try:
                other_executors = [
                    eid for eid in self._executors.keys()
                    if eid != subtask.assigned_agent
                ]

                if not other_executors:
                    new_executor_id = f"failover_{retry}"
                    executor = self._get_or_create_executor(new_executor_id)
                else:
                    executor_id = other_executors[retry % len(other_executors)]
                    executor = self._executors[executor_id]

                task = Task(
                    id=f"{subtask.id}_retry_{retry}",
                    prompt=subtask.prompt,
                    context=subtask.context
                )

                result = await asyncio.wait_for(
                    executor.execute(task),
                    timeout=self.config.parallel_timeout
                )

                if result.success:
                    subtask.status = SubTaskStatus.COMPLETED
                    subtask.result = result
                    return result

            except Exception:
                continue

        return TaskResult(
            success=False,
            error=f"故障切换失败，已重试{self.config.retry_count}次: {error!s}"
        )

    def get_execution_plan(self, task_id: str) -> ExecutionPlan | None:
        """获取执行计划"""
        return self._execution_plans.get(task_id)

    def get_executor(self, agent_id: str) -> ExecutorAgent | None:
        """获取执行智能体"""
        return self._executors.get(agent_id)

    def get_all_executors(self) -> dict[str, ExecutorAgent]:
        """获取所有执行智能体"""
        return self._executors.copy()

    def clear_execution_plan(self, task_id: str) -> None:
        """清除执行计划"""
        if task_id in self._execution_plans:
            del self._execution_plans[task_id]

    def shutdown(self) -> None:
        """关闭协作管理器"""
        self._executors.clear()

        if self._executor_pool:
            self._executor_pool.shutdown(wait=False)
            self._executor_pool = None

        self._execution_plans.clear()
