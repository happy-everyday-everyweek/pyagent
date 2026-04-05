from typing import Literal

import numpy as np

from .base import Transition


class WipeTransition(Transition):
    def __init__(
        self,
        duration: float = 0.5,
        direction: Literal["left", "right", "up", "down"] = "right"
    ):
        super().__init__(duration)
        self.direction = direction

    def apply(self, frame1: np.ndarray, frame2: np.ndarray, progress: float) -> np.ndarray:
        self.validate_frames(frame1, frame2)
        progress = self.clamp_progress(progress)
        height, width = frame1.shape[:2]
        result = frame1.copy()
        
        if self.direction == "right":
            boundary = int(width * progress)
            result[:, :boundary] = frame2[:, :boundary]
        elif self.direction == "left":
            boundary = int(width * (1 - progress))
            result[:, boundary:] = frame2[:, boundary:]
        elif self.direction == "down":
            boundary = int(height * progress)
            result[:boundary, :] = frame2[:boundary, :]
        elif self.direction == "up":
            boundary = int(height * (1 - progress))
            result[boundary:, :] = frame2[boundary:, :]
        
        return result

    def get_type(self) -> str:
        return f"wipe-{self.direction}"
