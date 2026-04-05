"""
PyAgent 浏览器自动化模块 - 任务规划系统

提供任务规划、执行跟踪和动态调整功能。
参考 browser-use 项目的规划器设计实现。
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PlanStatus(str, Enum):
    """计划状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepStatus(str, Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """计划步骤"""
    id: int
    description: str
    status: StepStatus = StepStatus.PENDING
    action: str | None = None
    expected_outcome: str | None = None
    actual_outcome: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    dependencies: list[int] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3


class Plan(BaseModel):
    """执行计划"""
    
    id: str = Field(default_factory=lambda: f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    task: str
    goal: str | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list)
    current_step_index: int = 0
    status: PlanStatus = PlanStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    def add_step(
        self,
        description: str,
        action: str | None = None,
        expected_outcome: str | None = None,
        dependencies: list[int] | None = None,
    ) -> int:
        """
        添加步骤
        
        Args:
            description: 步骤描述
            action: 要执行的动作
            expected_outcome: 预期结果
            dependencies: 依赖的步骤 ID 列表
            
        Returns:
            步骤 ID
        """
        step_id = len(self.steps)
        
        step = {
            "id": step_id,
            "description": description,
            "action": action,
            "expected_outcome": expected_outcome,
            "status": StepStatus.PENDING.value,
            "dependencies": dependencies or [],
            "retry_count": 0,
            "max_retries": 3,
        }
        
        self.steps.append(step)
        self.updated_at = datetime.now()
        
        return step_id
    
    def get_current_step(self) -> dict[str, Any] | None:
        """获取当前步骤"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def get_step(self, step_id: int) -> dict[str, Any] | None:
        """获取指定步骤"""
        if 0 <= step_id < len(self.steps):
            return self.steps[step_id]
        return None
    
    def update_step_status(
        self,
        step_id: int,
        status: StepStatus,
        outcome: str | None = None,
        error: str | None = None,
    ) -> bool:
        """
        更新步骤状态
        
        Args:
            step_id: 步骤 ID
            status: 新状态
            outcome: 实际结果
            error: 错误信息
            
        Returns:
            是否更新成功
        """
        step = self.get_step(step_id)
        if step is None:
            return False
        
        step["status"] = status.value
        
        if outcome:
            step["actual_outcome"] = outcome
        
        if error:
            step["error"] = error
        
        if status == StepStatus.RUNNING:
            step["started_at"] = datetime.now().isoformat()
        elif status in [StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED]:
            step["completed_at"] = datetime.now().isoformat()
        
        self.updated_at = datetime.now()
        
        return True
    
    def advance_step(self) -> dict[str, Any] | None:
        """前进到下一步"""
        self.current_step_index += 1
        return self.get_current_step()
    
    def get_progress(self) -> dict[str, Any]:
        """获取进度信息"""
        total = len(self.steps)
        completed = sum(
            1 for s in self.steps
            if s.get("status") == StepStatus.COMPLETED.value
        )
        failed = sum(
            1 for s in self.steps
            if s.get("status") == StepStatus.FAILED.value
        )
        skipped = sum(
            1 for s in self.steps
            if s.get("status") == StepStatus.SKIPPED.value
        )
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "pending": total - completed - failed - skipped,
            "current_step": self.current_step_index,
            "progress_percent": (completed / total * 100) if total > 0 else 0,
        }
    
    def is_complete(self) -> bool:
        """检查计划是否完成"""
        return all(
            s.get("status") in [
                StepStatus.COMPLETED.value,
                StepStatus.SKIPPED.value,
            ]
            for s in self.steps
        )
    
    def has_failed(self) -> bool:
        """检查是否有失败步骤"""
        return any(
            s.get("status") == StepStatus.FAILED.value
            for s in self.steps
        )
    
    def get_next_executable_step(self) -> dict[str, Any] | None:
        """获取下一个可执行的步骤"""
        for step in self.steps:
            if step.get("status") != StepStatus.PENDING.value:
                continue
            
            dependencies = step.get("dependencies", [])
            all_deps_met = all(
                self.steps[dep_id].get("status") == StepStatus.COMPLETED.value
                for dep_id in dependencies
                if 0 <= dep_id < len(self.steps)
            )
            
            if all_deps_met:
                return step
        
        return None
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "task": self.task,
            "goal": self.goal,
            "steps": self.steps,
            "current_step_index": self.current_step_index,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "progress": self.get_progress(),
            "metadata": self.metadata,
        }


class TaskPlanner:
    """任务规划器"""
    
    def __init__(self, llm_client: Any | None = None):
        """
        初始化任务规划器
        
        Args:
            llm_client: LLM 客户端
        """
        self._llm_client = llm_client
        self._plans: dict[str, Plan] = {}
    
    def set_llm_client(self, client: Any) -> None:
        """设置 LLM 客户端"""
        self._llm_client = client
    
    async def create_plan(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> Plan:
        """
        创建执行计划
        
        Args:
            task: 任务描述
            context: 上下文信息
            
        Returns:
            Plan: 执行计划
        """
        plan = Plan(task=task)
        
        if self._llm_client:
            try:
                steps = await self._generate_steps_with_llm(task, context)
                for step_info in steps:
                    plan.add_step(
                        description=step_info.get("description", ""),
                        action=step_info.get("action"),
                        expected_outcome=step_info.get("expected_outcome"),
                        dependencies=step_info.get("dependencies"),
                    )
            except Exception as e:
                logger.error(f"Failed to generate plan with LLM: {e}")
                plan = self._create_default_plan(task)
        else:
            plan = self._create_default_plan(task)
        
        self._plans[plan.id] = plan
        logger.info(f"Created plan {plan.id} with {len(plan.steps)} steps")
        
        return plan
    
    async def _generate_steps_with_llm(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """使用 LLM 生成步骤"""
        prompt = f"""Break down the following task into executable steps for a browser automation agent.

Task: {task}

Context: {json.dumps(context, default=str) if context else 'None'}

For each step, provide:
1. description: A clear description of what the step does
2. action: The browser action to take (navigate, click, type, scroll, extract, etc.)
3. expected_outcome: What should happen after this step
4. dependencies: List of step IDs this step depends on (use indices starting from 0)

Return a JSON array of steps. Example:
[
  {{"description": "Navigate to the website", "action": "navigate", "expected_outcome": "Page loads successfully", "dependencies": []}},
  {{"description": "Click login button", "action": "click", "expected_outcome": "Login form appears", "dependencies": [0]}}
]

Only return the JSON array, no other text."""

        response = await self._llm_client.chat.completions.create(
            model=self._llm_client.model,
            messages=[{"role": "user", "content": prompt}],
        )
        
        content = response.choices[0].message.content or "[]"
        
        json_match = re.search(r'\[[\s\S]*\]', content)
        if json_match:
            return json.loads(json_match.group())
        
        return []
    
    def _create_default_plan(self, task: str) -> Plan:
        """创建默认计划"""
        plan = Plan(task=task)
        
        plan.add_step(
            description="Analyze the task and determine the first action",
            action="analyze",
            expected_outcome="Task understood, ready to proceed",
        )
        
        plan.add_step(
            description="Execute the main task actions",
            expected_outcome="Task actions completed",
            dependencies=[0],
        )
        
        plan.add_step(
            description="Verify and complete the task",
            action="done",
            expected_outcome="Task completed successfully",
            dependencies=[1],
        )
        
        return plan
    
    def get_plan(self, plan_id: str) -> Plan | None:
        """获取计划"""
        return self._plans.get(plan_id)
    
    def update_plan(
        self,
        plan_id: str,
        updates: dict[str, Any],
    ) -> Plan | None:
        """更新计划"""
        plan = self.get_plan(plan_id)
        if plan is None:
            return None
        
        for key, value in updates.items():
            if hasattr(plan, key):
                setattr(plan, key, value)
        
        plan.updated_at = datetime.now()
        
        return plan
    
    async def replan(
        self,
        plan_id: str,
        reason: str,
        context: dict[str, Any] | None = None,
    ) -> Plan | None:
        """
        重新规划
        
        Args:
            plan_id: 计划 ID
            reason: 重新规划的原因
            context: 当前上下文
            
        Returns:
            新计划或 None
        """
        old_plan = self.get_plan(plan_id)
        if old_plan is None:
            return None
        
        logger.info(f"Replanning {plan_id} due to: {reason}")
        
        new_task = f"{old_plan.task} (Replanned: {reason})"
        
        new_plan = await self.create_plan(new_task, context)
        
        return new_plan
    
    def list_plans(self) -> list[Plan]:
        """列出所有计划"""
        return list(self._plans.values())
    
    def delete_plan(self, plan_id: str) -> bool:
        """删除计划"""
        if plan_id in self._plans:
            del self._plans[plan_id]
            return True
        return False
    
    def clear_plans(self) -> None:
        """清除所有计划"""
        self._plans.clear()
