"""
PyAgent 桌面自动化模块 - 键盘控制器
"""

import asyncio
from dataclasses import dataclass
from typing import Any


@dataclass
class HotKey:
    keys: list[str]
    description: str = ""


class KeyboardController:
    """键盘控制器"""

    def __init__(self):
        self._pyautogui_available = self._check_pyautogui()
        self._pynput_available = self._check_pynput()
        self._common_hotkeys: dict[str, HotKey] = {
            "copy": HotKey(["ctrl", "c"], "复制"),
            "paste": HotKey(["ctrl", "v"], "粘贴"),
            "cut": HotKey(["ctrl", "x"], "剪切"),
            "undo": HotKey(["ctrl", "z"], "撤销"),
            "redo": HotKey(["ctrl", "y"], "重做"),
            "select_all": HotKey(["ctrl", "a"], "全选"),
            "save": HotKey(["ctrl", "s"], "保存"),
            "find": HotKey(["ctrl", "f"], "查找"),
            "new": HotKey(["ctrl", "n"], "新建"),
            "alt_tab": HotKey(["alt", "tab"], "切换窗口"),
            "ctrl_tab": HotKey(["ctrl", "tab"], "切换标签页"),
        }

    def _check_pyautogui(self) -> bool:
        try:
            import pyautogui
            return True
        except ImportError:
            return False

    def _check_pynput(self) -> bool:
        try:
            from pynput.keyboard import Controller
            return True
        except ImportError:
            return False

    def type_text(self, text: str, interval: float = 0.0) -> bool:
        try:
            if self._pyautogui_available:
                import pyautogui
                pyautogui.write(text, interval=interval)
                return True
            return False
        except Exception:
            return False

    async def type_text_human_like(self, text: str, base_interval: float = 0.05) -> bool:
        import random

        for char in text:
            if not self.type_text(char):
                return False

            jitter = random.uniform(-0.02, 0.02)
            await asyncio.sleep(base_interval + jitter)

        return True

    def press_key(self, key: str) -> bool:
        try:
            if self._pyautogui_available:
                import pyautogui
                pyautogui.press(key)
                return True
            return False
        except Exception:
            return False

    def release_key(self, key: str) -> bool:
        try:
            if self._pyautogui_available:
                import pyautogui
                pyautogui.release(key)
                return True
            return False
        except Exception:
            return False

    def hotkey(self, *keys: str) -> bool:
        try:
            if self._pyautogui_available:
                import pyautogui
                pyautogui.hotkey(*keys)
                return True
            return False
        except Exception:
            return False

    def key_down(self, key: str) -> bool:
        return self.press_key(key)

    def key_up(self, key: str) -> bool:
        return self.release_key(key)

    def execute_hotkey(self, hotkey_name: str) -> bool:
        if hotkey_name in self._common_hotkeys:
            hk = self._common_hotkeys[hotkey_name]
            return self.hotkey(*hk.keys)
        return False

    def get_available_hotkeys(self) -> dict[str, str]:
        return {name: hk.description for name, hk in self._common_hotkeys.items()}

    def add_hotkey(self, name: str, keys: list[str], description: str = "") -> None:
        self._common_hotkeys[name] = HotKey(keys, description)

    async def type_with_speed(self, text: str, wpm: int = 60) -> bool:
        chars_per_second = wpm * 5 / 60
        interval = 1.0 / chars_per_second

        return await self.type_text_human_like(text, interval)


keyboard_controller = KeyboardController()
