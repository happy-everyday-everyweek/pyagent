"""
PyAgent 移动端模块 - Linux环境管理

管理移动设备上的嵌入式Linux环境，包括Python后端服务的启动和停止。
v0.8.0: 新增移动端支持
"""

import asyncio
import logging
import os
import platform
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class EnvironmentStatus(Enum):
    """环境状态"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class EnvironmentInfo:
    """环境信息"""
    python_version: str = ""
    linux_distro: str = ""
    architecture: str = ""
    available_memory_mb: float = 0.0
    cpu_cores: int = 0
    is_root: bool = False
    environment_vars: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "python_version": self.python_version,
            "linux_distro": self.linux_distro,
            "architecture": self.architecture,
            "available_memory_mb": self.available_memory_mb,
            "cpu_cores": self.cpu_cores,
            "is_root": self.is_root,
            "environment_vars": self.environment_vars,
        }


@dataclass
class ServiceConfig:
    """服务配置"""
    host: str = "127.0.0.1"
    port: int = 8080
    workers: int = 1
    log_level: str = "info"
    auto_restart: bool = True
    max_restarts: int = 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "workers": self.workers,
            "log_level": self.log_level,
            "auto_restart": self.auto_restart,
            "max_restarts": self.max_restarts,
        }


class LinuxEnv:
    """Linux环境管理器

    管理移动设备上的嵌入式Linux环境，提供Python后端服务的生命周期管理。
    """

    def __init__(self, config: ServiceConfig | None = None):
        self._status = EnvironmentStatus.UNINITIALIZED
        self._config = config or ServiceConfig()
        self._env_info: EnvironmentInfo | None = None
        self._process: subprocess.Popen | None = None
        self._api_endpoint: str = ""
        self._restart_count: int = 0
        self._logger = logging.getLogger(__name__)

    @property
    def status(self) -> EnvironmentStatus:
        return self._status

    @property
    def api_endpoint(self) -> str:
        return self._api_endpoint

    @property
    def config(self) -> ServiceConfig:
        return self._config

    @property
    def env_info(self) -> EnvironmentInfo | None:
        return self._env_info

    def detect_environment(self) -> EnvironmentInfo:
        """检测Linux环境信息"""
        env_info = EnvironmentInfo()

        try:
            env_info.python_version = platform.python_version()
        except Exception:
            pass

        try:
            env_info.architecture = platform.machine()
        except Exception:
            pass

        try:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", encoding="utf-8") as f:
                    content = f.read()
                    for line in content.splitlines():
                        if line.startswith("PRETTY_NAME="):
                            env_info.linux_distro = line.split("=", 1)[1].strip('"')
                            break
        except Exception:
            pass

        try:
            env_info.is_root = os.geteuid() == 0
        except Exception:
            env_info.is_root = False

        try:
            env_info.cpu_cores = os.cpu_count() or 1
        except Exception:
            env_info.cpu_cores = 1

        try:
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("MemAvailable:"):
                            kb = int(line.split()[1])
                            env_info.available_memory_mb = round(kb / 1024, 2)
                            break
        except Exception:
            pass

        env_info.environment_vars = dict(os.environ)

        return env_info

    def initialize(self) -> bool:
        """初始化Linux环境"""
        if self._status == EnvironmentStatus.READY:
            return True

        self._status = EnvironmentStatus.INITIALIZING
        self._logger.info("Initializing Linux environment...")

        try:
            self._env_info = self.detect_environment()
            self._logger.info(f"Environment detected: {self._env_info.linux_distro}")

            required_commands = ["python3", "pip3"]
            for cmd in required_commands:
                if not self._check_command(cmd):
                    self._logger.error(f"Required command not found: {cmd}")
                    self._status = EnvironmentStatus.ERROR
                    return False

            self._api_endpoint = f"http://{self._config.host}:{self._config.port}"
            self._status = EnvironmentStatus.READY
            self._logger.info("Linux environment initialized successfully")
            return True

        except Exception as e:
            self._logger.error(f"Failed to initialize environment: {e}")
            self._status = EnvironmentStatus.ERROR
            return False

    def _check_command(self, command: str) -> bool:
        """检查命令是否存在"""
        try:
            result = subprocess.run(
                ["which", command],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def start_service(self, main_script: str = "src/main.py") -> bool:
        """启动Python后端服务

        Args:
            main_script: 主入口脚本路径

        Returns:
            启动是否成功
        """
        if self._status == EnvironmentStatus.RUNNING:
            self._logger.warning("Service is already running")
            return True

        if self._status != EnvironmentStatus.READY:
            if not self.initialize():
                return False

        try:
            script_path = Path(main_script)
            if not script_path.exists():
                self._logger.error(f"Main script not found: {main_script}")
                self._status = EnvironmentStatus.ERROR
                return False

            cmd = [
                "python3",
                str(script_path),
                "--mode", "web",
                "--host", self._config.host,
                "--port", str(self._config.port),
            ]

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )

            self._status = EnvironmentStatus.RUNNING
            self._logger.info(f"Service started on {self._api_endpoint}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to start service: {e}")
            self._status = EnvironmentStatus.ERROR
            return False

    def stop_service(self) -> bool:
        """停止Python后端服务"""
        if self._status != EnvironmentStatus.RUNNING:
            return True

        try:
            if self._process:
                self._process.terminate()
                try:
                    self._process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait()

                self._process = None

            self._status = EnvironmentStatus.STOPPED
            self._logger.info("Service stopped")
            return True

        except Exception as e:
            self._logger.error(f"Failed to stop service: {e}")
            return False

    def restart_service(self) -> bool:
        """重启服务"""
        if not self.stop_service():
            return False

        self._restart_count += 1

        if self._config.max_restarts > 0 and self._restart_count > self._config.max_restarts:
            self._logger.error("Max restart count exceeded")
            return False

        return self.start_service()

    def is_service_running(self) -> bool:
        """检查服务是否运行"""
        if self._process is None:
            return False

        return self._process.poll() is None

    def get_service_logs(self, lines: int = 100) -> str:
        """获取服务日志"""
        if self._process is None:
            return ""

        try:
            stdout = self._process.stdout
            stderr = self._process.stderr

            logs = []
            if stdout:
                try:
                    output = stdout.read().decode("utf-8", errors="ignore")
                    logs.append(output)
                except Exception:
                    pass

            if stderr:
                try:
                    error = stderr.read().decode("utf-8", errors="ignore")
                    logs.append(error)
                except Exception:
                    pass

            all_logs = "\n".join(logs)
            log_lines = all_logs.splitlines()
            return "\n".join(log_lines[-lines:])

        except Exception:
            return ""

    def get_status_info(self) -> dict[str, Any]:
        """获取状态信息"""
        return {
            "status": self._status.value,
            "api_endpoint": self._api_endpoint,
            "restart_count": self._restart_count,
            "service_running": self.is_service_running(),
            "environment": self._env_info.to_dict() if self._env_info else None,
            "config": self._config.to_dict(),
        }

    async def health_check(self) -> bool:
        """健康检查"""
        if not self.is_service_running():
            return False

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._api_endpoint}/",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception:
            return False

    def cleanup(self) -> None:
        """清理资源"""
        self.stop_service()
        self._status = EnvironmentStatus.UNINITIALIZED
        self._restart_count = 0
