"""
PyAgent 移动端模块 - 代码执行沙箱
移植自 OpenKiwi CodeSandbox
"""

import asyncio
import logging
import re
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class SandboxStatus(Enum):
    """沙箱状态"""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    duration_ms: int = 0
    status: SandboxStatus = SandboxStatus.IDLE
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "error": self.error,
        }


@dataclass
class SandboxConfig:
    """沙箱配置"""
    timeout_seconds: int = 30
    max_output_bytes: int = 1024 * 100
    max_file_size_bytes: int = 1024 * 1024
    allowed_commands: list[str] = field(default_factory=lambda: [
        "ls", "cat", "echo", "grep", "find", "head", "tail",
        "wc", "sort", "uniq", "cut", "awk", "sed",
        "python", "python3", "node", "npm",
    ])
    sandbox_dir: str = ""


class DangerCommandDetector:
    """危险命令检测器

    检测可能造成危险的命令。
    """

    DANGEROUS_PATTERNS = [
        re.compile(r"rm\s+-rf\s+/", re.IGNORECASE),
        re.compile(r"rm\s+-rf\s+~", re.IGNORECASE),
        re.compile(r"rm\s+-rf\s+\*", re.IGNORECASE),
        re.compile(r"mkfs", re.IGNORECASE),
        re.compile(r"dd\s+if=", re.IGNORECASE),
        re.compile(r">\s*/dev/sd", re.IGNORECASE),
        re.compile(r"chmod\s+777", re.IGNORECASE),
        re.compile(r"chown\s+root", re.IGNORECASE),
        re.compile(r"wget\s+.*\s*\|\s*bash", re.IGNORECASE),
        re.compile(r"curl\s+.*\s*\|\s*bash", re.IGNORECASE),
        re.compile(r"eval\s+\$\(curl", re.IGNORECASE),
        re.compile(r"eval\s+\$\(wget", re.IGNORECASE),
        re.compile(r":(){ :|:& };:", re.IGNORECASE),
        re.compile(r"fork\s+bomb", re.IGNORECASE),
        re.compile(r"shutdown", re.IGNORECASE),
        re.compile(r"reboot", re.IGNORECASE),
        re.compile(r"halt", re.IGNORECASE),
        re.compile(r"init\s+0", re.IGNORECASE),
        re.compile(r"init\s+6", re.IGNORECASE),
    ]

    SENSITIVE_PATHS = [
        "/etc/passwd",
        "/etc/shadow",
        "/etc/sudoers",
        "/root",
        "/home",
        "~/.ssh",
        "~/.gnupg",
    ]

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def detect(self, command: str) -> tuple[bool, str]:
        """检测命令是否危险

        Returns:
            (is_dangerous, reason)
        """
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(command):
                return True, f"Matches dangerous pattern: {pattern.pattern}"

        for path in self.SENSITIVE_PATHS:
            if path in command:
                return True, f"Accesses sensitive path: {path}"

        if "sudo" in command.lower():
            return True, "Requires sudo privileges"

        return False, ""

    def sanitize(self, command: str) -> str:
        """清理命令（移除危险部分）"""
        sanitized = command

        for path in self.SENSITIVE_PATHS:
            sanitized = sanitized.replace(path, "")

        return sanitized.strip()


