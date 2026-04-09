"""
PyAgent Web服务 - 执行模块API路由

提供执行模块管理的API接口，包括协作模式配置。
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.execution.collaboration import CollaborationMode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/execution", tags=["execution"])

_collaboration_manager = None


def set_collaboration_manager(manager: Any) -> None:
    """设置协作管理器实例"""
    global _collaboration_manager
    _collaboration_manager = manager


def get_collaboration_manager() -> Any:
    """获取协作管理器实例"""
    return _collaboration_manager


class CollaborationModeRequest(BaseModel):
    """协作模式请求"""
    enabled: bool


class CollaborationConfigRequest(BaseModel):
    """协作配置请求"""
    max_agents: int | None = 3
    parallel_timeout: float | None = 300.0
    retry_count: int | None = 2
    failover_enabled: bool | None = True
    enable_parallel: bool | None = True
    auto_assign: bool | None = True


class ExecutionRequest(BaseModel):
    """执行请求"""
    task_id: str


class ExecutionResponse(BaseModel):
    """执行响应"""
    success: bool
    result: Any | None = None
    error: str | None = None
    duration: float | None = None


class ExecutionPlanResponse(BaseModel):
    """执行计划响应"""
    task_id: str
    strategy: str
    subtask_count: int
    subtasks: list[dict[str, Any]]


class StatisticsResponse(BaseModel):
    """统计信息响应"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_duration: float
    parallel_tasks: int
    sequential_tasks: int
    failover_count: int


@router.post("/collaboration/mode")
async def set_collaboration_mode(mode: CollaborationModeRequest) -> dict[str, Any]:
    """设置协作模式"""
    if not _collaboration_manager:
        raise HTTPException(status_code=503, detail="Collaboration manager not initialized")

    new_mode = CollaborationMode.MULTI if mode.enabled else CollaborationMode.SINGLE
    _collaboration_manager.set_mode(new_mode)

    return {
        "success": True,
        "mode": new_mode.value,
        "multi_agent_enabled": _collaboration_manager.is_multi_agent_enabled()
    }


@router.get("/collaboration/mode")
async def get_collaboration_mode() -> dict[str, Any]:
    """获取当前协作模式"""
    if not _collaboration_manager:
        raise HTTPException(status_code=503, detail="Collaboration manager not initialized")

    config = _collaboration_manager.get_config()

    return {
        "mode": config.mode.value,
        "multi_agent_enabled": _collaboration_manager.is_multi_agent_enabled(),
        "config": config.to_dict()
    }


@router.post("/collaboration/config")
async def set_collaboration_config(config: CollaborationConfigRequest) -> dict[str, Any]:
    """设置协作配置"""
    if not _collaboration_manager:
        raise HTTPException(status_code=503, detail="Collaboration manager not initialized")

    current_config = _collaboration_manager.get_config()

    if config.max_agents is not None:
        current_config.max_agents = config.max_agents
    if config.parallel_timeout is not None:
        current_config.parallel_timeout = config.parallel_timeout
    if config.retry_count is not None:
        current_config.retry_count = config.retry_count
    if config.failover_enabled is not None:
        current_config.failover_enabled = config.failover_enabled
    if config.enable_parallel is not None:
        current_config.enable_parallel = config.enable_parallel
    if config.auto_assign is not None:
        current_config.auto_assign = config.auto_assign

    return {
        "success": True,
        "config": current_config.to_dict()
    }


@router.get("/collaboration/config")
async def get_collaboration_config() -> dict[str, Any]:
    """获取协作配置"""
    if not _collaboration_manager:
        raise HTTPException(status_code=503, detail="Collaboration manager not initialized")

    config = _collaboration_manager.get_config()
    return {"config": config.to_dict()}


@router.post("/execute")
async def execute_task(request: ExecutionRequest) -> ExecutionResponse:
    """执行任务"""
    if not _collaboration_manager:
        raise HTTPException(status_code=503, detail="Collaboration manager not initialized")

    from src.execution.task import Task

    from .task_routes import _task_store

    if request.task_id in _task_store:
        task = _task_store[request.task_id]
    else:
        task = Task(id=request.task_id, prompt="")

    try:
        result = await _collaboration_manager.execute(task)

        return ExecutionResponse(
            success=result.success,
            result=result.data if result.success else None,
            error=result.error,
            duration=result.duration
        )
    except Exception as e:
        logger.error(f"Execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plan/{task_id}", response_model=ExecutionPlanResponse)
async def get_execution_plan(task_id: str) -> ExecutionPlanResponse:
    """获取执行计划"""
    if not _collaboration_manager:
        raise HTTPException(status_code=503, detail="Collaboration manager not initialized")

    plan = _collaboration_manager.get_execution_plan(task_id)

    if not plan:
        raise HTTPException(status_code=404, detail="Execution plan not found")

    return ExecutionPlanResponse(
        task_id=task_id,
        strategy=plan.strategy.value,
        subtask_count=len(plan.subtasks),
        subtasks=[s.to_dict() for s in plan.subtasks]
    )


@router.get("/statistics", response_model=StatisticsResponse)
async def get_execution_statistics() -> StatisticsResponse:
    """获取执行统计信息"""
    if not _collaboration_manager:
        raise HTTPException(status_code=503, detail="Collaboration manager not initialized")

    stats = _collaboration_manager.get_statistics()

    return StatisticsResponse(
        total_tasks=stats.total_tasks,
        completed_tasks=stats.completed_tasks,
        failed_tasks=stats.failed_tasks,
        total_duration=stats.total_duration,
        parallel_tasks=stats.parallel_tasks,
        sequential_tasks=stats.sequential_tasks,
        failover_count=stats.failover_count
    )


@router.post("/statistics/reset")
async def reset_statistics() -> dict[str, Any]:
    """重置统计信息"""
    if not _collaboration_manager:
        raise HTTPException(status_code=503, detail="Collaboration manager not initialized")

    _collaboration_manager.reset_statistics()

    return {"success": True}


@router.get("/executors")
async def list_executors() -> dict[str, Any]:
    """列出所有执行器"""
    if not _collaboration_manager:
        raise HTTPException(status_code=503, detail="Collaboration manager not initialized")

    executors = _collaboration_manager.get_all_executors()

    return {
        "count": len(executors),
        "executors": [
            {
                "id": eid,
                "running_tasks": len(executor.get_running_tasks()),
                "queue_size": executor.get_queue_size()
            }
            for eid, executor in executors.items()
        ]
    }


@router.delete("/plan/{task_id}")
async def clear_execution_plan(task_id: str) -> dict[str, Any]:
    """清除执行计划"""
    if not _collaboration_manager:
        raise HTTPException(status_code=503, detail="Collaboration manager not initialized")

    _collaboration_manager.clear_execution_plan(task_id)

    return {"success": True, "task_id": task_id}
