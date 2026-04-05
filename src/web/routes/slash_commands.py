"""
PyAgent Web服务 - 斜杠命令处理器

处理斜杠命令的解析和执行。
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class SlashCommandType(Enum):
    """斜杠命令类型"""
    OPEN_APP = "open_app"
    OPEN_FILE = "open_file"
    CREATE_EVENT = "create_event"
    CREATE_TODO = "create_todo"
    MODIFY_SETTINGS = "modify_settings"
    TOGGLE_MATE = "toggle_mate"
    NEW_TOPIC = "new_topic"
    UNKNOWN = "unknown"


@dataclass
class SlashCommand:
    """斜杠命令"""
    type: SlashCommandType
    raw_input: str
    command: str
    args: str
    params: dict[str, Any]


@dataclass
class CommandResult:
    """命令执行结果"""
    success: bool
    message: str
    action: str
    data: dict[str, Any]
    redirect_url: Optional[str] = None


class SlashCommandProcessor:
    """斜杠命令处理器"""
    
    COMMAND_PATTERNS = {
        SlashCommandType.OPEN_APP: [
            r"^/(calendar|日历)$",
            r"^/(tasks?|任务)$",
            r"^/(email|邮件)$",
            r"^/(notes?|笔记)$",
            r"^/(browser|浏览器)$",
            r"^/(files?|文件)$",
            r"^/(word)$",
            r"^/(ppt)$",
            r"^/(excel)$",
            r"^/(settings?|设置)$",
        ],
        SlashCommandType.OPEN_FILE: [
            r"^/open\s+(.+)$",
            r"^/打开\s+(.+)$",
        ],
        SlashCommandType.CREATE_EVENT: [
            r"^/event\s+(.+)$",
            r"^/日程\s+(.+)$",
        ],
        SlashCommandType.CREATE_TODO: [
            r"^/todo\s+(.+)$",
            r"^/待办\s+(.+)$",
        ],
        SlashCommandType.MODIFY_SETTINGS: [
            r"^/settings?\s+(.+)$",
            r"^/设置\s+(.+)$",
        ],
        SlashCommandType.TOGGLE_MATE: [
            r"^/mate$",
            r"^/Mate模式$",
        ],
        SlashCommandType.NEW_TOPIC: [
            r"^/new-topic$",
            r"^/新话题$",
        ],
    }
    
    APP_ROUTES = {
        "calendar": "/calendar",
        "日历": "/calendar",
        "tasks": "/tasks",
        "task": "/tasks",
        "任务": "/tasks",
        "email": "/email",
        "邮件": "/email",
        "notes": "/notes",
        "note": "/notes",
        "笔记": "/notes",
        "browser": "/browser",
        "浏览器": "/browser",
        "files": "/files",
        "file": "/files",
        "文件": "/files",
        "word": "/documents?type=word",
        "ppt": "/documents?type=ppt",
        "excel": "/documents?type=excel",
        "settings": "/settings",
        "setting": "/settings",
        "设置": "/settings",
    }
    
    def __init__(self):
        self._handlers: dict[SlashCommandType, Callable[[SlashCommand], CommandResult]] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """注册默认处理器"""
        self._handlers[SlashCommandType.OPEN_APP] = self._handle_open_app
        self._handlers[SlashCommandType.OPEN_FILE] = self._handle_open_file
        self._handlers[SlashCommandType.CREATE_EVENT] = self._handle_create_event
        self._handlers[SlashCommandType.CREATE_TODO] = self._handle_create_todo
        self._handlers[SlashCommandType.MODIFY_SETTINGS] = self._handle_modify_settings
        self._handlers[SlashCommandType.TOGGLE_MATE] = self._handle_toggle_mate
        self._handlers[SlashCommandType.NEW_TOPIC] = self._handle_new_topic
    
    def parse(self, user_input: str) -> SlashCommand:
        """
        解析用户输入
        
        Args:
            user_input: 用户输入
            
        Returns:
            SlashCommand: 解析后的命令
        """
        user_input = user_input.strip()
        
        if not user_input.startswith('/'):
            return SlashCommand(
                type=SlashCommandType.UNKNOWN,
                raw_input=user_input,
                command="",
                args="",
                params={}
            )
        
        for command_type, patterns in self.COMMAND_PATTERNS.items():
            for pattern in patterns:
                match = re.match(pattern, user_input, re.IGNORECASE)
                if match:
                    args = match.group(1) if match.groups() else ""
                    return SlashCommand(
                        type=command_type,
                        raw_input=user_input,
                        command=user_input.split()[0] if user_input else "",
                        args=args,
                        params={"target": args} if args else {}
                    )
        
        return SlashCommand(
            type=SlashCommandType.UNKNOWN,
            raw_input=user_input,
            command=user_input.split()[0] if user_input else "",
            args="",
            params={}
        )
    
    def execute(self, command: SlashCommand) -> CommandResult:
        """
        执行命令
        
        Args:
            command: 斜杠命令
            
        Returns:
            CommandResult: 执行结果
        """
        handler = self._handlers.get(command.type)
        if handler:
            try:
                return handler(command)
            except Exception as e:
                logger.error(f"Command execution failed: {e}")
                return CommandResult(
                    success=False,
                    message=f"命令执行失败: {str(e)}",
                    action="error",
                    data={}
                )
        
        return CommandResult(
            success=False,
            message=f"未知命令: {command.raw_input}",
            action="unknown",
            data={}
        )
    
    def _handle_open_app(self, command: SlashCommand) -> CommandResult:
        """处理打开应用命令"""
        app_name = command.args.lower() if command.args else ""
        redirect_url = self.APP_ROUTES.get(app_name)
        
        if redirect_url:
            return CommandResult(
                success=True,
                message=f"正在打开应用: {app_name}",
                action="open_app",
                data={"app_name": app_name},
                redirect_url=redirect_url
            )
        
        return CommandResult(
            success=False,
            message=f"未知应用: {app_name}",
            action="open_app",
            data={}
        )
    
    def _handle_open_file(self, command: SlashCommand) -> CommandResult:
        """处理打开文件命令"""
        file_name = command.args
        if file_name:
            return CommandResult(
                success=True,
                message=f"正在搜索文件: {file_name}",
                action="open_file",
                data={"file_name": file_name},
                redirect_url=f"/files?search={file_name}"
            )
        
        return CommandResult(
            success=True,
            message="正在打开文件管理器",
            action="open_file",
            data={},
            redirect_url="/files"
        )
    
    def _handle_create_event(self, command: SlashCommand) -> CommandResult:
        """处理创建日程命令"""
        event_content = command.args
        if event_content:
            return CommandResult(
                success=True,
                message=f"正在创建日程: {event_content}",
                action="create_event",
                data={"event_content": event_content},
                redirect_url=f"/calendar/create?content={event_content}"
            )
        
        return CommandResult(
            success=True,
            message="正在打开日程创建页面",
            action="create_event",
            data={},
            redirect_url="/calendar/create"
        )
    
    def _handle_create_todo(self, command: SlashCommand) -> CommandResult:
        """处理创建待办命令"""
        todo_content = command.args
        if todo_content:
            return CommandResult(
                success=True,
                message=f"正在创建待办: {todo_content}",
                action="create_todo",
                data={"todo_content": todo_content},
                redirect_url=f"/tasks/create?content={todo_content}"
            )
        
        return CommandResult(
            success=True,
            message="正在打开待办创建页面",
            action="create_todo",
            data={},
            redirect_url="/tasks/create"
        )
    
    def _handle_modify_settings(self, command: SlashCommand) -> CommandResult:
        """处理修改设置命令"""
        settings_input = command.args
        return CommandResult(
            success=True,
            message=f"正在修改设置: {settings_input}",
            action="modify_settings",
            data={"settings_input": settings_input},
            redirect_url="/settings"
        )
    
    def _handle_toggle_mate(self, command: SlashCommand) -> CommandResult:
        """处理切换Mate模式命令"""
        return CommandResult(
            success=True,
            message="切换Mate模式",
            action="toggle_mate",
            data={},
            redirect_url=None
        )
    
    def _handle_new_topic(self, command: SlashCommand) -> CommandResult:
        """处理新话题命令"""
        return CommandResult(
            success=True,
            message="开始新话题",
            action="new_topic",
            data={},
            redirect_url=None
        )
    
    def register_handler(
        self,
        command_type: SlashCommandType,
        handler: Callable[[SlashCommand], CommandResult]
    ) -> None:
        """
        注册命令处理器
        
        Args:
            command_type: 命令类型
            handler: 处理函数
        """
        self._handlers[command_type] = handler
    
    def get_supported_commands(self) -> list[dict[str, str]]:
        """
        获取支持的命令列表
        
        Returns:
            list: 命令列表
        """
        return [
            {"command": "/calendar", "description": "打开日历"},
            {"command": "/tasks", "description": "打开任务"},
            {"command": "/email", "description": "打开邮件"},
            {"command": "/notes", "description": "打开笔记"},
            {"command": "/browser", "description": "打开浏览器"},
            {"command": "/files", "description": "打开文件"},
            {"command": "/word", "description": "打开Word"},
            {"command": "/ppt", "description": "打开PPT"},
            {"command": "/excel", "description": "打开Excel"},
            {"command": "/settings", "description": "打开设置"},
            {"command": "/event <内容>", "description": "创建日程"},
            {"command": "/todo <内容>", "description": "创建待办"},
            {"command": "/open <文件名>", "description": "打开文件"},
            {"command": "/mate", "description": "切换Mate模式"},
            {"command": "/new-topic", "description": "新话题"},
        ]


slash_command_processor = SlashCommandProcessor()
