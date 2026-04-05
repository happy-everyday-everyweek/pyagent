"""
PyAgent 执行模块工具系统 - 文件操作工具
"""

from pathlib import Path
from typing import Any

from .base import BaseTool, RiskLevel, ToolCategory, ToolParameter, ToolResult


class FileReadTool(BaseTool):
    """文件读取工具"""

    name = "file_read"
    description = "读取文件内容"
    category = ToolCategory.FILE
    risk_level = RiskLevel.LOW

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="path",
                type="string",
                description="文件路径",
                required=True
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="文件编码",
                required=False,
                default="utf-8"
            ),
            ToolParameter(
                name="max_size",
                type="integer",
                description="最大读取大小（字节）",
                required=False,
                default=1000000
            )
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """读取文件"""
        valid, errors = self.validate_parameters(**kwargs)
        if not valid:
            return ToolResult(success=False, error="; ".join(errors))

        path = kwargs.get("path", "")
        encoding = kwargs.get("encoding", "utf-8")
        max_size = kwargs.get("max_size", 1000000)

        try:
            file_path = Path(path)

            if not file_path.exists():
                return ToolResult(success=False, error=f"文件不存在: {path}")

            if not file_path.is_file():
                return ToolResult(success=False, error=f"路径不是文件: {path}")

            file_size = file_path.stat().st_size
            if file_size > max_size:
                return ToolResult(
                    success=False,
                    error=f"文件过大: {file_size} 字节 (最大: {max_size})"
                )

            with open(file_path, encoding=encoding) as f:
                content = f.read()

            return ToolResult(
                success=True,
                output=content,
                metadata={
                    "path": str(file_path),
                    "size": file_size,
                    "encoding": encoding
                }
            )

        except Exception as e:
            return ToolResult(success=False, error=f"读取文件时出错: {str(e)}")


class FileWriteTool(BaseTool):
    """文件写入工具"""

    name = "file_write"
    description = "写入文件内容"
    category = ToolCategory.FILE
    risk_level = RiskLevel.MEDIUM

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="path",
                type="string",
                description="文件路径",
                required=True
            ),
            ToolParameter(
                name="content",
                type="string",
                description="文件内容",
                required=True
            ),
            ToolParameter(
                name="mode",
                type="string",
                description="写入模式: write 或 append",
                required=False,
                default="write",
                enum=["write", "append"]
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="文件编码",
                required=False,
                default="utf-8"
            )
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """写入文件"""
        valid, errors = self.validate_parameters(**kwargs)
        if not valid:
            return ToolResult(success=False, error="; ".join(errors))

        path = kwargs.get("path", "")
        content = kwargs.get("content", "")
        mode = kwargs.get("mode", "write")
        encoding = kwargs.get("encoding", "utf-8")

        try:
            file_path = Path(path)

            file_path.parent.mkdir(parents=True, exist_ok=True)

            write_mode = "w" if mode == "write" else "a"
            with open(file_path, write_mode, encoding=encoding) as f:
                f.write(content)

            return ToolResult(
                success=True,
                output=f"成功写入文件: {path}",
                metadata={
                    "path": str(file_path),
                    "size": len(content),
                    "mode": mode
                }
            )

        except Exception as e:
            return ToolResult(success=False, error=f"写入文件时出错: {str(e)}")


class FileListTool(BaseTool):
    """文件列表工具"""

    name = "file_list"
    description = "列出目录内容"
    category = ToolCategory.FILE
    risk_level = RiskLevel.SAFE

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="path",
                type="string",
                description="目录路径",
                required=True
            ),
            ToolParameter(
                name="pattern",
                type="string",
                description="文件匹配模式（glob）",
                required=False,
                default="*"
            )
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """列出目录内容"""
        valid, errors = self.validate_parameters(**kwargs)
        if not valid:
            return ToolResult(success=False, error="; ".join(errors))

        path = kwargs.get("path", "")
        pattern = kwargs.get("pattern", "*")

        try:
            dir_path = Path(path)

            if not dir_path.exists():
                return ToolResult(success=False, error=f"目录不存在: {path}")

            if not dir_path.is_dir():
                return ToolResult(success=False, error=f"路径不是目录: {path}")

            items = list(dir_path.glob(pattern))

            result_lines = []
            for item in sorted(items):
                item_type = "DIR" if item.is_dir() else "FILE"
                size = item.stat().st_size if item.is_file() else "-"
                result_lines.append(f"{item_type:6} {size:>10} {item.name}")

            return ToolResult(
                success=True,
                output="\n".join(result_lines),
                metadata={
                    "path": str(dir_path),
                    "count": len(items)
                }
            )

        except Exception as e:
            return ToolResult(success=False, error=f"列出目录时出错: {str(e)}")
