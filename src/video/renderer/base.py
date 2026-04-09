import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class RenderConfig:
    output_path: str
    format: str = "mp4"
    resolution: tuple[int, int] = (1920, 1080)
    fps: int = 30
    video_bitrate: str = "5M"
    audio_bitrate: str = "256k"
    quality: str = "high"
    hardware_accel: bool = True
    metadata: dict = field(default_factory=dict)


@dataclass
class RenderJob:
    id: str
    project_id: str
    config: RenderConfig
    status: str = "pending"
    progress: float = 0.0
    output_path: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "config": {
                "output_path": self.config.output_path,
                "format": self.config.format,
                "resolution": self.config.resolution,
                "fps": self.config.fps,
                "video_bitrate": self.config.video_bitrate,
                "audio_bitrate": self.config.audio_bitrate,
                "quality": self.config.quality,
                "hardware_accel": self.config.hardware_accel,
                "metadata": self.config.metadata,
            },
            "status": self.status,
            "progress": self.progress,
            "output_path": self.output_path,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class BaseRenderer(ABC):
    def __init__(self):
        self.current_job: RenderJob | None = None
        self._progress_callback: Callable | None = None
        self._cancelled: bool = False

    @abstractmethod
    def render(self, project, config: RenderConfig) -> RenderJob:
        pass

    @abstractmethod
    def get_progress(self) -> float:
        pass

    @abstractmethod
    def cancel(self) -> bool:
        pass

    def set_progress_callback(self, callback: Callable):
        self._progress_callback = callback

    def _update_progress(self, progress: float):
        if self.current_job:
            self.current_job.progress = progress
        if self._progress_callback:
            self._progress_callback(progress)

    def _create_job(self, project_id: str, config: RenderConfig) -> RenderJob:
        return RenderJob(
            id=str(uuid.uuid4()),
            project_id=project_id,
            config=config,
        )
