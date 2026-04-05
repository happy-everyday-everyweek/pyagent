"""
PyAgent 聊天Agent工具集 - 记忆工具

通过模块间通信调用记忆模块。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MemoryOperation(Enum):
    """记忆操作类型"""
    STORE = "store"
    RETRIEVE = "retrieve"
    FORGET = "forget"
    LIST = "list"


@dataclass
class MemoryEntry:
    """记忆条目"""
    key: str
    value: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryToolResult:
    """记忆工具结果"""
    success: bool
    operation: MemoryOperation = MemoryOperation.STORE
    entries: list[MemoryEntry] = field(default_factory=list)
    error: str = ""
    message: str = ""


class MemoryTool:
    """记忆工具"""

    def __init__(self, memory_module: Any | None = None):
        self.memory_module = memory_module
        self.name = "memory"
        self.description = "操作记忆系统"

    async def execute(
        self,
        operation: str,
        content: str = "",
        key: str = "",
        **kwargs
    ) -> MemoryToolResult:
        """执行记忆操作"""
        try:
            op = MemoryOperation(operation.lower())
        except ValueError:
            return MemoryToolResult(
                success=False,
                error=f"未知的操作类型: {operation}"
            )

        if self.memory_module:
            try:
                if op == MemoryOperation.STORE:
                    await self.memory_module.store(key, content)
                    return MemoryToolResult(
                        success=True,
                        operation=op,
                        message=f"已存储记忆: {key}"
                    )

                elif op == MemoryOperation.RETRIEVE:
                    value = await self.memory_module.retrieve(key)
                    return MemoryToolResult(
                        success=True,
                        operation=op,
                        entries=[MemoryEntry(key=key, value=value)]
                    )

                elif op == MemoryOperation.FORGET:
                    await self.memory_module.forget(key)
                    return MemoryToolResult(
                        success=True,
                        operation=op,
                        message=f"已遗忘记忆: {key}"
                    )

                elif op == MemoryOperation.LIST:
                    entries = await self.memory_module.list_all()
                    return MemoryToolResult(
                        success=True,
                        operation=op,
                        entries=entries
                    )

            except Exception as e:
                return MemoryToolResult(
                    success=False,
                    operation=op,
                    error=str(e)
                )

        return MemoryToolResult(
            success=True,
            operation=op,
            message=f"模拟{operation}操作"
        )

    async def store(self, key: str, content: str) -> MemoryToolResult:
        """存储记忆"""
        return await self.execute("store", content=content, key=key)

    async def retrieve(self, key: str) -> MemoryToolResult:
        """检索记忆"""
        return await self.execute("retrieve", key=key)

    async def forget(self, key: str) -> MemoryToolResult:
        """遗忘记忆"""
        return await self.execute("forget", key=key)

    async def list_all(self) -> MemoryToolResult:
        """列出所有记忆"""
        return await self.execute("list")

    def get_description(self) -> str:
        """获取工具描述"""
        return self.description

    def get_parameters(self) -> dict[str, Any]:
        """获取参数定义"""
        return {
            "operation": {
                "type": "string",
                "description": "操作类型：store/retrieve/forget/list",
                "enum": ["store", "retrieve", "forget", "list"]
            },
            "key": {
                "type": "string",
                "description": "记忆键名"
            },
            "content": {
                "type": "string",
                "description": "记忆内容（仅store操作需要）"
            }
        }
