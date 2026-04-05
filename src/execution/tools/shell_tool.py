"""
PyAgent 执行模块工具系统 - Shell命令工具
"""

import asyncio
from typing import Any

from .base import BaseTool, RiskLevel, ToolCategory, ToolParameter, ToolResult


class ShellTool(BaseTool):
    """Shell命令执行工具"""

    name = "shell"
    description = "执行Shell命令"
    category = ToolCategory.SHELL
    risk_level = RiskLevel.HIGH

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="command",
                type="string",
                description="要执行的Shell命令",
                required=True
            ),
            ToolParameter(
                name="timeout",
                type="integer",
                description="超时时间（秒）",
                required=False,
                default=30
            ),
            ToolParameter(
                name="cwd",
                type="string",
                description="工作目录",
                required=False
            )
        ]

        self.blocked_commands = self.config.get("blocked_commands", [
            "rm -rf /",
            "mkfs",
            "dd if=",
            ":(){ :|:& };:",
            "chmod -R 777 /"
        ])

    async def execute(self, **kwargs) -> ToolResult:
        """执行Shell命令"""
        valid, errors = self.validate_parameters(**kwargs)
        if not valid:
            return ToolResult(success=False, error="; ".join(errors))

        command = kwargs.get("command", "")
        timeout = kwargs.get("timeout", 30)
        cwd = kwargs.get("cwd")

        for blocked in self.blocked_commands:
            if blocked in command:
                return ToolResult(
                    success=False,
                    error=f"命令被阻止: 包含危险操作 '{blocked}'"
                )

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    success=False,
                    error=f"命令执行超时（{timeout}秒）"
                )

            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace")

            if process.returncode == 0:
                return ToolResult(
                    success=True,
                    output=output,
                    metadata={"return_code": process.returncode}
                )
            else:
                return ToolResult(
                    success=False,
                    output=output,
                    error=error_output or f"命令返回非零退出码: {process.returncode}",
                    metadata={"return_code": process.returncode}
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"执行命令时出错: {str(e)}"
            )
