"""Research planner and validator for task decomposition."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ResearchTask:
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: list[str] = field(default_factory=list)
    subtasks: list["ResearchTask"] = field(default_factory=list)
    result: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None


@dataclass
class ResearchPlan:
    id: str
    query: str
    tasks: list[ResearchTask] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class ResearchPlanner:
    """Decomposes complex queries into research tasks."""

    def __init__(self, max_depth: int = 3, max_tasks: int = 10):
        self._max_depth = max_depth
        self._max_tasks = max_tasks
        self._plans: dict[str, ResearchPlan] = {}

    async def create_plan(self, query: str, context: dict[str, Any] | None = None) -> ResearchPlan:
        import uuid

        plan = ResearchPlan(id=str(uuid.uuid4()), query=query)
        tasks = await self._decompose_query(query, context)
        plan.tasks = tasks[: self._max_tasks]
        self._plans[plan.id] = plan
        logger.info("Created research plan with %d tasks", len(plan.tasks))
        return plan

    async def _decompose_query(self, query: str, context: dict[str, Any] | None = None) -> list[ResearchTask]:
        import uuid

        tasks = []

        keywords = self._extract_keywords(query)
        for i, keyword in enumerate(keywords[:5]):
            task = ResearchTask(
                id=str(uuid.uuid4()),
                title=f"Research: {keyword}",
                description=f"Find information about '{keyword}' related to the main query",
                priority=TaskPriority.HIGH if i < 2 else TaskPriority.MEDIUM,
            )
            tasks.append(task)

        analysis_task = ResearchTask(
            id=str(uuid.uuid4()),
            title="Synthesize findings",
            description="Combine all research findings into a coherent answer",
            priority=TaskPriority.HIGH,
            dependencies=[t.id for t in tasks],
        )
        tasks.append(analysis_task)

        return tasks

    def _extract_keywords(self, text: str) -> list[str]:
        import re

        words = re.findall(r"\b[A-Z][a-z]+\b|\b[a-z]{4,}\b", text)
        stop_words = {"about", "with", "from", "have", "this", "that", "what", "when", "where", "which", "would", "could", "should"}
        return [w.lower() for w in words if w.lower() not in stop_words][:10]

    def get_plan(self, plan_id: str) -> ResearchPlan | None:
        return self._plans.get(plan_id)

    def update_task_status(self, plan_id: str, task_id: str, status: TaskStatus, result: str | None = None) -> bool:
        plan = self._plans.get(plan_id)
        if not plan:
            return False

        for task in plan.tasks:
            if task.id == task_id:
                task.status = status
                if result:
                    task.result = result
                if status == TaskStatus.COMPLETED:
                    task.completed_at = datetime.now()
                plan.updated_at = datetime.now()
                return True
        return False

    def get_next_task(self, plan_id: str) -> ResearchTask | None:
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        completed_ids = {t.id for t in plan.tasks if t.status == TaskStatus.COMPLETED}

        for task in plan.tasks:
            if task.status == TaskStatus.PENDING:
                if all(dep_id in completed_ids for dep_id in task.dependencies):
                    return task
        return None


class ResearchValidator:
    """Validates research results and detects loops."""

    def __init__(self, max_iterations: int = 10, similarity_threshold: float = 0.9):
        self._max_iterations = max_iterations
        self._similarity_threshold = similarity_threshold
        self._iteration_counts: dict[str, int] = {}
        self._previous_results: dict[str, list[str]] = {}

    def check_loop(self, plan_id: str, result: str) -> bool:
        count = self._iteration_counts.get(plan_id, 0)
        count += 1
        self._iteration_counts[plan_id] = count

        if count > self._max_iterations:
            logger.warning("Max iterations reached for plan %s", plan_id)
            return True

        previous = self._previous_results.get(plan_id, [])
        for prev_result in previous:
            if self._similarity(result, prev_result) > self._similarity_threshold:
                logger.warning("Loop detected for plan %s", plan_id)
                return True

        previous.append(result)
        self._previous_results[plan_id] = previous[-5:]
        return False

    def _similarity(self, text1: str, text2: str) -> float:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    def validate_result(self, task: ResearchTask, result: str) -> dict[str, Any]:
        validation = {"valid": True, "issues": [], "score": 1.0}

        if not result or len(result) < 10:
            validation["valid"] = False
            validation["issues"].append("Result is too short")
            validation["score"] = 0.0

        if task.description.lower() in result.lower():
            validation["issues"].append("Result contains task description")
            validation["score"] *= 0.8

        return validation

    def reset(self, plan_id: str) -> None:
        self._iteration_counts.pop(plan_id, None)
        self._previous_results.pop(plan_id, None)


_planner: ResearchPlanner | None = None
_validator: ResearchValidator | None = None


def get_research_planner() -> ResearchPlanner:
    global _planner
    if _planner is None:
        _planner = ResearchPlanner()
    return _planner


def get_research_validator() -> ResearchValidator:
    global _validator
    if _validator is None:
        _validator = ResearchValidator()
    return _validator
