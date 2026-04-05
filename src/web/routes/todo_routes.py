"""
PyAgent Web服务 - Todo API路由

提供Todo列表和Mate模式的API接口。
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.todo import (
    TodoPriority,
    TodoStatus,
    mate_mode_manager,
    todo_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/todo", tags=["todo"])


class CreatePhaseRequest(BaseModel):
    """创建阶段请求"""
    title: str
    description: str = ""
    priority: str = "medium"
    min_reflections: int = 2
    max_reflections: int = 5


class CreateTaskRequest(BaseModel):
    """创建任务请求"""
    phase_id: str
    title: str
    description: str = ""
    priority: str = "medium"
    steps: list[str] | None = None


class CreateStepRequest(BaseModel):
    """创建步骤请求"""
    task_id: str
    content: str
    priority: str = "medium"
    dependencies: list[str] | None = None


class UpdateStepStatusRequest(BaseModel):
    """更新步骤状态请求"""
    status: str


class MateModeToggleRequest(BaseModel):
    """Mate模式切换请求"""
    enabled: bool


class CollaborationModeRequest(BaseModel):
    """协作模式请求"""
    enabled: bool


@router.post("/phases")
async def create_phase(request: CreatePhaseRequest) -> dict[str, Any]:
    """创建阶段"""
    priority = TodoPriority(request.priority)

    phase = await todo_manager.create_phase(
        title=request.title,
        description=request.description,
        priority=priority,
        min_reflections=request.min_reflections,
        max_reflections=request.max_reflections,
    )

    return phase.to_dict()


@router.get("/phases")
async def list_phases(status: str | None = None) -> list[dict[str, Any]]:
    """列出所有阶段"""
    todo_status = TodoStatus(status) if status else None
    phases = todo_manager.list_phases(status=todo_status)
    return [p.to_dict() for p in phases]


@router.get("/phases/{phase_id}")
async def get_phase(phase_id: str) -> dict[str, Any]:
    """获取阶段详情"""
    phase = todo_manager.get_phase(phase_id)
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")
    return phase.to_dict()


@router.post("/tasks")
async def create_task(request: CreateTaskRequest) -> dict[str, Any]:
    """创建任务"""
    priority = TodoPriority(request.priority)

    task = await todo_manager.create_task(
        phase_id=request.phase_id,
        title=request.title,
        description=request.description,
        priority=priority,
        steps=request.steps,
    )

    if not task:
        raise HTTPException(status_code=404, detail="Phase not found")

    return task.to_dict()


@router.get("/tasks/{task_id}")
async def get_task(task_id: str) -> dict[str, Any]:
    """获取任务详情"""
    task = todo_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.post("/steps")
async def create_step(request: CreateStepRequest) -> dict[str, Any]:
    """创建步骤"""
    priority = TodoPriority(request.priority)

    step = await todo_manager.create_step(
        task_id=request.task_id,
        content=request.content,
        priority=priority,
        dependencies=request.dependencies,
    )

    if not step:
        raise HTTPException(status_code=404, detail="Task not found")

    return step.to_dict()


@router.get("/steps/{step_id}")
async def get_step(step_id: str) -> dict[str, Any]:
    """获取步骤详情"""
    step = todo_manager.get_step(step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    return step.to_dict()


@router.put("/steps/{step_id}/status")
async def update_step_status(step_id: str, request: UpdateStepStatusRequest) -> dict[str, Any]:
    """更新步骤状态"""
    status = TodoStatus(request.status)

    success = await todo_manager.update_step_status(step_id, status)

    if not success:
        raise HTTPException(status_code=404, detail="Step not found")

    return {"success": True, "step_id": step_id, "status": request.status}


@router.post("/steps/{step_id}/complete")
async def complete_step(step_id: str) -> dict[str, Any]:
    """完成步骤"""
    success = await todo_manager.complete_step(step_id)

    if not success:
        raise HTTPException(status_code=404, detail="Step not found")

    return {"success": True, "step_id": step_id}


@router.get("/statistics")
async def get_statistics() -> dict[str, Any]:
    """获取统计信息"""
    return todo_manager.get_statistics()


@router.get("/list")
async def get_todo_list() -> dict[str, str]:
    """获取格式化的Todo列表"""
    return {"content": todo_manager.format_todo_list()}


@router.get("/mate-mode")
async def get_mate_mode_status() -> dict[str, Any]:
    """获取Mate模式状态"""
    return mate_mode_manager.to_dict()


@router.post("/mate-mode/toggle")
async def toggle_mate_mode(request: MateModeToggleRequest) -> dict[str, Any]:
    """切换Mate模式"""
    if request.enabled:
        mate_mode_manager.enable()
    else:
        mate_mode_manager.disable()

    return mate_mode_manager.to_dict()


@router.post("/mate-mode/collaboration")
async def set_collaboration_mode(request: CollaborationModeRequest) -> dict[str, Any]:
    """设置协作模式"""
    mate_mode_manager.set_collaboration_mode(request.enabled)
    return mate_mode_manager.to_dict()


@router.get("/mate-mode/collaboration")
async def get_collaboration_mode() -> dict[str, Any]:
    """获取协作模式状态"""
    return {"collaboration_enabled": mate_mode_manager.is_collaboration_enabled()}
