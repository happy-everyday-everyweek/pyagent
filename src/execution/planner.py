"""
PyAgent 执行模块 - 规划智能体

负责任务分解、智能体分配和结果聚合。
"""

import asyncio
import json
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .task import Task, TaskResult


class DecompositionStrategy(Enum):
    """分解策略"""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    HYBRID = "hybrid"


class SubTaskStatus(Enum):
    """子任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SubTask:
    """子任务定义"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_task_id: str = ""
    prompt: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    assigned_agent: str | None = None
    priority: int = 0
    dependencies: list[str] = field(default_factory=list)
    status: SubTaskStatus = SubTaskStatus.PENDING
    result: TaskResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "parent_task_id": self.parent_task_id,
            "prompt": self.prompt,
            "context": self.context,
            "assigned_agent": self.assigned_agent,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result.to_dict() if self.result else None,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SubTask":
        """从字典创建"""
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            parent_task_id=data.get("parent_task_id", ""),
            prompt=data.get("prompt", ""),
            context=data.get("context", {}),
            assigned_agent=data.get("assigned_agent"),
            priority=data.get("priority", 0),
            dependencies=data.get("dependencies", []),
            status=SubTaskStatus(data.get("status", "pending")),
            result=TaskResult.from_dict(data["result"]) if data.get("result") else None,
            metadata=data.get("metadata", {})
        )


@dataclass
class ExecutionPlan:
    """执行计划"""
    task_id: str = ""
    subtasks: list[SubTask] = field(default_factory=list)
    strategy: DecompositionStrategy = DecompositionStrategy.HYBRID
    execution_order: list[list[str]] = field(default_factory=list)
    estimated_duration: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "subtasks": [s.to_dict() for s in self.subtasks],
            "strategy": self.strategy.value,
            "execution_order": self.execution_order,
            "estimated_duration": self.estimated_duration,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionPlan":
        """从字典创建"""
        return cls(
            task_id=data.get("task_id", ""),
            subtasks=[SubTask.from_dict(s) for s in data.get("subtasks", [])],
            strategy=DecompositionStrategy(data.get("strategy", "hybrid")),
            execution_order=data.get("execution_order", []),
            estimated_duration=data.get("estimated_duration", 0.0),
            metadata=data.get("metadata", {})
        )

    def get_subtask(self, subtask_id: str) -> SubTask | None:
        """获取子任务"""
        for subtask in self.subtasks:
            if subtask.id == subtask_id:
                return subtask
        return None

    def get_ready_subtasks(self) -> list[SubTask]:
        """获取可执行的子任务（依赖已满足）"""
        completed_ids = {
            s.id for s in self.subtasks
            if s.status == SubTaskStatus.COMPLETED
        }

        ready = []
        for subtask in self.subtasks:
            if subtask.status != SubTaskStatus.PENDING:
                continue
            if all(dep in completed_ids for dep in subtask.dependencies):
                ready.append(subtask)

        return sorted(ready, key=lambda x: x.priority, reverse=True)

    def is_complete(self) -> bool:
        """检查计划是否完成"""
        return all(
            s.status in (SubTaskStatus.COMPLETED, SubTaskStatus.SKIPPED)
            for s in self.subtasks
        )

    def get_progress(self) -> dict[str, Any]:
        """获取执行进度"""
        total = len(self.subtasks)
        completed = sum(1 for s in self.subtasks if s.status == SubTaskStatus.COMPLETED)
        failed = sum(1 for s in self.subtasks if s.status == SubTaskStatus.FAILED)
        running = sum(1 for s in self.subtasks if s.status == SubTaskStatus.RUNNING)
        pending = sum(1 for s in self.subtasks if s.status == SubTaskStatus.PENDING)

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "progress_percent": (completed / total * 100) if total > 0 else 0
        }


@dataclass
class AgentCapability:
    """智能体能力描述"""
    name: str
    description: str
    skills: list[str] = field(default_factory=list)
    max_concurrent_tasks: int = 3
    priority: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "skills": self.skills,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "priority": self.priority
        }


