"""
PyAgent 桌面自动化模块 - 鼠标控制器
"""

import asyncio
from dataclasses import dataclass
from enum import Enum


class MouseButton(Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


@dataclass
class MousePosition:
    x: int
    y: int


class MouseController:
    """鼠标控制器"""

    def __init__(self):
        self._pyautogui_available = self._check_pyautogui()
        self._pynput_available = self._check_pynput()
        self._position: MousePosition = MousePosition(0, 0)

    def _check_pyautogui(self) -> bool:
        try:
            import pyautogui
            return True
        except ImportError:
            return False

    def _check_pynput(self) -> bool:
        try:
            from pynput.mouse import Controller
            return True
        except ImportError:
            return False

    def move_to(self, x: int, y: int, duration: float = 0.0) -> bool:
        try:
            if self._pyautogui_available:
                import pyautogui
                pyautogui.moveTo(x, y, duration=duration)
                self._position = MousePosition(x, y)
                return True
            return False
        except Exception:
            return False

    def click(
        self,
        x: int | None = None,
        y: int | None = None,
        button: MouseButton = MouseButton.LEFT,
        clicks: int = 1
    ) -> bool:
        try:
            if self._pyautogui_available:
                import pyautogui

                btn = pyautogui.LEFT if button == MouseButton.LEFT else (
                    pyautogui.RIGHT if button == MouseButton.RIGHT else pyautogui.MIDDLE
                )

                if x is not None and y is not None:
                    pyautogui.click(x, y, clicks=clicks, button=btn)
                else:
                    pyautogui.click(clicks=clicks, button=btn)

                return True
            return False
        except Exception:
            return False

    def double_click(self, x: int | None = None, y: int | None = None) -> bool:
        return self.click(x, y, clicks=2)

    def right_click(self, x: int | None = None, y: int | None = None) -> bool:
        return self.click(x, y, button=MouseButton.RIGHT)

    def scroll(self, direction: str, amount: int = 3) -> bool:
        try:
            if self._pyautogui_available:
                import pyautogui

                if direction == "up":
                    pyautogui.scroll(amount)
                elif direction == "down":
                    pyautogui.scroll(-amount)
                else:
                    return False

                return True
            return False
        except Exception:
            return False

    def drag_to(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: float = 0.5
    ) -> bool:
        try:
            if self._pyautogui_available:
                import pyautogui

                pyautogui.moveTo(start_x, start_y)
                pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration)

                self._position = MousePosition(end_x, end_y)
                return True
            return False
        except Exception:
            return False

    def get_position(self) -> MousePosition:
        try:
            if self._pyautogui_available:
                import pyautogui
                pos = pyautogui.position()
                return MousePosition(pos.x, pos.y)
            return self._position
        except Exception:
            return self._position

    async def move_smoothly(self, x: int, y: int, duration: float = 0.5) -> bool:
        steps = int(duration * 60)
        current = self.get_position()

        for i in range(steps + 1):
            progress = i / steps
            new_x = int(current.x + (x - current.x) * progress)
            new_y = int(current.y + (y - current.y) * progress)
            self.move_to(new_x, new_y)
            await asyncio.sleep(duration / steps)

        return True


mouse_controller = MouseController()
