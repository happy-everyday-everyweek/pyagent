import platform
import re
import shutil
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .base import PlatformAdapter, PlatformCapabilities


class FileSystemAccess:
    def __init__(self, base_path: Path | str | None = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self._watchers: dict[str, list[Callable]] = {}
        self._watch_threads: dict[str, threading.Thread] = {}
        self._watch_running: dict[str, bool] = {}

    def read_file(self, path: str | Path) -> bytes:
        full_path = self._resolve_path(path)
        return full_path.read_bytes()

    def write_file(self, path: str | Path, data: bytes) -> None:
        full_path = self._resolve_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)

    def delete_file(self, path: str | Path) -> None:
        full_path = self._resolve_path(path)
        if full_path.exists():
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink()

    def list_files(self, directory: str | Path) -> list[dict[str, Any]]:
        full_path = self._resolve_path(directory)
        if not full_path.exists() or not full_path.is_dir():
            return []
        result = []
        for item in full_path.iterdir():
            result.append({
                "name": item.name,
                "path": str(item.relative_to(self.base_path)),
                "is_dir": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else 0,
                "modified": item.stat().st_mtime,
            })
        return result

    def file_exists(self, path: str | Path) -> bool:
        full_path = self._resolve_path(path)
        return full_path.exists()

    def get_file_info(self, path: str | Path) -> dict[str, Any]:
        full_path = self._resolve_path(path)
        if not full_path.exists():
            return {}
        stat = full_path.stat()
        return {
            "name": full_path.name,
            "path": str(full_path.relative_to(self.base_path)),
            "is_dir": full_path.is_dir(),
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime,
        }

    def watch_directory(self, path: str | Path, callback: Callable[[str, str], None]) -> bool:
        full_path = self._resolve_path(path)
        if not full_path.exists() or not full_path.is_dir():
            return False
        watch_key = str(full_path)
        if watch_key in self._watchers:
            self._watchers[watch_key].append(callback)
        else:
            self._watchers[watch_key] = [callback]
            self._watch_running[watch_key] = True
            thread = threading.Thread(
                target=self._watch_loop,
                args=(watch_key,),
                daemon=True
            )
            thread.start()
            self._watch_threads[watch_key] = thread
        return True

    def stop_watch(self, path: str | Path) -> None:
        full_path = self._resolve_path(path)
        watch_key = str(full_path)
        if watch_key in self._watch_running:
            self._watch_running[watch_key] = False
            del self._watchers[watch_key]
            if watch_key in self._watch_threads:
                del self._watch_threads[watch_key]

    def _resolve_path(self, path: str | Path) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return self.base_path / p

    def _watch_loop(self, watch_key: str) -> None:
        import time
        path = Path(watch_key)
        last_state = self._get_dir_state(path)
        while self._watch_running.get(watch_key, False):
            time.sleep(1)
            current_state = self._get_dir_state(path)
            changes = self._detect_changes(last_state, current_state)
            for change_type, file_path in changes:
                for callback in self._watchers.get(watch_key, []):
                    try:
                        callback(change_type, file_path)
                    except Exception:
                        pass
            last_state = current_state

    def _get_dir_state(self, path: Path) -> dict[str, float]:
        state = {}
        for item in path.rglob("*"):
            if item.is_file():
                state[str(item)] = item.stat().st_mtime
        return state

    def _detect_changes(
        self,
        old_state: dict[str, float],
        new_state: dict[str, float]
    ) -> list[tuple[str, str]]:
        changes = []
        for path, mtime in new_state.items():
            if path not in old_state:
                changes.append(("created", path))
            elif old_state[path] != mtime:
                changes.append(("modified", path))
        for path in old_state:
            if path not in new_state:
                changes.append(("deleted", path))
        return changes


