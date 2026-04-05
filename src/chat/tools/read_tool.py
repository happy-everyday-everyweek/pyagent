"""
PyAgent 聊天Agent工具集 - 阅读工具

通过模块间通信调用阅读模块。
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ReadToolResult:
    """阅读工具结果"""
    success: bool
    content: str = ""
    error: str = ""
    path: str = ""
    size: int = 0


class ReadTool:
    """阅读工具"""

    def __init__(self, file_module: Any | None = None):
        self.file_module = file_module
        self.name = "read"
        self.description = "阅读文件或网页内容"

    async def execute(
        self,
        path: str,
        max_length: int = 10000,
        **kwargs
    ) -> ReadToolResult:
        """执行阅读"""
        if not path:
            return ReadToolResult(
                success=False,
                error="路径不能为空"
            )

        if self.file_module:
            try:
                content = await self.file_module.read(path, max_length)
                return ReadToolResult(
                    success=True,
                    content=content,
                    path=path,
                    size=len(content)
                )
            except Exception as e:
                return ReadToolResult(
                    success=False,
                    error=str(e),
                    path=path
                )

        return ReadToolResult(
            success=True,
            content=f"模拟读取 '{path}' 的内容",
            path=path,
            size=100
        )

    def get_description(self) -> str:
        """获取工具描述"""
        return self.description

    def get_parameters(self) -> dict[str, Any]:
        """获取参数定义"""
        return {
            "path": {
                "type": "string",
                "description": "文件路径或URL"
            },
            "max_length": {
                "type": "integer",
                "description": "最大读取长度",
                "default": 10000
            }
        }
