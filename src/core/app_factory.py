"""
PyAgent 统一应用工厂

提供统一的FastAPI应用创建和管理,支持Web端和移动端共享同一后端。
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.core.platform import PlatformAdapter, PlatformConfig, get_platform_adapter
from src.execution.collaboration import CollaborationManager
from src.execution.executor_agent import ExecutorAgent
from src.execution.tools.file_tools import FileListTool, FileReadTool, FileWriteTool
from src.execution.tools.registry import ToolRegistry
from src.execution.tools.shell_tool import ShellTool
from src.execution.tools.web_tools import WebFetchTool, WebRequestTool
from src.interaction.heart_flow.heartf_chatting import HeartFChatting
from src.llm import create_client_from_env, get_model_config_loader
from src.mcp import mcp_manager
from src.skills import skill_loader, skill_registry
from src.web.routes.calendar_routes import router as calendar_router
from src.web.routes.document_routes import router as document_router
from src.web.routes.domain_routes import router as domain_router
from src.web.routes.execution_routes import router as execution_router
from src.web.routes.human_tasks_routes import router as human_tasks_router
from src.web.routes.settings_routes import router as settings_router
from src.web.routes.storage_routes import router as storage_router
from src.web.routes.task_routes import router as task_router
from src.web.routes.todo_routes import router as todo_router
from src.web.routes.video_routes import router as video_router

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str
    chat_id: str | None = "default"
    platform: str | None = "web"


class ChatResponse(BaseModel):
    success: bool
    response: str
    chat_id: str
    actions: list[dict[str, Any]] = []


class ConnectionManager:
    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        for connection in self._connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()

_chat_agent: HeartFChatting | None = None
_executor_agent: ExecutorAgent | None = None
_collaboration_manager: CollaborationManager | None = None
_tool_registry: ToolRegistry | None = None


def get_chat_agent() -> HeartFChatting | None:
    return _chat_agent


def get_executor_agent() -> ExecutorAgent | None:
    return _executor_agent


def get_collaboration_manager() -> CollaborationManager | None:
    return _collaboration_manager


def get_tool_registry() -> ToolRegistry | None:
    return _tool_registry


def set_chat_agent(agent: HeartFChatting) -> None:
    global _chat_agent
    _chat_agent = agent


def set_executor_agent(agent: ExecutorAgent) -> None:
    global _executor_agent
    _executor_agent = agent


def set_collaboration_manager(manager_obj: CollaborationManager) -> None:
    global _collaboration_manager
    _collaboration_manager = manager_obj


def set_tool_registry(registry: ToolRegistry) -> None:
    global _tool_registry
    _tool_registry = registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _chat_agent, _executor_agent, _collaboration_manager, _tool_registry

    logger.info("Starting PyAgent...")

    try:
        llm_client = create_client_from_env()
    except Exception:
        llm_client = None
        logger.warning("LLM client not configured")

    _tool_registry = ToolRegistry()
    _tool_registry.register(ShellTool())
    _tool_registry.register(FileReadTool())
    _tool_registry.register(FileWriteTool())
    _tool_registry.register(FileListTool())
    _tool_registry.register(WebRequestTool())
    _tool_registry.register(WebFetchTool())

    platform_adapter = get_platform_adapter()
    if platform_adapter.is_android() or platform_adapter.is_ios():
        from src.mobile.tool_registry import register_mobile_tools

        register_mobile_tools(_tool_registry)

    _executor_agent = ExecutorAgent(llm_client=llm_client, tool_registry=_tool_registry)

    set_executor_agent(_executor_agent)

    _collaboration_manager = CollaborationManager(
        llm_client=llm_client, tool_registry=_tool_registry
    )
    set_collaboration_manager(_collaboration_manager)

    _chat_agent = HeartFChatting(chat_id="default", config={"llm_client": llm_client})

    logger.info("PyAgent started successfully")

    yield

    logger.info("Shutting down PyAgent...")

    if _chat_agent:
        await _chat_agent.stop()

    logger.info("PyAgent shutdown complete")


def create_app(
    config: PlatformConfig | None = None,
    title: str = "PyAgent API",
    description: str = "Python Agent API",
    version: str = "0.1.0",
) -> FastAPI:
    platform_adapter = get_platform_adapter(config)

    app = FastAPI(title=title, description=description, version=version, lifespan=lifespan)

    if platform_adapter.config.enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=platform_adapter.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    _register_core_routes(app)
    _register_shared_routes(app)
    _register_platform_routes(app, platform_adapter)

    return app


def _register_core_routes(app: FastAPI) -> None:
    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "PyAgent API", "version": "0.1.0"}

    @app.get("/api/status")
    async def get_status() -> dict[str, Any]:
        platform_adapter = get_platform_adapter()
        return {
            "status": "running",
            "platform": platform_adapter.platform_type.value,
            "capabilities": platform_adapter.capabilities.to_dict(),
        }

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        if not _chat_agent:
            raise HTTPException(status_code=503, detail="Chat agent not initialized")

        try:
            from src.interaction.heart_flow.heartf_chatting import MessageInfo

            message = MessageInfo(
                message_id=f"msg_{asyncio.get_event_loop().time()}",
                chat_id=request.chat_id,
                user_id="user",
                platform=request.platform,
                content=request.message,
                is_mentioned=True,
            )

            await _chat_agent.push_message(message)

            return ChatResponse(
                success=True, response="Message received, processing...", chat_id=request.chat_id
            )

        except Exception as e:
            logger.exception("Chat error: %s", e)
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/api/config")
    async def get_config() -> dict[str, Any]:
        loader = get_model_config_loader()

        return {
            "models": {
                tier: loader.get_model(tier).__dict__
                for tier in ["strong", "balanced", "fast", "tiny"]
            }
        }

    @app.get("/api/mcp/servers")
    async def list_mcp_servers() -> dict[str, Any]:
        return mcp_manager.get_summary()

    @app.post("/api/mcp/servers/{server_name}/connect")
    async def connect_mcp_server(server_name: str) -> dict[str, Any]:
        result = await mcp_manager.connect_server(server_name)
        return {"success": result.success, "error": result.error, "tool_count": result.tool_count}

    @app.get("/api/skills")
    async def list_skills() -> dict[str, Any]:
        return {
            "loaded": skill_loader.loaded_count,
            "skills": [
                {
                    "id": sid,
                    "name": skill.metadata.name,
                    "description": skill.metadata.description,
                    "enabled": skill_registry.is_enabled(sid),
                }
                for sid, skill in skill_loader.loaded_skills.items()
            ],
        }

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await manager.connect(websocket)

        try:
            while True:
                data = await websocket.receive_json()

                message_type = data.get("type", "chat")

                if message_type == "chat":
                    response = await handle_chat_message(data)
                    await websocket.send_json(response)
                elif message_type == "ping":
                    await websocket.send_json({"type": "pong"})

        except WebSocketDisconnect:
            manager.disconnect(websocket)


async def handle_chat_message(data: dict[str, Any]) -> dict[str, Any]:
    if not _chat_agent:
        return {"type": "error", "message": "Chat agent not initialized"}

    message = data.get("message", "")
    chat_id = data.get("chat_id", "default")

    return {"type": "response", "message": f"Received: {message}", "chat_id": chat_id}


def _register_shared_routes(app: FastAPI) -> None:
    app.include_router(todo_router)
    app.include_router(task_router)
    app.include_router(execution_router)
    app.include_router(document_router)
    app.include_router(video_router)
    app.include_router(domain_router)
    app.include_router(storage_router)
    app.include_router(human_tasks_router)
    app.include_router(calendar_router)
    app.include_router(settings_router)


def _register_platform_routes(app: FastAPI, platform_adapter: PlatformAdapter) -> None:
    platform_routes = platform_adapter.get_platform_specific_routes()

    for route_path, method, handler in platform_routes:
        if method == "GET":

            @app.get(route_path)
            async def route_handler(handler=handler):
                return await handler()
        elif method == "POST":

            @app.post(route_path)
            async def route_handler(data: dict[str, Any], handler=handler):
                return await handler(data)

    if platform_adapter.config.enable_hot_reload:
        from src.web.routes.hot_reload import init_hot_reload
        from src.web.routes.hot_reload import router as hot_reload_router

        app.include_router(hot_reload_router)
        init_hot_reload(Path(__file__).parent.parent.parent.parent)
