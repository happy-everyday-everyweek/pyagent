from typing import Literal

import numpy as np

from .base import Transition


class SlideTransition(Transition):
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
        result = np.zeros_like(frame1)

        if self.direction == "right":
            offset = int(width * progress)
            if offset > 0:
                result[:, :width - offset] = frame1[:, offset:]
            if offset < width:
                result[:, width - offset:] = frame2[:, :offset]
        elif self.direction == "left":
            offset = int(width * progress)
            if offset > 0:
                result[:, offset:] = frame1[:, :width - offset]
            if offset < width:
                result[:, :offset] = frame2[:, width - offset:]
        elif self.direction == "down":
            offset = int(height * progress)
            if offset > 0:
                result[:height - offset, :] = frame1[offset:, :]
            if offset < height:
                result[height - offset:, :] = frame2[:offset, :]
        elif self.direction == "up":
            offset = int(height * progress)
            if offset > 0:
                result[offset:, :] = frame1[:height - offset, :]
            if offset < height:
                result[:offset, :] = frame2[height - offset:, :]

        return result

    def get_type(self) -> str:
        return f"slide-{self.direction}"