class HardwareEncoder:
    def __init__(self):
        self._available_encoders: list[str] | None = None
        self._ffmpeg_path: str | None = None

    @property
    def available_encoders(self) -> list[str]:
        if self._available_encoders is None:
            self._available_encoders = self.detect_encoders()
        return self._available_encoders

    def detect_encoders(self) -> list[str]:
        encoders: list[str] = []
        ffmpeg_path = self._find_ffmpeg()
        if not ffmpeg_path:
            return encoders
        try:
            result = subprocess.run(
                [ffmpeg_path, "-encoders"],
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout
            encoder_patterns = [
                (r"h264_nvenc", "h264_nvenc"),
                (r"hevc_nvenc", "hevc_nvenc"),
                (r"h264_qsv", "h264_qsv"),
                (r"hevc_qsv", "hevc_qsv"),
                (r"h264_videotoolbox", "h264_videotoolbox"),
                (r"hevc_videotoolbox", "hevc_videotoolbox"),
                (r"h264_vaapi", "h264_vaapi"),
                (r"hevc_vaapi", "hevc_vaapi"),
                (r"libx264", "libx264"),
                (r"libx265", "libx265"),
            ]
            for pattern, encoder_name in encoder_patterns:
                if re.search(pattern, output):
                    encoders.append(encoder_name)
        except Exception:
            pass
        return encoders

    def has_nvenc(self) -> bool:
        return "h264_nvenc" in self.available_encoders

    def has_qsv(self) -> bool:
        return "h264_qsv" in self.available_encoders

    def has_videotoolbox(self) -> bool:
        return "h264_videotoolbox" in self.available_encoders

    def get_recommended_encoder(self) -> str:
        if self.has_nvenc():
            return "h264_nvenc"
        if self.has_qsv():
            return "h264_qsv"
        if self.has_videotoolbox():
            return "h264_videotoolbox"
        if "libx264" in self.available_encoders:
            return "libx264"
        return "libx264"

    def get_encoder_options(self, encoder: str) -> dict[str, Any]:
        options: dict[str, Any] = {
            "preset": "medium",
            "bitrate": "8M",
            "crf": 23,
        }
        if encoder in ("h264_nvenc", "hevc_nvenc"):
            options.update({
                "preset": "p4",
                "tune": "hq",
                "rc": "vbr",
                "cq": "23",
            })
        elif encoder in ("h264_qsv", "hevc_qsv"):
            options.update({
                "preset": "medium",
                "global_quality": "23",
            })
        elif encoder in ("h264_videotoolbox", "hevc_videotoolbox"):
            options.update({
                "q:v": "65",
                "profile": "high",
            })
        elif encoder in ("libx264", "libx265"):
            options.update({
                "preset": "medium",
                "crf": "23",
            })
        return options

    def _find_ffmpeg(self) -> str | None:
        if self._ffmpeg_path:
            return self._ffmpeg_path
        self._ffmpeg_path = shutil.which("ffmpeg")
        return self._ffmpeg_path


class FFmpegRenderer:
    def __init__(self, ffmpeg_path: str | None = None):
        self.ffmpeg_path = ffmpeg_path or self._detect_ffmpeg_path()
        self._render_process: subprocess.Popen | None = None
        self._render_progress: float = 0.0
        self._total_duration: float = 0.0
        self._is_rendering: bool = False

    def detect_ffmpeg(self) -> bool:
        return self.ffmpeg_path is not None

    def get_ffmpeg_version(self) -> str:
        if not self.ffmpeg_path:
            return ""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            first_line = result.stdout.split("\n")[0]
            match = re.search(r"ffmpeg version (\S+)", first_line)
            if match:
                return match.group(1)
        except Exception:
            pass
        return ""

    def render(
        self,
        input_files: list[str],
        output_path: str,
        config: dict[str, Any]
    ) -> bool:
        if not self.ffmpeg_path:
            return False
        if self._is_rendering:
            return False
        self._is_rendering = True
        self._render_progress = 0.0
        cmd = self._build_render_command(input_files, output_path, config)
        try:
            self._total_duration = self._get_total_duration(input_files)
            self._render_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self._monitor_render_progress()
            return self._render_process.returncode == 0
        except Exception:
            self._is_rendering = False
            return False

    def get_render_progress(self) -> float:
        return self._render_progress

    def cancel_render(self) -> None:
        if self._render_process and self._is_rendering:
            self._render_process.terminate()
            try:
                self._render_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._render_process.kill()
            self._is_rendering = False
            self._render_progress = 0.0

    def _detect_ffmpeg_path(self) -> str | None:
        return shutil.which("ffmpeg")

    def _build_render_command(
        self,
        input_files: list[str],
        output_path: str,
        config: dict[str, Any]
    ) -> list[str]:
        cmd = [self.ffmpeg_path, "-y"]
        for input_file in input_files:
            cmd.extend(["-i", input_file])
        encoder = config.get("encoder", "libx264")
        cmd.extend(["-c:v", encoder])
        encoder_opts = config.get("encoder_options", {})
        if encoder in ("h264_nvenc", "hevc_nvenc"):
            if "preset" in encoder_opts:
                cmd.extend(["-preset:v", str(encoder_opts["preset"])])
            if "bitrate" in encoder_opts:
                cmd.extend(["-b:v", str(encoder_opts["bitrate"])])
        elif encoder in ("h264_qsv", "hevc_qsv"):
            if "preset" in encoder_opts:
                cmd.extend(["-preset:v", str(encoder_opts["preset"])])
            if "global_quality" in encoder_opts:
                cmd.extend(["-global_quality", str(encoder_opts["global_quality"])])
        elif encoder in ("libx264", "libx265"):
            if "preset" in encoder_opts:
                cmd.extend(["-preset", str(encoder_opts["preset"])])
            if "crf" in encoder_opts:
                cmd.extend(["-crf", str(encoder_opts["crf"])])
        resolution = config.get("resolution")
        if resolution:
            cmd.extend(["-s", f"{resolution[0]}x{resolution[1]}"])
        fps = config.get("fps")
        if fps:
            cmd.extend(["-r", str(fps)])
        cmd.extend(["-c:a", config.get("audio_codec", "aac")])
        cmd.append(output_path)
        return cmd

    def _get_total_duration(self, input_files: list[str]) -> float:
        if not self.ffmpeg_path or not input_files:
            return 0.0
        total = 0.0
        for input_file in input_files:
            try:
                result = subprocess.run(
                    [self.ffmpeg_path.replace("ffmpeg", "ffprobe") or "ffprobe",
                     "-v", "error",
                     "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1",
                     input_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                duration = float(result.stdout.strip())
                total += duration
            except Exception:
                pass
        return total

    def _monitor_render_progress(self) -> None:
        if not self._render_process:
            return
        stderr = self._render_process.stderr
        if not stderr:
            return
        while True:
            line = stderr.readline()
            if not line:
                break
            time_match = re.search(r"time=(\d+):(\d+):(\d+\.?\d*)", line)
            if time_match and self._total_duration > 0:
                hours = float(time_match.group(1))
                minutes = float(time_match.group(2))
                seconds = float(time_match.group(3))
                current_time = hours * 3600 + minutes * 60 + seconds
                self._render_progress = min(100.0, (current_time / self._total_duration) * 100)
        self._render_process.wait()
        if self._render_process.returncode == 0:
            self._render_progress = 100.0
        self._is_rendering = False


class DesktopAdapter(PlatformAdapter):
    def __init__(self, base_path: Path | str | None = None):
        super().__init__()
        self._base_path = Path(base_path) if base_path else Path.cwd()
        self._storage: FileSystemAccess | None = None
        self._renderer: FFmpegRenderer | None = None
        self._hardware_encoder: HardwareEncoder | None = None
        self._os_name = platform.system().lower()

    def get_platform_name(self) -> str:
        return "desktop"

    def detect_capabilities(self) -> PlatformCapabilities:
        hw_encoder = HardwareEncoder()
        has_hw_encode = hw_encoder.has_nvenc() or hw_encoder.has_qsv() or hw_encoder.has_videotoolbox()
        max_res = self._detect_max_resolution()
        return PlatformCapabilities(
            can_hardware_encode=has_hw_encode,
            can_gpu_render=has_hw_encode,
            max_preview_fps=60,
            max_resolution=max_res,
            supports_touch=self._detect_touch_support(),
            supports_offline=True,
            storage_type="file",
            renderer_type="ffmpeg",
        )

    def get_storage(self) -> FileSystemAccess:
        if self._storage is None:
            self._storage = FileSystemAccess(self._base_path)
        return self._storage

    def get_renderer_config(self) -> dict[str, Any]:
        hw_encoder = HardwareEncoder()
        recommended = hw_encoder.get_recommended_encoder()
        encoder_opts = hw_encoder.get_encoder_options(recommended)
        return {
            "type": "ffmpeg",
            "encoder": recommended,
            "encoder_options": encoder_opts,
            "supports_hardware": hw_encoder.has_nvenc() or hw_encoder.has_qsv() or hw_encoder.has_videotoolbox(),
            "output_formats": ["mp4", "webm", "mov", "avi", "gif"],
            "audio_codecs": ["aac", "mp3", "opus", "vorbis"],
            "video_codecs": ["h264", "h265", "vp8", "vp9", "av1"],
        }

    def get_hardware_encoder(self) -> HardwareEncoder:
        if self._hardware_encoder is None:
            self._hardware_encoder = HardwareEncoder()
        return self._hardware_encoder

    def get_renderer(self) -> FFmpegRenderer:
        if self._renderer is None:
            self._renderer = FFmpegRenderer()
        return self._renderer

    def _detect_max_resolution(self) -> tuple[int, int]:
        if self._os_name == "windows":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                width = user32.GetSystemMetrics(0)
                height = user32.GetSystemMetrics(1)
                if width > 0 and height > 0:
                    return (width, height)
            except Exception:
                pass
        elif self._os_name == "darwin":
            try:
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                match = re.search(r"Resolution:\s*(\d+)\s*x\s*(\d+)", result.stdout)
                if match:
                    return (int(match.group(1)), int(match.group(2)))
            except Exception:
                pass
        elif self._os_name == "linux":
            try:
                result = subprocess.run(
                    ["xrandr"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                match = re.search(r"current\s*(\d+)\s*x\s*(\d+)", result.stdout)
                if match:
                    return (int(match.group(1)), int(match.group(2)))
            except Exception:
                pass
        return (1920, 1080)

    def _detect_touch_support(self) -> bool:
        if self._os_name == "windows":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                return bool(user32.GetSystemMetrics(94))
            except Exception:
                pass
        return False
