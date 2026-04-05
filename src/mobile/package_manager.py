"""
PyAgent 移动端模块 - 包管理器

提供Android应用包管理功能，包括应用列表、启动、停止等操作。
v0.8.0: 新增包管理支持

参考: Operit项目 PackageManager模块
"""

import logging
import os
import platform
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PackageState(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


class PackageType(Enum):
    SYSTEM = "system"
    THIRD_PARTY = "third_party"
    ALL = "all"


@dataclass
class PackageInfo:
    package_name: str
    version_name: str = ""
    version_code: int = 0
    label: str = ""
    icon_path: str = ""
    data_dir: str = ""
    source_dir: str = ""
    is_system: bool = False
    is_enabled: bool = True
    install_time: int = 0
    update_time: int = 0
    size_bytes: int = 0
    permissions: list[str] = field(default_factory=list)
    flags: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_name": self.package_name,
            "version_name": self.version_name,
            "version_code": self.version_code,
            "label": self.label,
            "icon_path": self.icon_path,
            "data_dir": self.data_dir,
            "source_dir": self.source_dir,
            "is_system": self.is_system,
            "is_enabled": self.is_enabled,
            "install_time": self.install_time,
            "update_time": self.update_time,
            "size_bytes": self.size_bytes,
            "permissions": self.permissions,
            "flags": self.flags,
        }


@dataclass
class RunningPackage:
    package_name: str
    pid: int = 0
    uid: int = 0
    process_name: str = ""
    memory_kb: int = 0
    cpu_percent: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_name": self.package_name,
            "pid": self.pid,
            "uid": self.uid,
            "process_name": self.process_name,
            "memory_kb": self.memory_kb,
            "cpu_percent": self.cpu_percent,
        }


@dataclass
class PackageManagerConfig:
    adb_path: str = "adb"
    use_shizuku: bool = False
    use_root: bool = False
    cache_enabled: bool = True
    cache_ttl_seconds: int = 60
    timeout_seconds: int = 30


