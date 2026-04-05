"""
PyAgent Web服务 - 任务API路由

提供任务管理的API接口。
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.execution.task import Task, TaskStatus, TaskResult, TaskState, WaitingType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

_task_store: dict[str, Task] = {}
_executor_agent = None


def set_executor_agent(agent: Any) -> None:
    """设置执行Agent实例"""
    global _executor_agent
    _executor_agent = agent


def get_executor_agent() -> Any:
    """获取执行Agent实例"""
    return _executor_agent


class TaskCreate(BaseModel):
    """创建任务请求"""
    prompt: str
    context: Optional[dict[str, Any]] = None
    priority: Optional[int] = 0
    tags: Optional[list[str]] = None


class TaskResponse(BaseModel):
    """任务响应"""
    id: str
    prompt: str
    status: str
    state: str = "active"
    progress: float = 0.0
    display_status: str = ""
    waiting_type: Optional[str] = None
    waiting_message: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    priority: int = 0
    tags: list[str] = []


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: list[TaskResponse]
    total: int


class TaskStatusUpdate(BaseModel):
    """任务状态更新"""
    status: str


class UserRespondRequest(BaseModel):
    """用户响应请求"""
    response: str
    confirmed: bool = True


def _create_task_response(task: Task) -> TaskResponse:
    """创建任务响应对象"""
    return TaskResponse(
        id=task.id,
        prompt=task.prompt,
        status=task.status.value,
        state=task.state.value,
        progress=task.progress,
        display_status=task.get_display_status(),
        waiting_type=task.waiting_type.value if task.waiting_type else None,
        waiting_message=task.waiting_message,
        result=task.result,
        error=task.error,
        priority=task.priority,
        tags=task.tags
    )


@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate) -> TaskResponse:
    """创建新任务"""
    new_task = Task(
        prompt=task.prompt,
        context=task.context or {},
        priority=task.priority or 0,
        tags=task.tags or []
    )
    
    _task_store[new_task.id] = new_task
    
    return _create_task_response(new_task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str) -> TaskResponse:
    """获取任务详情"""
    if task_id in _task_store:
        task = _task_store[task_id]
        return _create_task_response(task)
    
    if _executor_agent:
        status = await _executor_agent.get_task_status(task_id)
        if status:
            return TaskResponse(
                id=task_id,
                prompt=status.get("task", ""),
                status=status.get("status", "unknown"),
                state=status.get("state", "active"),
                progress=status.get("progress", 0.0),
                display_status=status.get("display_status", ""),
                waiting_type=status.get("waiting_type"),
                waiting_message=status.get("waiting_message"),
                result=status.get("result"),
                error=status.get("error"),
                priority=0,
                tags=[]
            )
    
    raise HTTPException(status_code=404, detail="Task not found")


@router.get("/", response_model=TaskListResponse)
async def list_tasks(status: Optional[str] = None) -> TaskListResponse:
    """列出任务"""
    tasks = list(_task_store.values())
    
    if status:
        try:
            filter_status = TaskStatus(status)
            tasks = [t for t in tasks if t.status == filter_status]
        except ValueError:
            pass
    
    task_responses = [_create_task_response(t) for t in tasks]
    
    return TaskListResponse(tasks=task_responses, total=len(task_responses))


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str) -> dict[str, Any]:
    """取消任务"""
    if task_id in _task_store:
        task = _task_store[task_id]
        if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task.mark_cancelled()
            return {"success": True, "task_id": task_id, "status": "cancelled"}
        return {"success": False, "error": "Task cannot be cancelled"}
    
    if _executor_agent:
        success = await _executor_agent.cancel_task(task_id)
        return {"success": success, "task_id": task_id}
    
    raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/pause", response_model=TaskResponse)
async def pause_task(task_id: str) -> TaskResponse:
    """暂停任务"""
    if task_id not in _task_store:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = _task_store[task_id]
    
    if task.status != TaskStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Only running tasks can be paused")
    
    if task.state == TaskState.PAUSED:
        raise HTTPException(status_code=400, detail="Task is already paused")
    
    task.pause()
    logger.info(f"Task {task_id} paused")
    
    return _create_task_response(task)


@router.post("/{task_id}/resume", response_model=TaskResponse)
async def resume_task(task_id: str) -> TaskResponse:
    """恢复任务"""
    if task_id not in _task_store:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = _task_store[task_id]
    
    if task.state != TaskState.PAUSED:
        raise HTTPException(status_code=400, detail="Only paused tasks can be resumed")
    
    task.resume()
    logger.info(f"Task {task_id} resumed")
    
    return _create_task_response(task)


@router.post("/{task_id}/respond", response_model=TaskResponse)
async def respond_to_task(task_id: str, request: UserRespondRequest) -> TaskResponse:
    """用户响应任务（确认或协助）"""
    if task_id not in _task_store:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = _task_store[task_id]
    
    if task.state != TaskState.WAITING:
        raise HTTPException(status_code=400, detail="Task is not waiting for user response")
    
    task.user_responded()
    logger.info(f"User responded to task {task_id}: confirmed={request.confirmed}")
    
    return _create_task_response(task)


@router.post("/{task_id}/execute")
async def execute_task(task_id: str) -> dict[str, Any]:
    """执行任务"""
    if task_id not in _task_store:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = _task_store[task_id]
    
    if task.status != TaskStatus.PENDING:
        raise HTTPException(status_code=400, detail="Task is not in pending status")
    
    if not _executor_agent:
        raise HTTPException(status_code=503, detail="Executor agent not initialized")
    
    try:
        result = await _executor_agent.execute(task)
        
        return {
            "success": result.success,
            "task_id": task_id,
            "result": result.data if result.success else None,
            "error": result.error,
            "duration": result.duration
        }
    except Exception as e:
        logger.error(f"Task execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}")
async def delete_task(task_id: str) -> dict[str, Any]:
    """删除任务"""
    if task_id not in _task_store:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = _task_store[task_id]
    
    if task.status == TaskStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Cannot delete running task")
    
    del _task_store[task_id]
    
    return {"success": True, "task_id": task_id}


@router.get("/statistics/summary")
async def get_task_statistics() -> dict[str, Any]:
    """获取任务统计信息"""
    total = len(_task_store)
    by_status = {}
    
    for status in TaskStatus:
        count = sum(1 for t in _task_store.values() if t.status == status)
        if count > 0:
            by_status[status.value] = count
    
    return {
        "total": total,
        "by_status": by_status
    }
