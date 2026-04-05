"""
PyAgent 交互模块 - 意图路由器

将识别出的意图路由到对应的处理模块。
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional

from .intent_types import Intent, IntentType


@dataclass
class RouteResult:
    """
    路由结果
    
    表示意图路由的结果。
    """
    success: bool
    handler_name: str
    action: str
    data: dict[str, Any]
    message: str = ""
    redirect_url: Optional[str] = None


class IntentRouter:
    """意图路由器"""
    
    def __init__(self):
        self._handlers: dict[IntentType, Callable[[Intent], RouteResult]] = {}
        self._default_handler: Optional[Callable[[Intent], RouteResult]] = None
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """注册默认处理器"""
        self._handlers[IntentType.OPEN_FILE] = self._handle_open_file
        self._handlers[IntentType.OPEN_APP] = self._handle_open_app
        self._handlers[IntentType.CREATE_EVENT] = self._handle_create_event
        self._handlers[IntentType.CREATE_TODO] = self._handle_create_todo
        self._handlers[IntentType.MODIFY_SETTINGS] = self._handle_modify_settings
        self._handlers[IntentType.COMMAND] = self._handle_command
        self._handlers[IntentType.CHAT] = self._handle_chat
        self._handlers[IntentType.TASK] = self._handle_task
        self._handlers[IntentType.QUERY] = self._handle_query
    
    def register_handler(
        self,
        intent_type: IntentType,
        handler: Callable[[Intent], RouteResult]
    ) -> None:
        """
        注册意图处理器
        
        Args:
            intent_type: 意图类型
            handler: 处理函数
        """
        self._handlers[intent_type] = handler
    
    def set_default_handler(self, handler: Callable[[Intent], RouteResult]) -> None:
        """
        设置默认处理器
        
        Args:
            handler: 默认处理函数
        """
        self._default_handler = handler
    
    def route(self, intent: Intent) -> RouteResult:
        """
        路由意图到对应的处理器
        
        Args:
            intent: 识别出的意图
            
        Returns:
            RouteResult: 路由结果
        """
        handler = self._handlers.get(intent.type)
        if handler:
            return handler(intent)
        
        if self._default_handler:
            return self._default_handler(intent)
        
        return RouteResult(
            success=False,
            handler_name="default",
            action="unknown",
            data={},
            message=f"未找到意图类型 {intent.type.name} 的处理器"
        )
    
    def _handle_open_file(self, intent: Intent) -> RouteResult:
        """处理打开文件意图"""
        file_name = intent.entities.get("file_name", "")
        return RouteResult(
            success=True,
            handler_name="file_manager",
            action="open_file",
            data={"file_name": file_name},
            message=f"正在打开文件: {file_name}",
            redirect_url=f"/files?search={file_name}"
        )
    
    def _handle_open_app(self, intent: Intent) -> RouteResult:
        """处理打开应用意图"""
        app_id = intent.entities.get("app_id", "")
        app_name = intent.entities.get("app_name", "")
        
        app_routes = {
            "calendar": "/calendar",
            "tasks": "/tasks",
            "email": "/email",
            "notes": "/notes",
            "browser": "/browser",
            "files": "/files",
            "settings": "/settings",
            "word": "/documents?type=word",
            "ppt": "/documents?type=ppt",
            "excel": "/documents?type=excel",
        }
        
        redirect_url = app_routes.get(app_id, f"/apps/{app_id}")
        
        return RouteResult(
            success=True,
            handler_name="app_launcher",
            action="open_app",
            data={"app_id": app_id, "app_name": app_name},
            message=f"正在打开应用: {app_name}",
            redirect_url=redirect_url
        )
    
    def _handle_create_event(self, intent: Intent) -> RouteResult:
        """处理创建日程意图"""
        event_content = intent.entities.get("event_content", intent.content)
        return RouteResult(
            success=True,
            handler_name="calendar",
            action="create_event",
            data={"event_content": event_content},
            message=f"正在创建日程: {event_content}",
            redirect_url=f"/calendar/create?content={event_content}"
        )
    
    def _handle_create_todo(self, intent: Intent) -> RouteResult:
        """处理创建待办意图"""
        todo_content = intent.entities.get("todo_content", intent.content)
        return RouteResult(
            success=True,
            handler_name="todo",
            action="create_todo",
            data={"todo_content": todo_content},
            message=f"正在创建待办: {todo_content}",
            redirect_url=f"/tasks/create?content={todo_content}"
        )
    
    def _handle_modify_settings(self, intent: Intent) -> RouteResult:
        """处理修改设置意图"""
        settings_input = intent.entities.get("settings_input", intent.content)
        return RouteResult(
            success=True,
            handler_name="settings",
            action="modify_settings",
            data={"settings_input": settings_input},
            message=f"正在修改设置: {settings_input}",
            redirect_url="/settings"
        )
    
    def _handle_command(self, intent: Intent) -> RouteResult:
        """处理命令意图"""
        command = intent.entities.get("command", "")
        return RouteResult(
            success=True,
            handler_name="command_processor",
            action="execute_command",
            data={"command": command},
            message=f"执行命令: {command}"
        )
    
    def _handle_chat(self, intent: Intent) -> RouteResult:
        """处理聊天意图"""
        return RouteResult(
            success=True,
            handler_name="chat_module",
            action="chat",
            data={"content": intent.content},
            message="发送到聊天模块"
        )
    
    def _handle_task(self, intent: Intent) -> RouteResult:
        """处理任务意图"""
        return RouteResult(
            success=True,
            handler_name="task_executor",
            action="execute_task",
            data={"content": intent.content, "entities": intent.entities},
            message="创建执行任务"
        )
    
    def _handle_query(self, intent: Intent) -> RouteResult:
        """处理查询意图"""
        return RouteResult(
            success=True,
            handler_name="search_engine",
            action="search",
            data={"query": intent.content},
            message="执行查询"
        )
    
    def get_supported_intents(self) -> list[str]:
        """
        获取支持的意图类型列表
        
        Returns:
            list: 意图类型名称列表
        """
        return [intent_type.name for intent_type in self._handlers.keys()]
    
    def needs_redirect(self, intent: Intent) -> bool:
        """
        检查意图是否需要重定向
        
        Args:
            intent: 意图对象
            
        Returns:
            bool: 是否需要重定向
        """
        return intent.needs_redirect()


router = IntentRouter()
