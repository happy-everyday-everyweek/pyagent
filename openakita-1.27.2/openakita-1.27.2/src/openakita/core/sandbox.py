"""
L6: OS 级沙箱 — 按需隔离执行

仅对 HIGH 风险 shell 命令启用沙箱。日常操作不受影响。

支持后端:
- Windows: Low Integrity 进程 (MIC, 零依赖)
- Linux: bubblewrap (bwrap)
- macOS: Seatbelt (sandbox-exec)
- 任何平台: Docker (可选)
"""

from __future__ import annotations

import asyncio
import ctypes
import logging
import platform
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SandboxResult:
    """沙箱执行结果"""
    stdout: str
    stderr: str
    returncode: int
    sandboxed: bool
    backend: str


class SandboxExecutor:
    """
    Unified sandbox interface. Automatically selects the best available
    backend for the current platform.
    """

    def __init__(
        self,
        writable_paths: list[str] | None = None,
        allow_network: bool = False,
        backend: str = "auto",
    ) -> None:
        self._writable_paths = writable_paths or []
        self._allow_network = allow_network
        self._requested_backend = backend
        self._backend: str | None = None

    def detect_backend(self) -> str:
        """Detect the best available sandbox backend."""
        if self._requested_backend != "auto":
            return self._requested_backend

        sys = platform.system()
        if sys == "Linux":
            if shutil.which("bwrap"):
                return "bubblewrap"
        elif sys == "Darwin":
            if shutil.which("sandbox-exec"):
                return "seatbelt"
        elif sys == "Windows":
            return "low_integrity"

        return "none"

    def is_available(self) -> bool:
        backend = self.detect_backend()
        return backend != "none"

    async def execute(
        self,
        command: str,
        cwd: str | None = None,
        timeout: float = 300,
        env: dict[str, str] | None = None,
    ) -> SandboxResult:
        """Execute a command inside the sandbox."""
        backend = self.detect_backend()
        self._backend = backend

        if backend == "bubblewrap":
            return await self._exec_bubblewrap(command, cwd, timeout, env)
        elif backend == "seatbelt":
            return await self._exec_seatbelt(command, cwd, timeout, env)
        elif backend == "low_integrity":
            return await self._exec_low_integrity(command, cwd, timeout, env)
        else:
            return await self._exec_unsandboxed(command, cwd, timeout, env)

    # ----- Linux: bubblewrap -----------------------------------------------

    async def _exec_bubblewrap(
        self, command: str, cwd: str | None, timeout: float,
        env: dict[str, str] | None,
    ) -> SandboxResult:
        args = ["bwrap", "--ro-bind", "/", "/"]

        for wp in self._writable_paths:
            p = str(Path(wp).resolve())
            args.extend(["--bind", p, p])

        args.extend(["--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp"])

        if not self._allow_network:
            args.append("--unshare-net")

        args.extend(["--", "/bin/bash", "-c", command])

        return await self._run_subprocess(
            args, cwd, timeout, env, backend="bubblewrap"
        )

    # ----- macOS: Seatbelt -------------------------------------------------

    async def _exec_seatbelt(
        self, command: str, cwd: str | None, timeout: float,
        env: dict[str, str] | None,
    ) -> SandboxResult:
        rules = ['(version 1)', '(deny default)']
        rules.append('(allow process-exec process-fork)')

        read_paths = ["/usr", "/bin", "/sbin", "/lib", "/System",
                      "/Library", "/private/var", "/private/etc",
                      "/dev/urandom", "/dev/null"]
        for rp in read_paths:
            rules.append(f'(allow file-read* (subpath "{rp}"))')

        for wp in self._writable_paths:
            p = str(Path(wp).resolve())
            rules.append(f'(allow file-read* file-write* (subpath "{p}"))')

        if cwd:
            rules.append(f'(allow file-read* file-write* (subpath "{cwd}"))')

        tmpdir = tempfile.gettempdir()
        rules.append(f'(allow file-read* file-write* (subpath "{tmpdir}"))')

        if self._allow_network:
            rules.append('(allow network*)')

        profile = "\n".join(rules)

        args = ["sandbox-exec", "-p", profile, "/bin/bash", "-c", command]

        return await self._run_subprocess(
            args, cwd, timeout, env, backend="seatbelt"
        )

    # ----- Windows: Low Integrity process ----------------------------------

    async def _exec_low_integrity(
        self, command: str, cwd: str | None, timeout: float,
        env: dict[str, str] | None,
    ) -> SandboxResult:
        if platform.system() != "Windows":
            return await self._exec_unsandboxed(command, cwd, timeout, env)

        for wp in self._writable_paths:
            try:
                subprocess.run(
                    ["icacls", wp, "/setintegritylevel", "(OI)(CI)Low"],
                    capture_output=True, timeout=10,
                )
            except Exception as e:
                logger.debug(f"[Sandbox] icacls failed for {wp}: {e}")

        try:
            result = await self._run_low_integrity_win(
                command, cwd, timeout, env
            )
            return result
        except Exception as e:
            logger.warning(
                f"[Sandbox] Low integrity execution failed, falling back: {e}"
            )
            return await self._exec_unsandboxed(command, cwd, timeout, env)

    async def _run_low_integrity_win(
        self, command: str, cwd: str | None, timeout: float,
        env: dict[str, str] | None,
    ) -> SandboxResult:
        """Create a low-integrity process on Windows using ctypes."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self._sync_low_integrity_win, command, cwd, timeout, env
        )

    def _sync_low_integrity_win(
        self, command: str, cwd: str | None, timeout: float,
        env: dict[str, str] | None,
    ) -> SandboxResult:
        import ctypes.wintypes as wt

        advapi32 = ctypes.windll.advapi32  # type: ignore[attr-defined]
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]

        TOKEN_DUPLICATE = 0x0002
        TOKEN_QUERY = 0x0008
        TOKEN_ADJUST_DEFAULT = 0x0080
        TOKEN_ASSIGN_PRIMARY = 0x0001
        MAXIMUM_ALLOWED = 0x02000000
        SecurityImpersonation = 2
        TokenPrimary = 1
        TokenIntegrityLevel = 25

        LOW_INTEGRITY_SID = "S-1-16-4096"

        CREATE_UNICODE_ENVIRONMENT = 0x00000400

        class STARTUPINFOW(ctypes.Structure):
            _fields_ = [
                ("cb", wt.DWORD), ("lpReserved", wt.LPWSTR),
                ("lpDesktop", wt.LPWSTR), ("lpTitle", wt.LPWSTR),
                ("dwX", wt.DWORD), ("dwY", wt.DWORD),
                ("dwXSize", wt.DWORD), ("dwYSize", wt.DWORD),
                ("dwXCountChars", wt.DWORD), ("dwYCountChars", wt.DWORD),
                ("dwFillAttribute", wt.DWORD), ("dwFlags", wt.DWORD),
                ("wShowWindow", wt.WORD), ("cbReserved2", wt.WORD),
                ("lpReserved2", ctypes.c_void_p),
                ("hStdInput", wt.HANDLE), ("hStdOutput", wt.HANDLE),
                ("hStdError", wt.HANDLE),
            ]

        class PROCESS_INFORMATION(ctypes.Structure):  # noqa: N801
            _fields_ = [
                ("hProcess", wt.HANDLE), ("hThread", wt.HANDLE),
                ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD),
            ]

        h_token = wt.HANDLE()
        h_new_token = wt.HANDLE()
        pi = PROCESS_INFORMATION()
        sid = None

        try:
            if not advapi32.OpenProcessToken(
                kernel32.GetCurrentProcess(),
                TOKEN_DUPLICATE | TOKEN_QUERY | TOKEN_ADJUST_DEFAULT | TOKEN_ASSIGN_PRIMARY,
                ctypes.byref(h_token),
            ):
                raise OSError(f"OpenProcessToken failed: {ctypes.GetLastError()}")

            if not advapi32.DuplicateTokenEx(
                h_token, MAXIMUM_ALLOWED, None,
                SecurityImpersonation, TokenPrimary,
                ctypes.byref(h_new_token),
            ):
                raise OSError(f"DuplicateTokenEx failed: {ctypes.GetLastError()}")

            sid = ctypes.c_void_p()
            if not advapi32.ConvertStringSidToSidW(
                LOW_INTEGRITY_SID, ctypes.byref(sid)
            ):
                raise OSError(f"ConvertStringSidToSidW failed: {ctypes.GetLastError()}")

            class SID_AND_ATTRIBUTES(ctypes.Structure):  # noqa: N801
                _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", wt.DWORD)]

            class TOKEN_MANDATORY_LABEL(ctypes.Structure):  # noqa: N801
                _fields_ = [("Label", SID_AND_ATTRIBUTES)]

            label = TOKEN_MANDATORY_LABEL()
            label.Label.Sid = sid
            label.Label.Attributes = 0x00000020  # SE_GROUP_INTEGRITY

            if not advapi32.SetTokenInformation(
                h_new_token, TokenIntegrityLevel,
                ctypes.byref(label), ctypes.sizeof(label),
            ):
                raise OSError(f"SetTokenInformation failed: {ctypes.GetLastError()}")

            si = STARTUPINFOW()
            si.cb = ctypes.sizeof(STARTUPINFOW)

            out_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
                mode="w", suffix="_sb_out.txt", delete=False
            )
            err_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
                mode="w", suffix="_sb_err.txt", delete=False
            )
            out_path = out_file.name
            err_path = err_file.name
            out_file.close()
            err_file.close()

            escaped_cmd = command.replace('"', '\\"')
            full_cmd = f'cmd /c "{escaped_cmd}" > "{out_path}" 2> "{err_path}"'
            cmd_line = ctypes.create_unicode_buffer(full_cmd)

            if not advapi32.CreateProcessAsUserW(
                h_new_token,
                None,
                cmd_line,
                None, None, False,
                CREATE_UNICODE_ENVIRONMENT,
                None,
                cwd,
                ctypes.byref(si),
                ctypes.byref(pi),
            ):
                raise OSError(
                    f"CreateProcessAsUserW failed: {ctypes.GetLastError()}"
                )

            timeout_ms = int(timeout * 1000)
            kernel32.WaitForSingleObject(pi.hProcess, timeout_ms)

            exit_code = wt.DWORD()
            kernel32.GetExitCodeProcess(pi.hProcess, ctypes.byref(exit_code))

            stdout_text = ""
            stderr_text = ""
            try:
                with open(out_path, encoding="utf-8", errors="replace") as f:
                    stdout_text = f.read()
            except Exception:
                pass
            try:
                with open(err_path, encoding="utf-8", errors="replace") as f:
                    stderr_text = f.read()
            except Exception:
                pass

            import os
            for p in (out_path, err_path):
                try:
                    os.unlink(p)
                except Exception:
                    pass

            return SandboxResult(
                stdout=stdout_text,
                stderr=stderr_text,
                returncode=exit_code.value,
                sandboxed=True,
                backend="low_integrity",
            )

        except Exception:
            raise
        finally:
            if sid:
                kernel32.LocalFree(sid)
            for h in (h_token, h_new_token, pi.hProcess, pi.hThread):
                if h:
                    kernel32.CloseHandle(h)

    # ----- Fallback: unsandboxed -------------------------------------------

    async def _exec_unsandboxed(
        self, command: str, cwd: str | None, timeout: float,
        env: dict[str, str] | None,
    ) -> SandboxResult:
        result = await self._run_subprocess(
            ["/bin/bash", "-c", command] if platform.system() != "Windows"
            else ["cmd", "/c", command],
            cwd, timeout, env, backend="none",
        )
        result.sandboxed = False
        return result

    # ----- Shared subprocess runner ----------------------------------------

    async def _run_subprocess(
        self, args: list[str], cwd: str | None, timeout: float,
        env: dict[str, str] | None, backend: str,
    ) -> SandboxResult:
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return SandboxResult(
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                returncode=proc.returncode or 0,
                sandboxed=True,
                backend=backend,
            )
        except TimeoutError:
            if proc:
                proc.kill()
            return SandboxResult(
                stdout="", stderr="Sandbox execution timed out",
                returncode=-1, sandboxed=True, backend=backend,
            )
        except FileNotFoundError:
            return SandboxResult(
                stdout="",
                stderr=f"Sandbox backend '{backend}' not found",
                returncode=-1, sandboxed=False, backend="none",
            )


_global_sandbox: SandboxExecutor | None = None


def get_sandbox_executor() -> SandboxExecutor:
    global _global_sandbox
    if _global_sandbox is None:
        try:
            from .policy import get_policy_engine
            cfg = get_policy_engine().config
            writable = (
                cfg.zones.workspace + cfg.zones.controlled
            )
            writable = [
                str(Path.cwd()).replace("\\", "/") if p == "${CWD}" else p
                for p in writable
            ]
            _global_sandbox = SandboxExecutor(
                writable_paths=writable,
                allow_network=cfg.sandbox.network_allow_in_sandbox,
                backend=cfg.sandbox.backend,
            )
        except Exception:
            _global_sandbox = SandboxExecutor()
    return _global_sandbox
