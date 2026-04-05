import subprocess
import re
import shutil
from pathlib import Path
from typing import Optional
import time

from .base import BaseRenderer, RenderConfig, RenderJob


class FFmpegRenderer(BaseRenderer):
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        super().__init__()
        self.ffmpeg_path = ffmpeg_path
        self._process: Optional[subprocess.Popen] = None
        self._duration: float = 0.0

    def render(self, project, config: RenderConfig) -> RenderJob:
        job = self._create_job(project.project_id if project else "export", config)
        self.current_job = job
        job.status = "running"
        job.started_at = time.time()
        self._cancelled = False
        try:
            Path(config.output_path).parent.mkdir(parents=True, exist_ok=True)
            cmd = self._build_command(config)
            self._process = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True
            )
            self._duration = 10.0
            while self._process.poll() is None:
                if self._cancelled:
                    self._process.terminate()
                    job.status = "cancelled"
                    break
                line = self._process.stderr.readline()
                progress = self._parse_progress(line)
                if progress > 0:
                    self._update_progress(progress)
            if not self._cancelled and self._process.returncode == 0:
                job.output_path = config.output_path
                job.status = "completed"
            elif not self._cancelled:
                job.status = "failed"
                job.error = f"FFmpeg exited with code {self._process.returncode}"
            job.completed_at = time.time()
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = time.time()
        finally:
            self._process = None
        return job

    def get_progress(self) -> float:
        return self.current_job.progress if self.current_job else 0.0

    def cancel(self) -> bool:
        self._cancelled = True
        if self._process:
            self._process.terminate()
        return True

    def _build_command(self, config: RenderConfig) -> list[str]:
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s={config.resolution[0]}x{config.resolution[1]}:d=10",
            "-c:v", self._get_encoder(config),
        ]
        cmd.extend(self._get_quality_params(config))
        cmd.extend([
            "-r", str(config.fps),
            str(config.output_path)
        ])
        return cmd

    def _get_encoder(self, config: RenderConfig) -> str:
        if not config.hardware_accel:
            return "libx264"
        encoders = self._detect_hardware_encoders()
        if encoders.get("nvenc"):
            return "h264_nvenc"
        elif encoders.get("qsv"):
            return "h264_qsv"
        elif encoders.get("videotoolbox"):
            return "h264_videotoolbox"
        return "libx264"

    def _get_quality_params(self, config: RenderConfig) -> list[str]:
        quality_map = {
            "low": ["-b:v", "1M", "-preset", "fast"],
            "medium": ["-b:v", "2.5M", "-preset", "medium"],
            "high": ["-b:v", "5M", "-preset", "slow"],
            "ultra": ["-b:v", "10M", "-preset", "veryslow"],
        }
        return quality_map.get(config.quality, quality_map["high"])

    def _parse_progress(self, line: str) -> float:
        match = re.search(r"time=(\d+):(\d+):(\d+\.?\d*)", line)
        if match:
            h, m, s = float(match.group(1)), float(match.group(2)), float(match.group(3))
            current = h * 3600 + m * 60 + s
            if self._duration > 0:
                return min(current / self._duration, 1.0)
        return 0.0

    def _detect_hardware_encoders(self) -> dict:
        result = {"nvenc": False, "qsv": False, "videotoolbox": False}
        try:
            proc = subprocess.run(
                [self.ffmpeg_path, "-encoders"],
                capture_output=True,
                text=True
            )
            output = proc.stdout
            result["nvenc"] = "h264_nvenc" in output
            result["qsv"] = "h264_qsv" in output
            result["videotoolbox"] = "h264_videotoolbox" in output
        except Exception:
            pass
        return result

    @staticmethod
    def is_available() -> bool:
        return shutil.which("ffmpeg") is not None

    @staticmethod
    def get_version() -> str:
        try:
            proc = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True
            )
            match = re.search(r"ffmpeg version (\S+)", proc.stdout)
            return match.group(1) if match else "unknown"
        except Exception:
            return "not found"
