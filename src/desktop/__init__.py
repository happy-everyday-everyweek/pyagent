"""
PyAgent 桌面自动化模块

提供AI驱动的桌面键鼠操作功能。
"""

from .screen import ScreenCapture
from .mouse import MouseController
from .keyboard import KeyboardController
from .automation import DesktopAutomation, DesktopSession

__all__ = [
    "ScreenCapture",
    "MouseController",
    "KeyboardController",
    "DesktopAutomation",
    "DesktopSession",
]