class PackageManager:
    _instance: Optional["PackageManager"] = None
    _lock = threading.Lock()

    def __new__(cls, config: PackageManagerConfig | None = None) -> "PackageManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: PackageManagerConfig | None = None):
        if self._initialized:
            return

        self._config = config or PackageManagerConfig()
        self._package_cache: dict[str, PackageInfo] = {}
        self._cache_time: float = 0
        self._running_cache: dict[str, RunningPackage] = {}
        self._running_cache_time: float = 0
        self._is_android: bool = False
        self._has_adb: bool = False
        self._has_root: bool = False
        self._initialized = True

        self._detect_environment()

    def _detect_environment(self) -> None:
        system = platform.system().lower()

        if system == "linux":
            if "android" in platform.platform().lower():
                self._is_android = True
            elif os.path.exists("/system/bin") or os.path.exists("/vendor/bin"):
                self._is_android = True

        try:
            result = subprocess.run(
                [self._config.adb_path, "version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                self._has_adb = True
                logger.info(f"ADB available: {result.stdout.split()[0] if result.stdout else 'unknown'}")
        except Exception:
            self._has_adb = False
            logger.debug("ADB not available")

        if self._is_android:
            try:
                result = subprocess.run(
                    ["which", "su"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if result.returncode == 0:
                    test_result = subprocess.run(
                        ["su", "-c", "id"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if "uid=0" in test_result.stdout:
                        self._has_root = True
                        logger.info("Root access available")
            except Exception:
                self._has_root = False

    @property
    def is_android(self) -> bool:
        return self._is_android

    @property
    def has_adb(self) -> bool:
        return self._has_adb

    @property
    def has_root(self) -> bool:
        return self._has_root

    def _run_command(self, cmd: list[str], use_root: bool = False) -> tuple[bool, str]:
        try:
            if use_root and self._has_root:
                cmd = ["su", "-c", " ".join(cmd)]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._config.timeout_seconds,
            )
            return result.returncode == 0, result.stdout.strip()

        except subprocess.TimeoutExpired:
            return False, "Command timeout"
        except Exception as e:
            return False, str(e)

    def _run_adb_command(self, args: list[str], device: str | None = None) -> tuple[bool, str]:
        if not self._has_adb:
            return False, "ADB not available"

        try:
            cmd = [self._config.adb_path]
            if device:
                cmd.extend(["-s", device])
            cmd.extend(args)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._config.timeout_seconds,
            )
            return result.returncode == 0, result.stdout.strip()

        except subprocess.TimeoutExpired:
            return False, "ADB command timeout"
        except Exception as e:
            return False, str(e)

    def list_packages(
        self,
        package_type: PackageType = PackageType.ALL,
        use_cache: bool = True,
    ) -> list[PackageInfo]:
        current_time = time.time()

        if (
            use_cache
            and self._config.cache_enabled
            and self._package_cache
            and current_time - self._cache_time < self._config.cache_ttl_seconds
        ):
            packages = list(self._package_cache.values())
            if package_type == PackageType.SYSTEM:
                return [p for p in packages if p.is_system]
            elif package_type == PackageType.THIRD_PARTY:
                return [p for p in packages if not p.is_system]
            return packages

        packages = []

        if self._is_android:
            packages = self._list_packages_android(package_type)
        elif self._has_adb:
            packages = self._list_packages_adb(package_type)
        else:
            packages = self._list_packages_simulation()

        if self._config.cache_enabled:
            self._package_cache = {p.package_name: p for p in packages}
            self._cache_time = current_time

        return packages

    def _list_packages_android(self, package_type: PackageType) -> list[PackageInfo]:
        packages = []

        try:
            cmd_args = ["pm", "list", "packages", "-f", "-i", "-u"]
            if package_type == PackageType.SYSTEM:
                cmd_args.append("-s")
            elif package_type == PackageType.THIRD_PARTY:
                cmd_args.append("-3")

            success, output = self._run_command(cmd_args)
            if not success:
                logger.warning(f"Failed to list packages: {output}")
                return self._list_packages_simulation()

            for line in output.split("\n"):
                if not line.startswith("package:"):
                    continue

                package_info = self._parse_package_line(line)
                if package_info:
                    packages.append(package_info)

        except Exception as e:
            logger.error(f"Error listing packages: {e}")

        return packages

    def _list_packages_adb(self, package_type: PackageType) -> list[PackageInfo]:
        packages = []

        try:
            cmd_args = ["shell", "pm", "list", "packages", "-f"]
            if package_type == PackageType.SYSTEM:
                cmd_args[-1] = "-s"
            elif package_type == PackageType.THIRD_PARTY:
                cmd_args[-1] = "-3"

            success, output = self._run_adb_command(cmd_args)
            if not success:
                logger.warning(f"Failed to list packages via ADB: {output}")
                return self._list_packages_simulation()

            for line in output.split("\n"):
                if not line.startswith("package:"):
                    continue

                package_info = self._parse_package_line(line)
                if package_info:
                    packages.append(package_info)

        except Exception as e:
            logger.error(f"Error listing packages via ADB: {e}")

        return packages

    def _list_packages_simulation(self) -> list[PackageInfo]:
        return [
            PackageInfo(
                package_name="com.example.app1",
                version_name="1.0.0",
                version_code=1,
                label="Example App 1",
                is_system=False,
                is_enabled=True,
            ),
            PackageInfo(
                package_name="com.example.app2",
                version_name="2.0.0",
                version_code=2,
                label="Example App 2",
                is_system=False,
                is_enabled=True,
            ),
            PackageInfo(
                package_name="com.android.settings",
                version_name="12",
                version_code=31,
                label="Settings",
                is_system=True,
                is_enabled=True,
            ),
        ]

    def _parse_package_line(self, line: str) -> PackageInfo | None:
        try:
            match = re.match(r"package:(.+?)=(\S+)\s*", line)
            if not match:
                return None

            source_dir = match.group(1)
            package_name = match.group(2)

            return PackageInfo(
                package_name=package_name,
                source_dir=source_dir,
                is_system="/system/" in source_dir or "/vendor/" in source_dir,
            )

        except Exception:
            return None

    def get_package_info(self, package_name: str) -> PackageInfo | None:
        if self._config.cache_enabled and package_name in self._package_cache:
            return self._package_cache[package_name]

        if self._is_android:
            return self._get_package_info_android(package_name)
        elif self._has_adb:
            return self._get_package_info_adb(package_name)
        else:
            for pkg in self._list_packages_simulation():
                if pkg.package_name == package_name:
                    return pkg
            return None

    def _get_package_info_android(self, package_name: str) -> PackageInfo | None:
        try:
            success, output = self._run_command(
                ["dumpsys", "package", package_name]
            )
            if not success:
                return None

            info = PackageInfo(package_name=package_name)

            version_match = re.search(r"versionName=([^\s]+)", output)
            if version_match:
                info.version_name = version_match.group(1)

            version_code_match = re.search(r"versionCode=(\d+)", output)
            if version_code_match:
                info.version_code = int(version_code_match.group(1))

            flags_match = re.search(r"flags=\[([^\]]+)\]", output)
            if flags_match:
                flags_str = flags_match.group(1)
                info.is_system = "SYSTEM" in flags_str

            data_dir_match = re.search(r"dataDir=([^\s]+)", output)
            if data_dir_match:
                info.data_dir = data_dir_match.group(1)

            source_dir_match = re.search(r"sourceDir=([^\s]+)", output)
            if source_dir_match:
                info.source_dir = source_dir_match.group(1)

            enabled_match = re.search(r"enabled=(\d+)", output)
            if enabled_match:
                info.is_enabled = enabled_match.group(1) == "1"

            permissions = re.findall(r"android\.permission\.\w+", output)
            info.permissions = list(set(permissions))

            return info

        except Exception as e:
            logger.error(f"Error getting package info: {e}")
            return None

    def _get_package_info_adb(self, package_name: str) -> PackageInfo | None:
        try:
            success, output = self._run_adb_command(
                ["shell", "dumpsys", "package", package_name]
            )
            if not success:
                return None

            info = PackageInfo(package_name=package_name)

            version_match = re.search(r"versionName=([^\s]+)", output)
            if version_match:
                info.version_name = version_match.group(1)

            version_code_match = re.search(r"versionCode=(\d+)", output)
            if version_code_match:
                info.version_code = int(version_code_match.group(1))

            return info

        except Exception as e:
            logger.error(f"Error getting package info via ADB: {e}")
            return None

    def launch_package(self, package_name: str) -> bool:
        logger.info(f"Launching package: {package_name}")

        if self._is_android:
            return self._launch_package_android(package_name)
        elif self._has_adb:
            return self._launch_package_adb(package_name)
        else:
            logger.info(f"[Simulation] Launched package: {package_name}")
            return True

    def _launch_package_android(self, package_name: str) -> bool:
        try:
            success, output = self._run_command(
                ["monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"]
            )
            if success:
                logger.info(f"Successfully launched: {package_name}")
                return True

            success, output = self._run_command(
                ["am", "start", "-n", f"{package_name}/.MainActivity"]
            )
            return success

        except Exception as e:
            logger.error(f"Error launching package: {e}")
            return False

    def _launch_package_adb(self, package_name: str) -> bool:
        try:
            success, output = self._run_adb_command(
                ["shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"]
            )
            return success

        except Exception as e:
            logger.error(f"Error launching package via ADB: {e}")
            return False

    def force_stop(self, package_name: str) -> bool:
        logger.info(f"Force stopping package: {package_name}")

        if self._is_android:
            return self._force_stop_android(package_name)
        elif self._has_adb:
            return self._force_stop_adb(package_name)
        else:
            logger.info(f"[Simulation] Force stopped package: {package_name}")
            return True

    def _force_stop_android(self, package_name: str) -> bool:
        try:
            success, _ = self._run_command(["am", "force-stop", package_name])
            if success:
                logger.info(f"Successfully force stopped: {package_name}")
            return success

        except Exception as e:
            logger.error(f"Error force stopping package: {e}")
            return False

    def _force_stop_adb(self, package_name: str) -> bool:
        try:
            success, _ = self._run_adb_command(
                ["shell", "am", "force-stop", package_name]
            )
            return success

        except Exception as e:
            logger.error(f"Error force stopping package via ADB: {e}")
            return False

    def get_running_packages(self, use_cache: bool = True) -> list[RunningPackage]:
        current_time = time.time()

        if (
            use_cache
            and self._config.cache_enabled
            and self._running_cache
            and current_time - self._running_cache_time < self._config.cache_ttl_seconds
        ):
            return list(self._running_cache.values())

        packages = []

        if self._is_android:
            packages = self._get_running_packages_android()
        elif self._has_adb:
            packages = self._get_running_packages_adb()
        else:
            packages = self._get_running_packages_simulation()

        if self._config.cache_enabled:
            self._running_cache = {p.package_name: p for p in packages}
            self._running_cache_time = current_time

        return packages

    def _get_running_packages_android(self) -> list[RunningPackage]:
        packages = []

        try:
            success, output = self._run_command(["ps", "-A"])
            if not success:
                return self._get_running_packages_simulation()

            for line in output.split("\n")[1:]:
                parts = line.split()
                if len(parts) >= 9:
                    package_name = parts[-1]
                    if "." in package_name:
                        packages.append(RunningPackage(
                            package_name=package_name,
                            pid=int(parts[1]) if parts[1].isdigit() else 0,
                            uid=int(parts[0]) if parts[0].isdigit() else 0,
                            process_name=package_name,
                        ))

        except Exception as e:
            logger.error(f"Error getting running packages: {e}")

        return packages

    def _get_running_packages_adb(self) -> list[RunningPackage]:
        packages = []

        try:
            success, output = self._run_adb_command(["shell", "ps", "-A"])
            if not success:
                return self._get_running_packages_simulation()

            for line in output.split("\n")[1:]:
                parts = line.split()
                if len(parts) >= 9:
                    package_name = parts[-1]
                    if "." in package_name:
                        packages.append(RunningPackage(
                            package_name=package_name,
                            pid=int(parts[1]) if parts[1].isdigit() else 0,
                        ))

        except Exception as e:
            logger.error(f"Error getting running packages via ADB: {e}")

        return packages

    def _get_running_packages_simulation(self) -> list[RunningPackage]:
        return [
            RunningPackage(
                package_name="com.example.app1",
                pid=12345,
                uid=10001,
                process_name="com.example.app1",
                memory_kb=50000,
                cpu_percent=2.5,
            ),
            RunningPackage(
                package_name="com.android.systemui",
                pid=1000,
                uid=1000,
                process_name="com.android.systemui",
                memory_kb=80000,
                cpu_percent=1.2,
            ),
        ]

    def is_package_running(self, package_name: str) -> bool:
        running = self.get_running_packages()
        return any(p.package_name == package_name for p in running)

    def clear_cache(self, package_name: str) -> bool:
        logger.info(f"Clearing cache for package: {package_name}")

        if self._is_android:
            return self._clear_cache_android(package_name)
        elif self._has_adb:
            return self._clear_cache_adb(package_name)
        else:
            logger.info(f"[Simulation] Cleared cache for: {package_name}")
            return True

    def _clear_cache_android(self, package_name: str) -> bool:
        try:
            success, _ = self._run_command(
                ["pm", "clear", package_name],
                use_root=self._has_root,
            )
            return success

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def _clear_cache_adb(self, package_name: str) -> bool:
        try:
            success, _ = self._run_adb_command(
                ["shell", "pm", "clear", package_name]
            )
            return success

        except Exception as e:
            logger.error(f"Error clearing cache via ADB: {e}")
            return False

    def enable_package(self, package_name: str) -> bool:
        logger.info(f"Enabling package: {package_name}")

        if self._is_android:
            try:
                success, _ = self._run_command(
                    ["pm", "enable", package_name],
                    use_root=self._has_root,
                )
                return success
            except Exception as e:
                logger.error(f"Error enabling package: {e}")
                return False
        elif self._has_adb:
            try:
                success, _ = self._run_adb_command(
                    ["shell", "pm", "enable", package_name]
                )
                return success
            except Exception:
                return False
        else:
            logger.info(f"[Simulation] Enabled package: {package_name}")
            return True

    def disable_package(self, package_name: str) -> bool:
        logger.info(f"Disabling package: {package_name}")

        if self._is_android:
            try:
                success, _ = self._run_command(
                    ["pm", "disable", package_name],
                    use_root=self._has_root,
                )
                return success
            except Exception as e:
                logger.error(f"Error disabling package: {e}")
                return False
        elif self._has_adb:
            try:
                success, _ = self._run_adb_command(
                    ["shell", "pm", "disable", package_name]
                )
                return success
            except Exception:
                return False
        else:
            logger.info(f"[Simulation] Disabled package: {package_name}")
            return True

    def get_package_size(self, package_name: str) -> dict[str, int]:
        if self._is_android:
            try:
                success, output = self._run_command(
                    ["dumpsys", "package", package_name]
                )
                if success:
                    code_match = re.search(r"codeSize=(\d+)", output)
                    data_match = re.search(r"dataSize=(\d+)", output)
                    cache_match = re.search(r"cacheSize=(\d+)", output)

                    return {
                        "code_size": int(code_match.group(1)) if code_match else 0,
                        "data_size": int(data_match.group(1)) if data_match else 0,
                        "cache_size": int(cache_match.group(1)) if cache_match else 0,
                    }
            except Exception as e:
                logger.error(f"Error getting package size: {e}")

        return {
            "code_size": 0,
            "data_size": 0,
            "cache_size": 0,
        }

    def clear_cache_all(self) -> None:
        self._package_cache.clear()
        self._running_cache.clear()
        self._cache_time = 0
        self._running_cache_time = 0

    @classmethod
    def reset_instance(cls) -> None:
        if cls._instance:
            cls._instance.clear_cache_all()
            cls._instance = None


package_manager = PackageManager()
