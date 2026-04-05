"""
PyAgent AI原生Todo列表系统 - Todo管理器

实现三级分类的Todo管理：
- 阶段（Phase）：最高层级，包含多个任务
- 任务（Task）：中间层级，包含多个步骤
- 步骤（Step）：最低层级，具体执行单元

功能：
- 步骤完成后自动更新任务列表
- 任务完成后自动创建验收文档
- 阶段完成后进行2-5轮反思
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .types import (
    ReflectionResult,
    TodoPhase,
    TodoPriority,
    TodoStatus,
    TodoStep,
    TodoTask,
    VerificationDocument,
)


class TodoManager:
    """AI原生Todo管理器"""

    def __init__(self, data_dir: str = "data/todo"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.phases: dict[str, TodoPhase] = {}
        self._verification_dir = self.data_dir / "verifications"
        self._verification_dir.mkdir(parents=True, exist_ok=True)

        self._load_data()

    def _get_storage_file(self) -> Path:
        return self.data_dir / "todos.json"

    def _load_data(self) -> None:
        file_path = self._get_storage_file()
        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("phases", []):
                        phase = TodoPhase.from_dict(item)
                        self.phases[phase.id] = phase
            except Exception:
                pass

    def _save_data(self) -> None:
        file_path = self._get_storage_file()
        try:
            data = {
                "phases": [p.to_dict() for p in self.phases.values()],
                "updated_at": datetime.now().isoformat(),
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _generate_id(self, prefix: str = "todo") -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    async def create_phase(
        self,
        title: str,
        description: str = "",
        priority: TodoPriority = TodoPriority.MEDIUM,
        min_reflections: int = 2,
        max_reflections: int = 5,
    ) -> TodoPhase:
        phase = TodoPhase(
            id=self._generate_id("phase"),
            title=title,
            description=description,
            priority=priority,
            min_reflections=min_reflections,
            max_reflections=max_reflections,
        )

        self.phases[phase.id] = phase
        self._save_data()

        return phase

    async def create_task(
        self,
        phase_id: str,
        title: str,
        description: str = "",
        priority: TodoPriority = TodoPriority.MEDIUM,
        steps: list[str] | None = None,
    ) -> TodoTask | None:
        phase = self.phases.get(phase_id)
        if not phase:
            return None

        task = TodoTask(
            id=self._generate_id("task"),
            phase_id=phase_id,
            title=title,
            description=description,
            priority=priority,
            order=len(phase.tasks),
        )

        if steps:
            for i, step_content in enumerate(steps):
                step = TodoStep(
                    id=self._generate_id("step"),
                    task_id=task.id,
                    content=step_content,
                    order=i,
                )
                task.steps.append(step)

        phase.tasks.append(task)
        self._save_data()

        await self._create_verification_document(task)

        return task

    async def create_step(
        self,
        task_id: str,
        content: str,
        priority: TodoPriority = TodoPriority.MEDIUM,
        dependencies: list[str] | None = None,
    ) -> TodoStep | None:
        task = self._find_task(task_id)
        if not task:
            return None

        step = TodoStep(
            id=self._generate_id("step"),
            task_id=task_id,
            content=content,
            priority=priority,
            order=len(task.steps),
            dependencies=dependencies or [],
        )

        task.steps.append(step)
        self._save_data()

        return step

    def _find_task(self, task_id: str) -> TodoTask | None:
        for phase in self.phases.values():
            for task in phase.tasks:
                if task.id == task_id:
                    return task
        return None

    def _find_phase_by_task(self, task_id: str) -> TodoPhase | None:
        for phase in self.phases.values():
            for task in phase.tasks:
                if task.id == task_id:
                    return phase
        return None

    async def _create_verification_document(self, task: TodoTask) -> None:
        phase = self._find_phase_by_task(task.id)
        phase_title = phase.title if phase else "Unknown"

        acceptance_criteria = self._generate_acceptance_criteria(task)

        doc = VerificationDocument(
            id=self._generate_id("verify"),
            task_id=task.id,
            title=f"验收文档: {task.title}",
            description=f"任务: {task.title}\n阶段: {phase_title}",
            acceptance_criteria=acceptance_criteria,
        )

        task.verification_document = doc
        self._save_data()

        doc_path = self._verification_dir / f"{doc.id}.md"
        doc_content = self._format_verification_document(doc, task)
        doc_path.write_text(doc_content, encoding="utf-8")

    def _generate_acceptance_criteria(self, task: TodoTask) -> list[str]:
        criteria = []

        criteria.append(f"任务标题: {task.title}")

        if task.description:
            criteria.append(f"任务描述: {task.description}")

        if task.steps:
            criteria.append("完成以下所有步骤:")
            for step in task.steps:
                criteria.append(f"  - {step.content}")

        criteria.append("所有步骤状态为已完成")
        criteria.append("无遗留问题或已记录后续处理方案")

        return criteria

    def _format_verification_document(
        self,
        doc: VerificationDocument,
        task: TodoTask,
    ) -> str:
        lines = [
            f"# {doc.title}",
            "",
            f"**任务ID**: {task.id}",
            f"**创建时间**: {datetime.fromtimestamp(doc.created_at).strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 验收标准",
            "",
        ]

        for criterion in doc.acceptance_criteria:
            lines.append(f"- {criterion}")

        lines.extend([
            "",
            "## 验收结果",
            "",
            f"- **状态**: {'已验收' if doc.is_verified else '待验收'}",
        ])

        if doc.verified_at:
            lines.append(f"- **验收时间**: {datetime.fromtimestamp(doc.verified_at).strftime('%Y-%m-%d %H:%M:%S')}")

        if doc.verification_results:
            lines.extend([
                "",
                "### 验收详情",
                "",
            ])
            for result in doc.verification_results:
                lines.append(f"- {result}")

        lines.extend([
            "",
            "## 签名",
            "",
            f"验收人: {doc.verified_by}",
        ])

        return "\n".join(lines)

    async def complete_step(self, step_id: str) -> bool:
        step = self._find_step(step_id)
        if not step:
            return False

        step.status = TodoStatus.COMPLETED
        step.completed_at = datetime.now().timestamp()

        task = self._find_task(step.task_id)
        if task:
            await self._check_task_completion(task)

        self._save_data()
        return True

    def _find_step(self, step_id: str) -> TodoStep | None:
        for phase in self.phases.values():
            for task in phase.tasks:
                for step in task.steps:
                    if step.id == step_id:
                        return step
        return None

    async def _check_task_completion(self, task: TodoTask) -> None:
        if not task.steps:
            return

        all_completed = all(
            s.status == TodoStatus.COMPLETED for s in task.steps
        )

        if all_completed and task.status != TodoStatus.COMPLETED:
            task.status = TodoStatus.COMPLETED
            task.completed_at = datetime.now().timestamp()

            await self._verify_task(task)

            phase = self._find_phase_by_task(task.id)
            if phase:
                await self._check_phase_completion(phase)

    async def _verify_task(self, task: TodoTask) -> None:
        if not task.verification_document:
            return

        doc = task.verification_document
        doc.is_verified = True
        doc.verified_at = datetime.now().timestamp()
        doc.verification_results = [
            f"所有 {len(task.steps)} 个步骤已完成",
            "任务进度: 100%",
            "验收通过",
        ]

        doc_path = self._verification_dir / f"{doc.id}.md"
        doc_content = self._format_verification_document(doc, task)
        doc_path.write_text(doc_content, encoding="utf-8")

    async def _check_phase_completion(self, phase: TodoPhase) -> None:
        if not phase.tasks:
            return

        all_completed = all(
            t.status == TodoStatus.COMPLETED for t in phase.tasks
        )

        if all_completed and phase.status != TodoStatus.COMPLETED:
            phase.status = TodoStatus.COMPLETED
            phase.completed_at = datetime.now().timestamp()

            await self._conduct_phase_reflection(phase)

    async def _conduct_phase_reflection(self, phase: TodoPhase) -> None:
        reflection_rounds = min(
            max(phase.min_reflections, phase.reflection_count + 1),
            phase.max_reflections
        )

        while phase.reflection_count < reflection_rounds:
            phase.reflection_count += 1

            reflection = await self._generate_reflection(phase)
            if reflection:
                phase.reflections.append(reflection)

        self._save_data()

    async def _generate_reflection(
        self,
        phase: TodoPhase,
        llm_client: Any | None = None,
    ) -> ReflectionResult | None:
        reflection = ReflectionResult(
            id=self._generate_id("reflect"),
            phase_id=phase.id,
            round_number=phase.reflection_count,
            content=self._generate_reflection_content(phase),
            insights=self._extract_insights(phase),
            improvements=self._extract_improvements(phase),
        )

        return reflection

    def _generate_reflection_content(self, phase: TodoPhase) -> str:
        completed_tasks = sum(1 for t in phase.tasks if t.status == TodoStatus.COMPLETED)
        total_tasks = len(phase.tasks)
        total_steps = sum(len(t.steps) for t in phase.tasks)
        completed_steps = sum(
            sum(1 for s in t.steps if s.status == TodoStatus.COMPLETED)
            for t in phase.tasks
        )

        return (
            f"阶段 '{phase.title}' 反思 (第{phase.reflection_count}轮)\n"
            f"完成进度: {completed_tasks}/{total_tasks} 任务, "
            f"{completed_steps}/{total_steps} 步骤"
        )

    def _extract_insights(self, phase: TodoPhase) -> list[str]:
        insights = []

        for task in phase.tasks:
            if task.status == TodoStatus.COMPLETED:
                insights.append(f"任务 '{task.title}' 成功完成")

                blocked_steps = [s for s in task.steps if s.status == TodoStatus.BLOCKED]
                if blocked_steps:
                    insights.append(f"任务 '{task.title}' 有 {len(blocked_steps)} 个步骤曾被阻塞")

        return insights

    def _extract_improvements(self, phase: TodoPhase) -> list[str]:
        improvements = []

        avg_steps_per_task = sum(len(t.steps) for t in phase.tasks) / max(len(phase.tasks), 1)
        if avg_steps_per_task > 10:
            improvements.append("建议将大任务拆分为更小的任务")

        blocked_count = sum(
            sum(1 for s in t.steps if s.status == TodoStatus.BLOCKED)
            for t in phase.tasks
        )
        if blocked_count > 0:
            improvements.append(f"共有 {blocked_count} 个步骤被阻塞，建议优化依赖关系")

        return improvements

    async def update_step_status(
        self,
        step_id: str,
        status: TodoStatus,
    ) -> bool:
        step = self._find_step(step_id)
        if not step:
            return False

        step.status = status

        if status == TodoStatus.IN_PROGRESS and not step.started_at:
            step.started_at = datetime.now().timestamp()
        elif status == TodoStatus.COMPLETED:
            step.completed_at = datetime.now().timestamp()

            task = self._find_task(step.task_id)
            if task:
                await self._check_task_completion(task)

        self._save_data()
        return True

    def get_phase(self, phase_id: str) -> TodoPhase | None:
        return self.phases.get(phase_id)

    def get_task(self, task_id: str) -> TodoTask | None:
        return self._find_task(task_id)

    def get_step(self, step_id: str) -> TodoStep | None:
        return self._find_step(step_id)

    def list_phases(self, status: TodoStatus | None = None) -> list[TodoPhase]:
        phases = list(self.phases.values())
        if status:
            phases = [p for p in phases if p.status == status]
        return sorted(phases, key=lambda x: x.order)

    def get_statistics(self) -> dict[str, Any]:
        total_phases = len(self.phases)
        total_tasks = sum(len(p.tasks) for p in self.phases.values())
        total_steps = sum(
            sum(len(t.steps) for t in p.tasks)
            for p in self.phases.values()
        )

        completed_phases = sum(1 for p in self.phases.values() if p.status == TodoStatus.COMPLETED)
        completed_tasks = sum(
            sum(1 for t in p.tasks if t.status == TodoStatus.COMPLETED)
            for p in self.phases.values()
        )
        completed_steps = sum(
            sum(
                sum(1 for s in t.steps if s.status == TodoStatus.COMPLETED)
                for t in p.tasks
            )
            for p in self.phases.values()
        )

        return {
            "total_phases": total_phases,
            "total_tasks": total_tasks,
            "total_steps": total_steps,
            "completed_phases": completed_phases,
            "completed_tasks": completed_tasks,
            "completed_steps": completed_steps,
            "progress": {
                "phases": completed_phases / max(total_phases, 1),
                "tasks": completed_tasks / max(total_tasks, 1),
                "steps": completed_steps / max(total_steps, 1),
            },
        }

    def format_todo_list(self) -> str:
        lines = ["# Todo List", ""]

        for phase in sorted(self.phases.values(), key=lambda x: x.order):
            status_icon = self._get_status_icon(phase.status)
            progress = phase.get_progress() * 100

            lines.append(f"## {status_icon} {phase.title} ({progress:.0f}%)")

            if phase.description:
                lines.append(f"   {phase.description}")

            for task in sorted(phase.tasks, key=lambda x: x.order):
                task_icon = self._get_status_icon(task.status)
                task_progress = task.get_progress() * 100

                lines.append(f"### {task_icon} {task.title} ({task_progress:.0f}%)")

                for step in sorted(task.steps, key=lambda x: x.order):
                    step_icon = self._get_status_icon(step.status)
                    lines.append(f"- {step_icon} {step.content}")

                lines.append("")

            if phase.reflections:
                lines.append(f"**反思轮数**: {len(phase.reflections)}")
                lines.append("")

        return "\n".join(lines)

    def _get_status_icon(self, status: TodoStatus) -> str:
        icons = {
            TodoStatus.PENDING: "[ ]",
            TodoStatus.IN_PROGRESS: "[>]",
            TodoStatus.COMPLETED: "[x]",
            TodoStatus.BLOCKED: "[!]",
            TodoStatus.CANCELLED: "[-]",
        }
        return icons.get(status, "[ ]")


todo_manager = TodoManager()
