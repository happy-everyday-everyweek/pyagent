"""
PyAgent - Python Agent智能体系统

一个功能强大的Python智能体框架，支持多平台IM集成、多智能体协作、
ReAct推理引擎、MCP协议支持、AI原生Todo管理、四级记忆系统等高级特性。
"""

__version__ = "0.8.1"
__author__ = "PyAgent Team"
__license__ = "GPL-3.0"

from src.llm import LLMClient, get_default_client, create_client_from_env
from src.memory import (
    ChatMemoryStorage,
    chat_memory_storage,
    WorkMemoryStorage,
    work_memory_storage,
)
from src.execution import ExecutorAgent, Task, TaskResult, TaskStatus
from src.interaction import IntentRecognizer, IntentType

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "LLMClient",
    "get_default_client",
    "create_client_from_env",
    "ChatMemoryStorage",
    "chat_memory_storage",
    "WorkMemoryStorage",
    "work_memory_storage",
    "ExecutorAgent",
    "Task",
    "TaskResult",
    "TaskStatus",
    "IntentRecognizer",
    "IntentType",
]
