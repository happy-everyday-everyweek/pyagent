"""
PyAgent Web服务 - FastAPI应用

提供REST API和WebSocket接口。
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.web.routes.calendar_routes import router as calendar_router
from src.web.routes.document_routes import router as document_router
from src.web.routes.domain_routes import router as domain_router
from src.web.routes.execution_routes import router as execution_router
from src.web.routes.execution_routes import (
    set_collaboration_manager,
)
from src.web.routes.hot_reload import init_hot_reload
from src.web.routes.hot_reload import router as hot_reload_router
from src.web.routes.human_tasks_routes import router as human_tasks_router
from src.web.routes.storage_routes import router as storage_router
from src.web.routes.task_routes import router as task_router
from src.web.routes.task_routes import set_executor_agent
from src.web.routes.todo_routes import router as todo_router
from src.web.routes.video_routes import router as video_router

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    chat_id: str | None = "default"
    platform: str | None = "web"


class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool
    response: str
    chat_id: str
    actions: list[dict[str, Any]] = []


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    result: str | None = None
    error: str | None = None


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    key: str
    value: Any


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """接受连接"""
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """断开连接"""
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """广播消息"""
        for connection in self._connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()

_chat_agent = None
_executor_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    global _chat_agent, _executor_agent

    logger.info("Starting PyAgent...")

    from src.execution.executor_agent import ExecutorAgent
    from src.execution.tools.file_tools import FileListTool, FileReadTool, FileWriteTool
    from src.execution.tools.registry import ToolRegistry
    from src.execution.tools.shell_tool import ShellTool
    from src.execution.tools.web_tools import WebFetchTool, WebRequestTool
    from src.interaction.heart_flow.heartf_chatting import HeartFChatting
    from src.llm import create_client_from_env

    try:
        llm_client = create_client_from_env()
    except Exception:
        llm_client = None
        logger.warning("LLM client not configured")

    tool_registry = ToolRegistry()
    tool_registry.register(ShellTool())
    tool_registry.register(FileReadTool())
    tool_registry.register(FileWriteTool())
    tool_registry.register(FileListTool())
    tool_registry.register(WebRequestTool())
    tool_registry.register(WebFetchTool())

    _executor_agent = ExecutorAgent(
        llm_client=llm_client,
        tool_registry=tool_registry
    )

    set_executor_agent(_executor_agent)

    from src.execution.collaboration import CollaborationManager
    _collaboration_manager = CollaborationManager(
        llm_client=llm_client,
        tool_registry=tool_registry
    )
    set_collaboration_manager(_collaboration_manager)

    _chat_agent = HeartFChatting(chat_id="web", config={"llm_client": llm_client})

    logger.info("PyAgent started successfully")

    yield

    logger.info("Shutting down PyAgent...")

    if _chat_agent:
        await _chat_agent.stop()

    logger.info("PyAgent shutdown complete")


app = FastAPI(
    title="PyAgent API",
    description="Python Agent智能体系统API",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """根路径"""
    return {"message": "PyAgent API", "version": "0.1.0"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """聊天接口"""
    global _chat_agent

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
            is_mentioned=True
        )

        await _chat_agent.push_message(message)

        return ChatResponse(
            success=True,
            response="消息已接收，正在处理...",
            chat_id=request.chat_id
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/config")
async def get_config() -> dict[str, Any]:
    """获取配置"""
    from src.llm import get_model_config_loader

    loader = get_model_config_loader()

    return {
        "models": {
            tier: loader.get_model(tier).__dict__
            for tier in ["strong", "balanced", "fast", "tiny"]
        }
    }


@app.put("/api/config")
async def update_config(request: ConfigUpdateRequest) -> dict[str, bool]:
    """更新配置"""
    return {"success": True}


@app.get("/api/mcp/servers")
async def list_mcp_servers() -> dict[str, Any]:
    """列出MCP服务器"""
    from src.mcp import mcp_manager

    return mcp_manager.get_summary()


@app.post("/api/mcp/servers/{server_name}/connect")
async def connect_mcp_server(server_name: str) -> dict[str, Any]:
    """连接MCP服务器"""
    from src.mcp import mcp_manager

    result = await mcp_manager.connect_server(server_name)
    return {
        "success": result.success,
        "error": result.error,
        "tool_count": result.tool_count
    }


@app.get("/api/skills")
async def list_skills() -> dict[str, Any]:
    """列出技能"""
    from src.skills import skill_loader, skill_registry

    return {
        "loaded": skill_loader.loaded_count,
        "skills": [
            {
                "id": sid,
                "name": skill.metadata.name,
                "description": skill.metadata.description,
                "enabled": skill_registry.is_enabled(sid)
            }
            for sid, skill in skill_loader._loaded_skills.items()
        ]
    }


app.include_router(todo_router)
app.include_router(task_router)
app.include_router(execution_router)
app.include_router(hot_reload_router)
app.include_router(document_router)
app.include_router(video_router)
app.include_router(domain_router)
app.include_router(storage_router)
app.include_router(human_tasks_router)
app.include_router(calendar_router)

from pathlib import Path

init_hot_reload(Path(__file__).parent.parent.parent.parent)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket接口"""
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
    """处理聊天消息"""
    global _chat_agent

    if not _chat_agent:
        return {"type": "error", "message": "Chat agent not initialized"}

    message = data.get("message", "")
    chat_id = data.get("chat_id", "default")

    return {
        "type": "response",
        "message": f"收到消息: {message}",
        "chat_id": chat_id
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
