"""
PyAgent - Python Agent智能体系统

一个功能强大的Python智能体框架，支持多平台IM集成、多智能体协作、
ReAct推理引擎、MCP协议支持、AI原生Todo管理、四级记忆系统等高级特性。
"""

__version__ = "0.9.11"
__author__ = "PyAgent Team"
__license__ = "GPL-3.0"

from src.execution import ExecutorAgent, Task, TaskResult, TaskStatus
from src.interaction import IntentRecognizer, IntentType
from src.llm import LLMClient, create_client_from_env, get_default_client
from src.memory import (
    ChatMemoryStorage,
    WorkMemoryStorage,
    chat_memory_storage,
    work_memory_storage,
)

__all__ = [
    "ChatMemoryStorage",
    "ExecutorAgent",
    "IntentRecognizer",
    "IntentType",
    "LLMClient",
    "Task",
    "TaskResult",
    "TaskStatus",
    "WorkMemoryStorage",
    "__author__",
    "__license__",
    "__version__",
    "chat_memory_storage",
    "create_client_from_env",
    "get_default_client",
    "work_memory_storage",
]
