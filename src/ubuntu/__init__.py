"""Ubuntu environment management for PyAgent."""

import asyncio
import logging
import shutil
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PackageManager(Enum):
    APT = "apt"
    PIP = "pip"
    NPM = "npm"
    SNAP = "snap"


@dataclass
class PackageInfo:
    name: str
    version: str
    installed: bool
    description: str = ""


@dataclass
class EnvironmentConfig:
    name: str
    python_version: str = "3.12"
    node_version: str = "20"
    packages: list[str] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)
    working_dir: str = "/workspace"


class UbuntuEnvironment:
    """Manages Ubuntu/WSL environment for PyAgent."""

    def __init__(self, base_dir: str = "data/ubuntu"):
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._is_wsl = self._detect_wsl()
        self._environments: dict[str, EnvironmentConfig] = {}

    def _detect_wsl(self) -> bool:
        try:
            with open("/proc/version", encoding="utf-8") as f:
                return "microsoft" in f.read().lower() or "wsl" in f.read().lower()
        except FileNotFoundError:
            return False

    async def execute_command(self, command: str, cwd: str | None = None) -> dict[str, Any]:
        """Execute a command in the Ubuntu environment."""
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or str(self._base_dir),
            )
            stdout, stderr = await proc.communicate()
            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def install_package(
        self, package: str, manager: PackageManager = PackageManager.APT
    ) -> dict[str, Any]:
        """Install a package using the specified package manager."""
        commands = {
            PackageManager.APT: f"sudo apt-get install -y {package}",
            PackageManager.PIP: f"pip install {package}",
            PackageManager.NPM: f"npm install -g {package}",
            PackageManager.SNAP: f"sudo snap install {package}",
        }
        command = commands.get(manager, commands[PackageManager.APT])
        return await self.execute_command(command)

    async def uninstall_package(
        self, package: str, manager: PackageManager = PackageManager.APT
    ) -> dict[str, Any]:
        """Uninstall a package."""
        commands = {
            PackageManager.APT: f"sudo apt-get remove -y {package}",
            PackageManager.PIP: f"pip uninstall -y {package}",
            PackageManager.NPM: f"npm uninstall -g {package}",
            PackageManager.SNAP: f"sudo snap remove {package}",
        }
        command = commands.get(manager, commands[PackageManager.APT])
        return await self.execute_command(command)

    async def list_packages(self, manager: PackageManager = PackageManager.APT) -> list[PackageInfo]:
        """List installed packages."""
        packages = []
        if manager == PackageManager.APT:
            result = await self.execute_command("dpkg -l")
            if result["success"]:
                for line in result["stdout"].split("\n")[5:]:
                    parts = line.split()
                    if len(parts) >= 3:
                        packages.append(
                            PackageInfo(
                                name=parts[1],
                                version=parts[2],
                                installed=True,
                            )
                        )
        elif manager == PackageManager.PIP:
            result = await self.execute_command("pip list --format=json")
            if result["success"]:
                import json

                try:
                    data = json.loads(result["stdout"])
                    for item in data:
                        packages.append(
                            PackageInfo(
                                name=item.get("name", ""),
                                version=item.get("version", ""),
                                installed=True,
                            )
                        )
                except json.JSONDecodeError:
                    pass
        return packages

    async def update_system(self) -> dict[str, Any]:
        """Update system packages."""
        result1 = await self.execute_command("sudo apt-get update")
        if not result1["success"]:
            return result1
        return await self.execute_command("sudo apt-get upgrade -y")

    async def create_virtualenv(self, name: str, python_version: str = "3.12") -> dict[str, Any]:
        """Create a Python virtual environment."""
        venv_path = self._base_dir / "venvs" / name
        venv_path.parent.mkdir(parents=True, exist_ok=True)
        return await self.execute_command(f"python{python_version} -m venv {venv_path}")

    async def run_python_script(self, script: str, env_name: str | None = None) -> dict[str, Any]:
        """Run a Python script."""
        if env_name:
            venv_path = self._base_dir / "venvs" / env_name
            python_cmd = f"{venv_path}/bin/python"
        else:
            python_cmd = "python3"
        return await self.execute_command(f"{python_cmd} -c '{script}'")

    async def run_node_script(self, script: str) -> dict[str, Any]:
        """Run a Node.js script."""
        return await self.execute_command(f"node -e '{script}'")

    async def setup_environment(self, config: EnvironmentConfig) -> dict[str, Any]:
        """Set up a complete development environment."""
        results = []

        await self.create_virtualenv(config.name, config.python_version)
        results.append({"step": "create_venv", "success": True})

        for package in config.packages:
            result = await self.install_package(package, PackageManager.PIP)
            results.append({"step": "install_package", "package": package, "success": result["success"]})

        self._environments[config.name] = config
        return {"success": True, "results": results}

    def get_environment(self, name: str) -> EnvironmentConfig | None:
        return self._environments.get(name)

    def list_environments(self) -> list[str]:
        return list(self._environments.keys())

    @property
    def is_wsl(self) -> bool:
        return self._is_wsl


_ubuntu_env: UbuntuEnvironment | None = None


def get_ubuntu_environment() -> UbuntuEnvironment:
    global _ubuntu_env
    if _ubuntu_env is None:
        _ubuntu_env = UbuntuEnvironment()
    return _ubuntu_env
