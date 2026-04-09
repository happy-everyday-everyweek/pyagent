"""
PyAgent 桌面自动化模块

提供AI驱动的桌面键鼠操作功能。
"""

from .automation import DesktopAutomation, DesktopSession
from .keyboard import KeyboardController
from .mouse import MouseController
from .screen import ScreenCapture

__all__ = [
    "DesktopAutomation",
    "DesktopSession",
    "KeyboardController",
    "MouseController",
    "ScreenCapture",
]
