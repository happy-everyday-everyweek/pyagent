"""
PyAgent Web服务 - 路由模块

提供所有API路由的统一入口。
"""

from src.web.routes.execution_routes import router as execution_router
from src.web.routes.execution_routes import (
    get_collaboration_manager,
    set_collaboration_manager,
)
from src.web.routes.task_routes import router as task_router
from src.web.routes.task_routes import get_executor_agent, set_executor_agent
from src.web.routes.todo_routes import router as todo_router
from src.web.routes.hot_reload import router as hot_reload_router
from src.web.routes.hot_reload import init_hot_reload
from src.web.routes.document_routes import router as document_router
from src.web.routes.video_routes import router as video_router
from src.web.routes.domain_routes import router as domain_router
from src.web.routes.storage_routes import router as storage_router
from src.web.routes.human_tasks_routes import router as human_tasks_router
from src.web.routes.calendar_routes import router as calendar_router
from src.web.routes.verification_routes import router as verification_router
from src.web.routes.slash_commands import router as slash_commands_router
from src.web.routes.settings_routes import router as settings_router

__all__ = [
    "todo_router",
    "task_router",
    "execution_router",
    "hot_reload_router",
    "document_router",
    "video_router",
    "domain_router",
    "storage_router",
    "human_tasks_router",
    "calendar_router",
    "verification_router",
    "slash_commands_router",
    "settings_router",
    "set_executor_agent",
    "get_executor_agent",
    "set_collaboration_manager",
    "get_collaboration_manager",
    "init_hot_reload",
]