class CodeSandbox:
    """代码执行沙箱

    提供安全的代码执行环境。
    移植自 OpenKiwi 的 CodeSandbox。
    """

    def __init__(self, config: SandboxConfig | None = None):
        self._config = config or SandboxConfig()
        self._detector = DangerCommandDetector()
        self._status = SandboxStatus.IDLE
        self._logger = logging.getLogger(__name__)

        if not self._config.sandbox_dir:
            self._config.sandbox_dir = tempfile.mkdtemp(prefix="pyagent_sandbox_")

        self._sandbox_path = Path(self._config.sandbox_dir)
        self._sandbox_path.mkdir(parents=True, exist_ok=True)

    @property
    def status(self) -> SandboxStatus:
        """获取沙箱状态"""
        return self._status

    @property
    def sandbox_dir(self) -> Path:
        """获取沙箱目录"""
        return self._sandbox_path

    def check_command(self, command: str) -> tuple[bool, str]:
        """检查命令是否允许执行

        Returns:
            (allowed, reason)
        """
        is_dangerous, reason = self._detector.detect(command)
        if is_dangerous:
            return False, f"Dangerous command detected: {reason}"

        first_word = command.split(maxsplit=1)[0] if command.split() else ""
        if first_word and self._config.allowed_commands:
            if first_word not in self._config.allowed_commands:
                return False, f"Command not allowed: {first_word}"

        return True, "OK"

    async def execute_shell(
        self,
        command: str,
        timeout: int | None = None,
        check_danger: bool = True
    ) -> ExecutionResult:
        """执行 Shell 命令

        Args:
            command: Shell 命令
            timeout: 超时时间（秒）
            check_danger: 是否检查危险命令

        Returns:
            ExecutionResult: 执行结果
        """
        if check_danger:
            allowed, reason = self.check_command(command)
            if not allowed:
                return ExecutionResult(
                    success=False,
                    status=SandboxStatus.ERROR,
                    error=reason,
                )

        timeout = timeout or self._config.timeout_seconds
        self._status = SandboxStatus.RUNNING
        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self._sandbox_path,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                self._status = SandboxStatus.TIMEOUT
                return ExecutionResult(
                    success=False,
                    status=SandboxStatus.TIMEOUT,
                    error=f"Command timed out after {timeout} seconds",
                    duration_ms=int((time.time() - start_time) * 1000),
                )

            stdout_str = self._truncate_output(stdout.decode("utf-8", errors="replace"))
            stderr_str = self._truncate_output(stderr.decode("utf-8", errors="replace"))

            self._status = SandboxStatus.IDLE

            return ExecutionResult(
                success=process.returncode == 0,
                stdout=stdout_str,
                stderr=stderr_str,
                exit_code=process.returncode or 0,
                duration_ms=int((time.time() - start_time) * 1000),
                status=SandboxStatus.IDLE,
            )

        except Exception as e:
            self._status = SandboxStatus.ERROR
            self._logger.error(f"Failed to execute command: {e}")
            return ExecutionResult(
                success=False,
                status=SandboxStatus.ERROR,
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def execute_python(
        self,
        code: str,
        timeout: int | None = None
    ) -> ExecutionResult:
        """执行 Python 代码

        Args:
            code: Python 代码
            timeout: 超时时间（秒）

        Returns:
            ExecutionResult: 执行结果
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_file = self._sandbox_path / f"script_{timestamp}.py"

        try:
            script_file.write_text(code, encoding="utf-8")

            result = await self.execute_shell(
                f"python {script_file.name}",
                timeout=timeout,
                check_danger=False,
            )

            return result

        except Exception as e:
            self._logger.error(f"Failed to execute Python code: {e}")
            return ExecutionResult(
                success=False,
                status=SandboxStatus.ERROR,
                error=str(e),
            )

        finally:
            if script_file.exists():
                try:
                    script_file.unlink()
                except Exception:
                    pass

    async def execute_javascript(
        self,
        code: str,
        timeout: int | None = None
    ) -> ExecutionResult:
        """执行 JavaScript 代码

        Args:
            code: JavaScript 代码
            timeout: 超时时间（秒）

        Returns:
            ExecutionResult: 执行结果
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_file = self._sandbox_path / f"script_{timestamp}.js"

        try:
            script_file.write_text(code, encoding="utf-8")

            result = await self.execute_shell(
                f"node {script_file.name}",
                timeout=timeout,
                check_danger=False,
            )

            return result

        except Exception as e:
            self._logger.error(f"Failed to execute JavaScript code: {e}")
            return ExecutionResult(
                success=False,
                status=SandboxStatus.ERROR,
                error=str(e),
            )

        finally:
            if script_file.exists():
                try:
                    script_file.unlink()
                except Exception:
                    pass

    def _truncate_output(self, output: str) -> str:
        """截断输出"""
        if len(output.encode("utf-8")) > self._config.max_output_bytes:
            truncated = output[:self._config.max_output_bytes // 2]
            truncated += "\n... [output truncated] ..."
            return truncated
        return output

    def write_file(self, filename: str, content: str) -> bool:
        """写入文件到沙箱

        Args:
            filename: 文件名
            content: 文件内容

        Returns:
            是否成功
        """
        if len(content.encode("utf-8")) > self._config.max_file_size_bytes:
            self._logger.error("File size exceeds limit")
            return False

        try:
            file_path = self._sandbox_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            self._logger.error(f"Failed to write file: {e}")
            return False

    def read_file(self, filename: str) -> str | None:
        """从沙箱读取文件

        Args:
            filename: 文件名

        Returns:
            文件内容或 None
        """
        try:
            file_path = self._sandbox_path / filename
            if not file_path.exists():
                return None
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            self._logger.error(f"Failed to read file: {e}")
            return None

    def list_files(self) -> list[str]:
        """列出沙箱中的文件"""
        return [str(f.relative_to(self._sandbox_path)) for f in self._sandbox_path.rglob("*") if f.is_file()]

    def cleanup(self) -> None:
        """清理沙箱"""
        import shutil

        try:
            for item in self._sandbox_path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        except Exception as e:
            self._logger.error(f"Failed to cleanup sandbox: {e}")

        self._status = SandboxStatus.IDLE


code_sandbox = CodeSandbox()
