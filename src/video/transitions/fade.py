import numpy as np

from .base import Transition


class FadeTransition(Transition):
    def __init__(self, duration: float = 0.5):
        super().__init__(duration)

    def apply(self, frame1: np.ndarray, frame2: np.ndarray, progress: float) -> np.ndarray:
        self.validate_frames(frame1, frame2)
        progress = self.clamp_progress(progress)
        alpha = progress
        result = frame1 * (1 - alpha) + frame2 * alpha
        return result.astype(frame1.dtype)

    def get_type(self) -> str:
        return "fade"


class DissolveTransition(Transition):
    def __init__(self, duration: float = 0.5, grain_intensity: float = 0.1):
        super().__init__(duration)
        self.grain_intensity = grain_intensity

    def apply(self, frame1: np.ndarray, frame2: np.ndarray, progress: float) -> np.ndarray:
        self.validate_frames(frame1, frame2)
        progress = self.clamp_progress(progress)
        alpha = self._ease_in_out(progress)
        noise = np.random.uniform(
            -self.grain_intensity,
            self.grain_intensity,
            frame1.shape
        ).astype(np.float32)
        frame1_float = frame1.astype(np.float32) / 255.0
        frame2_float = frame2.astype(np.float32) / 255.0
        dissolved = frame1_float * (1 - alpha) + frame2_float * alpha + noise * (1 - abs(2 * progress - 1))
        dissolved = np.clip(dissolved * 255.0, 0, 255).astype(frame1.dtype)
        return dissolved

    def get_type(self) -> str:
        return "dissolve"

    def _ease_in_out(self, t: float) -> float:
        return t * t * (3 - 2 * t)
