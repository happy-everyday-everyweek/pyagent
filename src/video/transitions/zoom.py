import numpy as np

from .base import Transition


class ZoomInTransition(Transition):
    def __init__(self, duration: float = 0.5, max_scale: float = 2.0):
        super().__init__(duration)
        self.max_scale = max_scale

    def apply(self, frame1: np.ndarray, frame2: np.ndarray, progress: float) -> np.ndarray:
        self.validate_frames(frame1, frame2)
        progress = self.clamp_progress(progress)
        height, width = frame1.shape[:2]
        
        scale1 = 1.0 + progress * (self.max_scale - 1.0)
        scale2 = 1.0 / self.max_scale + progress * (1.0 - 1.0 / self.max_scale)
        
        frame1_scaled = self._scale_frame(frame1, scale1, width, height)
        frame2_scaled = self._scale_frame(frame2, scale2, width, height)
        
        alpha = self._ease_in_out(progress)
        result = (frame1_scaled * (1 - alpha) + frame2_scaled * alpha).astype(frame1.dtype)
        
        return result

    def get_type(self) -> str:
        return "zoom-in"

    def _scale_frame(self, frame: np.ndarray, scale: float, width: int, height: int) -> np.ndarray:
        new_width = max(1, int(width * scale))
        new_height = max(1, int(height * scale))
        
        indices_y = np.linspace(0, height - 1, new_height).astype(np.float32)
        indices_x = np.linspace(0, width - 1, new_width).astype(np.float32)
        
        y_indices = np.clip(indices_y.astype(int), 0, height - 1)
        x_indices = np.clip(indices_x.astype(int), 0, width - 1)
        
        scaled = frame[y_indices][:, x_indices]
        
        result = np.zeros((height, width, frame.shape[2]) if len(frame.shape) == 3 else (height, width), dtype=frame.dtype)
        
        if scale >= 1.0:
            start_y = (new_height - height) // 2
            start_x = (new_width - width) // 2
            end_y = start_y + height
            end_x = start_x + width
            result[:, :] = scaled[start_y:end_y, start_x:end_x]
        else:
            offset_y = (height - new_height) // 2
            offset_x = (width - new_width) // 2
            result[offset_y:offset_y + new_height, offset_x:offset_x + new_width] = scaled
        
        return result

    def _ease_in_out(self, t: float) -> float:
        return t * t * (3 - 2 * t)


class ZoomOutTransition(Transition):
    def __init__(self, duration: float = 0.5, max_scale: float = 2.0):
        super().__init__(duration)
        self.max_scale = max_scale

    def apply(self, frame1: np.ndarray, frame2: np.ndarray, progress: float) -> np.ndarray:
        self.validate_frames(frame1, frame2)
        progress = self.clamp_progress(progress)
        height, width = frame1.shape[:2]
        
        scale1 = self.max_scale - progress * (self.max_scale - 1.0)
        scale2 = 1.0 / self.max_scale * (1 - progress) + progress
        
        frame1_scaled = self._scale_frame(frame1, scale1, width, height)
        frame2_scaled = self._scale_frame(frame2, scale2, width, height)
        
        alpha = self._ease_in_out(progress)
        result = (frame1_scaled * (1 - alpha) + frame2_scaled * alpha).astype(frame1.dtype)
        
        return result

    def get_type(self) -> str:
        return "zoom-out"

    def _scale_frame(self, frame: np.ndarray, scale: float, width: int, height: int) -> np.ndarray:
        new_width = max(1, int(width * scale))
        new_height = max(1, int(height * scale))
        
        indices_y = np.linspace(0, height - 1, new_height).astype(np.float32)
        indices_x = np.linspace(0, width - 1, new_width).astype(np.float32)
        
        y_indices = np.clip(indices_y.astype(int), 0, height - 1)
        x_indices = np.clip(indices_x.astype(int), 0, width - 1)
        
        scaled = frame[y_indices][:, x_indices]
        
        result = np.zeros((height, width, frame.shape[2]) if len(frame.shape) == 3 else (height, width), dtype=frame.dtype)
        
        if scale >= 1.0:
            start_y = (new_height - height) // 2
            start_x = (new_width - width) // 2
            end_y = start_y + height
            end_x = start_x + width
            result[:, :] = scaled[start_y:end_y, start_x:end_x]
        else:
            offset_y = (height - new_height) // 2
            offset_x = (width - new_width) // 2
            result[offset_y:offset_y + new_height, offset_x:offset_x + new_width] = scaled
        
        return result

    def _ease_in_out(self, t: float) -> float:
        return t * t * (3 - 2 * t)
