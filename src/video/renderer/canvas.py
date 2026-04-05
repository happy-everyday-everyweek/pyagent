import numpy as np
from typing import Optional
from pathlib import Path
import time

from .base import BaseRenderer, RenderConfig, RenderJob


class CanvasRenderer(BaseRenderer):
    def __init__(self, width: int = 1920, height: int = 1080):
        super().__init__()
        self.width = width
        self.height = height
        self._frame_buffer: Optional[np.ndarray] = None

    def render(self, project, config: RenderConfig) -> RenderJob:
        job = self._create_job(project.project_id if project else "preview", config)
        self.current_job = job
        job.status = "running"
        job.started_at = time.time()
        try:
            self.width, self.height = config.resolution
            self._frame_buffer = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            total_frames = int(config.fps * 10)
            for i in range(total_frames):
                if self._cancelled:
                    job.status = "cancelled"
                    break
                frame = self._render_frame(i / config.fps)
                self._update_progress((i + 1) / total_frames)
            if not self._cancelled:
                job.output_path = config.output_path
                job.status = "completed"
            job.completed_at = time.time()
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = time.time()
        return job

    def render_frame(self, project, time_seconds: float) -> np.ndarray:
        return self._render_frame(time_seconds)

    def render_preview(self, project, time_seconds: float, size: Optional[tuple[int, int]] = None) -> np.ndarray:
        frame = self._render_frame(time_seconds)
        if size:
            frame = self._resize_frame(frame, size)
        return frame

    def get_progress(self) -> float:
        return self.current_job.progress if self.current_job else 0.0

    def cancel(self) -> bool:
        self._cancelled = True
        return True

    def _render_frame(self, time_seconds: float) -> np.ndarray:
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        r = int(128 + 127 * np.sin(time_seconds))
        g = int(128 + 127 * np.sin(time_seconds + 2.094))
        b = int(128 + 127 * np.sin(time_seconds + 4.188))
        frame[:, :] = [r, g, b]
        return frame

    def _resize_frame(self, frame: np.ndarray, size: tuple[int, int]) -> np.ndarray:
        h, w = frame.shape[:2]
        new_w, new_h = size
        y_indices = (np.arange(new_h) * h / new_h).astype(int)
        x_indices = (np.arange(new_w) * w / new_w).astype(int)
        return frame[y_indices][:, x_indices]

    def _composite_elements(self, elements: list, time_seconds: float) -> np.ndarray:
        frame = np.zeros((self.height, self.width, 4), dtype=np.float32)
        for element in elements:
            element_frame = self._render_element(element, time_seconds)
            if element_frame is not None:
                opacity = getattr(element, "opacity", 1.0)
                frame = frame * (1 - opacity) + element_frame * opacity
        return frame[:, :, :3].astype(np.uint8)

    def _render_element(self, element, time_seconds: float) -> Optional[np.ndarray]:
        return None

    def _apply_transition(self, frame1: np.ndarray, frame2: np.ndarray, transition, progress: float) -> np.ndarray:
        if transition is None:
            return frame2
        from ..transitions import get_transition
        trans = get_transition(transition.type.value, transition.duration)
        return trans.apply(frame1, frame2, progress)
