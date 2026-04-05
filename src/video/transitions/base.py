from abc import ABC, abstractmethod

import numpy as np


class Transition(ABC):
    def __init__(self, duration: float = 0.5):
        self.duration = duration

    @abstractmethod
    def apply(self, frame1: np.ndarray, frame2: np.ndarray, progress: float) -> np.ndarray:
        pass

    @abstractmethod
    def get_type(self) -> str:
        pass

    def validate_frames(self, frame1: np.ndarray, frame2: np.ndarray) -> None:
        if frame1 is None or frame2 is None:
            raise ValueError("Frames cannot be None")
        if frame1.shape != frame2.shape:
            raise ValueError(f"Frame shapes must match: {frame1.shape} vs {frame2.shape}")

    def clamp_progress(self, progress: float) -> float:
        return max(0.0, min(1.0, progress))