class PlannerAgent:
    """
    规划智能体

    负责：
    - 分析任务特征
    - 分解复杂任务
    - 分配执行智能体
    - 聚合执行结果
    """

    def __init__(
        self,
        llm_client: Any | None = None,
        config: dict[str, Any] | None = None
    ):
        self.llm_client = llm_client
        self.config = config or {}

        self._available_agents: dict[str, AgentCapability] = {}
        self._execution_plans: dict[str, ExecutionPlan] = {}

        self.max_subtasks = self.config.get("max_subtasks", 10)
        self.enable_parallel = self.config.get("enable_parallel", True)
        self.auto_assign = self.config.get("auto_assign", True)

    def register_agent(self, capability: AgentCapability) -> None:
        """注册可用智能体"""
        self._available_agents[capability.name] = capability

    def unregister_agent(self, name: str) -> None:
        """注销智能体"""
        if name in self._available_agents:
            del self._available_agents[name]

    def get_available_agents(self) -> list[AgentCapability]:
        """获取可用智能体列表"""
        return list(self._available_agents.values())

    async def analyze_task(self, task: Task) -> ExecutionPlan:
        """分析任务，生成执行计划"""
        strategy = self.determine_strategy(task)

        subtasks = await self.decompose_task(task, strategy)

        if self.auto_assign:
            subtasks = self.assign_agents(subtasks, list(self._available_agents.keys()))

        execution_order = self._calculate_execution_order(subtasks, strategy)

        plan = ExecutionPlan(
            task_id=task.id,
            subtasks=subtasks,
            strategy=strategy,
            execution_order=execution_order,
            metadata={
                "original_prompt": task.prompt,
                "created_at": asyncio.get_event_loop().time()
            }
        )

        self._execution_plans[task.id] = plan
        return plan

    def determine_strategy(self, task: Task) -> DecompositionStrategy:
        """根据任务特征确定分解策略"""
        prompt = task.prompt.lower()
        tags = task.tags

        sequential_keywords = ["然后", "之后", "接着", "依次", "步骤", "流程", "then", "after", "next", "step"]
        parallel_keywords = ["同时", "并行", "一起", "分别", "parallel", "simultaneously", "concurrently"]

        has_sequential = any(kw in prompt for kw in sequential_keywords)
        has_parallel = any(kw in prompt for kw in parallel_keywords)

        if "sequential" in tags or (has_sequential and not has_parallel):
            return DecompositionStrategy.SEQUENTIAL
        elif "parallel" in tags or (has_parallel and not has_sequential):
            return DecompositionStrategy.PARALLEL
        else:
            return DecompositionStrategy.HYBRID

    async def decompose_task(
        self,
        task: Task,
        strategy: DecompositionStrategy
    ) -> list[SubTask]:
        """分解任务为子任务"""
        if not self.llm_client:
            return self._simple_decompose(task, strategy)

        try:
            decomposition = await self._llm_decompose(task, strategy)
            return decomposition
        except Exception:
            return self._simple_decompose(task, strategy)

    async def _llm_decompose(
        self,
        task: Task,
        strategy: DecompositionStrategy
    ) -> list[SubTask]:
        """使用LLM分解任务"""
        from src.llm import Message

        prompt = self._build_decomposition_prompt(task, strategy)

        messages = [Message(role="user", content=prompt)]
        response = await self.llm_client.generate(messages=messages)

        return self._parse_decomposition_response(response.content, task.id, strategy)

    def _build_decomposition_prompt(
        self,
        task: Task,
        strategy: DecompositionStrategy
    ) -> str:
        """构建分解提示词"""
        strategy_desc = {
            DecompositionStrategy.PARALLEL: "并行执行（子任务之间无依赖）",
            DecompositionStrategy.SEQUENTIAL: "串行执行（子任务有先后顺序）",
            DecompositionStrategy.HYBRID: "混合执行（部分并行，部分串行）"
        }

        available_agents_desc = "\n".join([
            f"- {name}: {cap.description}"
            for name, cap in self._available_agents.items()
        ]) or "无特定智能体"

        return f"""请将以下任务分解为子任务。

原始任务: {task.prompt}

分解策略: {strategy_desc[strategy]}

可用智能体:
{available_agents_desc}

请按以下JSON格式输出分解结果：
{{
    "subtasks": [
        {{
            "prompt": "子任务描述",
            "priority": 0-10的优先级,
            "dependencies": ["依赖的子任务索引，从0开始"]
        }}
    ]
}}

要求：
1. 子任务数量不超过{self.max_subtasks}个
2. 每个子任务应该清晰明确
3. 根据策略设置正确的依赖关系
4. 优先级越高数值越大

请直接输出JSON，不要包含其他内容。"""

    def _parse_decomposition_response(
        self,
        response: str,
        task_id: str,
        strategy: DecompositionStrategy
    ) -> list[SubTask]:
        """解析分解响应"""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)

            subtasks = []
            subtask_data_list = data.get("subtasks", [])

            for idx, item in enumerate(subtask_data_list[:self.max_subtasks]):
                dependencies = []
                for dep_idx in item.get("dependencies", []):
                    if 0 <= dep_idx < idx:
                        dependencies.append(f"subtask_{dep_idx}")

                subtask = SubTask(
                    id=f"subtask_{idx}",
                    parent_task_id=task_id,
                    prompt=item.get("prompt", ""),
                    priority=item.get("priority", 0),
                    dependencies=dependencies,
                    metadata={"index": idx}
                )
                subtasks.append(subtask)

            return subtasks

        except (json.JSONDecodeError, KeyError):
            return []

    def _simple_decompose(
        self,
        task: Task,
        strategy: DecompositionStrategy
    ) -> list[SubTask]:
        """简单分解策略（不使用LLM）"""
        sentences = re.split(r'[。！？\n]', task.prompt)
        sentences = [s.strip() for s in sentences if s.strip()]

        subtasks = []
        for idx, sentence in enumerate(sentences[:self.max_subtasks]):
            dependencies = []
            if strategy == DecompositionStrategy.SEQUENTIAL and idx > 0:
                dependencies = [f"subtask_{idx - 1}"]

            subtask = SubTask(
                id=f"subtask_{idx}",
                parent_task_id=task.id,
                prompt=sentence,
                priority=max(0, 10 - idx),
                dependencies=dependencies,
                metadata={"index": idx}
            )
            subtasks.append(subtask)

        if not subtasks:
            subtasks.append(SubTask(
                id="subtask_0",
                parent_task_id=task.id,
                prompt=task.prompt,
                priority=10
            ))

        return subtasks

    def assign_agents(
        self,
        subtasks: list[SubTask],
        available_agents: list[str]
    ) -> list[SubTask]:
        """为子任务分配执行智能体"""
        if not available_agents:
            return subtasks

        for subtask in subtasks:
            best_agent = self._find_best_agent(subtask, available_agents)
            if best_agent:
                subtask.assigned_agent = best_agent

        return subtasks

    def _find_best_agent(
        self,
        subtask: SubTask,
        available_agents: list[str]
    ) -> str | None:
        """为子任务找到最佳智能体"""
        prompt_lower = subtask.prompt.lower()

        agent_scores: dict[str, float] = {}

        for agent_name in available_agents:
            capability = self._available_agents.get(agent_name)
            if not capability:
                continue

            score = 0.0

            for skill in capability.skills:
                if skill.lower() in prompt_lower:
                    score += 10.0

            if any(kw in prompt_lower for kw in ["搜索", "查询", "search", "query"]):
                if "search" in capability.name.lower():
                    score += 5.0

            if any(kw in prompt_lower for kw in ["浏览器", "网页", "browser", "web"]):
                if "browser" in capability.name.lower():
                    score += 5.0

            if any(kw in prompt_lower for kw in ["文件", "读写", "file", "read", "write"]):
                if "file" in capability.name.lower():
                    score += 5.0

            score += capability.priority * 0.1

            agent_scores[agent_name] = score

        if not agent_scores:
            return available_agents[0] if available_agents else None

        best_agent = max(agent_scores.keys(), key=lambda x: agent_scores[x])

        if agent_scores[best_agent] > 0:
            return best_agent

        min_tasks = float('inf')
        selected_agent = available_agents[0]

        for agent_name in available_agents:
            assigned_count = sum(
                1 for s in self._get_all_pending_subtasks()
                if s.assigned_agent == agent_name
            )
            if assigned_count < min_tasks:
                min_tasks = assigned_count
                selected_agent = agent_name

        return selected_agent

    def _get_all_pending_subtasks(self) -> list[SubTask]:
        """获取所有待执行的子任务"""
        subtasks = []
        for plan in self._execution_plans.values():
            subtasks.extend([
                s for s in plan.subtasks
                if s.status == SubTaskStatus.PENDING
            ])
        return subtasks

    def _calculate_execution_order(
        self,
        subtasks: list[SubTask],
        strategy: DecompositionStrategy
    ) -> list[list[str]]:
        """计算执行顺序"""
        if not subtasks:
            return []

        if strategy == DecompositionStrategy.PARALLEL:
            return [[s.id for s in subtasks]]

        if strategy == DecompositionStrategy.SEQUENTIAL:
            return [[s.id] for s in subtasks]

        order: list[list[str]] = []
        assigned: set[str] = set()

        while len(assigned) < len(subtasks):
            ready = []
            for subtask in subtasks:
                if subtask.id in assigned:
                    continue
                if all(dep in assigned for dep in subtask.dependencies):
                    ready.append(subtask)

            if not ready:
                for subtask in subtasks:
                    if subtask.id not in assigned:
                        ready.append(subtask)
                        if len(ready) >= 3:
                            break

            if ready:
                batch = [s.id for s in sorted(ready, key=lambda x: x.priority, reverse=True)[:3]]
                order.append(batch)
                assigned.update(batch)

        return order

    def aggregate_results(
        self,
        subtask_results: dict[str, TaskResult]
    ) -> TaskResult:
        """聚合子任务执行结果"""
        if not subtask_results:
            return TaskResult(
                success=False,
                error="没有子任务结果"
            )

        successful_results = {
            k: v for k, v in subtask_results.items()
            if v.success
        }
        failed_results = {
            k: v for k, v in subtask_results.items()
            if not v.success
        }

        all_success = len(failed_results) == 0

        aggregated_data = self._merge_result_data(successful_results)

        all_steps = []
        for result in subtask_results.values():
            all_steps.extend(result.steps)

        errors = [r.error for r in failed_results.values() if r.error]
        error_msg = "; ".join(errors) if errors else None

        total_duration = sum(r.duration for r in subtask_results.values())

        return TaskResult(
            success=all_success,
            data=aggregated_data,
            error=error_msg,
            duration=total_duration,
            steps=all_steps,
            metadata={
                "total_subtasks": len(subtask_results),
                "successful": len(successful_results),
                "failed": len(failed_results)
            }
        )

    def _merge_result_data(
        self,
        results: dict[str, TaskResult]
    ) -> dict[str, Any]:
        """合并结果数据"""
        merged: dict[str, Any] = {
            "summaries": [],
            "data": {}
        }

        for subtask_id, result in results.items():
            if result.data:
                if isinstance(result.data, str):
                    merged["summaries"].append({
                        "subtask_id": subtask_id,
                        "summary": result.data
                    })
                elif isinstance(result.data, dict):
                    merged["data"][subtask_id] = result.data
                else:
                    merged["data"][subtask_id] = str(result.data)

        return merged

    def get_plan(self, task_id: str) -> ExecutionPlan | None:
        """获取执行计划"""
        return self._execution_plans.get(task_id)

    def update_subtask_status(
        self,
        task_id: str,
        subtask_id: str,
        status: SubTaskStatus,
        result: TaskResult | None = None
    ) -> bool:
        """更新子任务状态"""
        plan = self._execution_plans.get(task_id)
        if not plan:
            return False

        subtask = plan.get_subtask(subtask_id)
        if not subtask:
            return False

        subtask.status = status
        if result:
            subtask.result = result

        return True

    def get_next_subtasks(self, task_id: str) -> list[SubTask]:
        """获取下一批可执行的子任务"""
        plan = self._execution_plans.get(task_id)
        if not plan:
            return []

        return plan.get_ready_subtasks()

    def clear_plan(self, task_id: str) -> None:
        """清除执行计划"""
        if task_id in self._execution_plans:
            del self._execution_plans[task_id]
