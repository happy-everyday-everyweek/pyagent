"""
PyAgent 移动端模块 - 屏幕操作工具

提供移动设备的屏幕操作功能，包括截图、点击、滑动和文本输入。
v0.8.0: 新增移动端支持
"""

import base64
import logging
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.tools.base import ToolContext, ToolResult, ToolState, UnifiedTool


@dataclass
class ScreenInfo:
    """屏幕信息"""
    width: int = 1080
    height: int = 1920
    density: int = 480
    orientation: str = "portrait"

    def to_dict(self) -> dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "density": self.density,
            "orientation": self.orientation,
        }


@dataclass
class GestureResult:
    """手势操作结果"""
    success: bool
    action: str
    coordinates: tuple[int, int] | tuple[int, int, int, int]
    duration_ms: int = 0
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "action": self.action,
            "coordinates": self.coordinates,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


class ScreenTools(UnifiedTool):
    """屏幕操作工具

    提供移动设备的屏幕操作功能，包括截图、点击、滑动和文本输入。
    支持Android设备通过ADB或本地shell命令进行操作。
    """

    name = "screen_tools"
    description = "屏幕操作工具，提供截图、点击、滑动和文本输入功能"

    def __init__(self, device_id: str = "", adb_path: str = "adb"):
        super().__init__(device_id)
        self._adb_path = adb_path
        self._screen_info: ScreenInfo | None = None
        self._screenshot_dir = Path(tempfile.gettempdir()) / "pyagent_screenshots"
        self._logger = logging.getLogger(__name__)

    async def activate(self, context: ToolContext) -> bool:
        """激活工具"""
        try:
            self._screenshot_dir.mkdir(parents=True, exist_ok=True)

            self._screen_info = await self._detect_screen_info()

            if not await self._check_adb_available():
                self._logger.warning("ADB not available, using fallback methods")

            self._state = ToolState.ACTIVE
            return True

        except Exception as e:
            self._logger.error(f"Failed to activate screen tools: {e}")
            self._state = ToolState.ERROR
            return False

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        """执行工具"""
        action = kwargs.get("action", "")

        action_map = {
            "capture": self.capture_screen,
            "tap": lambda: self.tap(kwargs.get("x", 0), kwargs.get("y", 0)),
            "swipe": lambda: self.swipe(
                kwargs.get("x1", 0),
                kwargs.get("y1", 0),
                kwargs.get("x2", 0),
                kwargs.get("y2", 0),
                kwargs.get("duration", 300)
            ),
            "input_text": lambda: self.input_text(kwargs.get("text", "")),
            "get_info": self.get_screen_info,
        }

        if action not in action_map:
            return ToolResult(
                success=False,
                error=f"Unknown action: {action}"
            )

        return await action_map[action]()

    async def dormant(self, context: ToolContext) -> bool:
        """休眠工具"""
        self._screen_info = None
        self._state = ToolState.DORMANT
        return True

    async def _check_adb_available(self) -> bool:
        """检查ADB是否可用"""
        try:
            result = subprocess.run(
                [self._adb_path, "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    async def _detect_screen_info(self) -> ScreenInfo:
        """检测屏幕信息"""
        info = ScreenInfo()

        try:
            result = subprocess.run(
                [self._adb_path, "shell", "wm", "size"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                if "Physical size:" in output:
                    size_str = output.split("Physical size:")[1].strip()
                    width, height = map(int, size_str.split("x"))
                    info.width = width
                    info.height = height

        except Exception:
            pass

        try:
            result = subprocess.run(
                [self._adb_path, "shell", "wm", "density"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                if "Physical density:" in output:
                    density_str = output.split("Physical density:")[1].strip()
                    info.density = int(density_str)

        except Exception:
            pass

        if info.width > info.height:
            info.orientation = "landscape"
        else:
            info.orientation = "portrait"

        return info

    async def capture_screen(self) -> ToolResult:
        """截取屏幕

        Returns:
            ToolResult: 包含截图的Base64编码
        """
        if self._state != ToolState.ACTIVE:
            return ToolResult(
                success=False,
                error="Tool not activated"
            )

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            local_path = self._screenshot_dir / filename
            device_path = f"/sdcard/{filename}"

            result = subprocess.run(
                [self._adb_path, "shell", "screencap", "-p", device_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Failed to capture screen: {result.stderr}"
                )

            result = subprocess.run(
                [self._adb_path, "pull", device_path, str(local_path)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Failed to pull screenshot: {result.stderr}"
                )

            subprocess.run(
                [self._adb_path, "shell", "rm", device_path],
                capture_output=True,
                timeout=10
            )

            with open(local_path, "rb") as f:
                image_data = f.read()
                base64_data = base64.b64encode(image_data).decode("utf-8")

            return ToolResult(
                success=True,
                output=f"Screenshot saved to {local_path}",
                data={
                    "image_base64": base64_data,
                    "width": self._screen_info.width if self._screen_info else 0,
                    "height": self._screen_info.height if self._screen_info else 0,
                    "path": str(local_path),
                }
            )

        except Exception as e:
            self._logger.error(f"Failed to capture screen: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to capture screen: {e!s}"
            )

    async def tap(self, x: int, y: int) -> ToolResult:
        """点击屏幕指定位置

        Args:
            x: X坐标
            y: Y坐标

        Returns:
            ToolResult: 操作结果
        """
        if self._state != ToolState.ACTIVE:
            return ToolResult(
                success=False,
                error="Tool not activated"
            )

        try:
            result = subprocess.run(
                [self._adb_path, "shell", "input", "tap", str(x), str(y)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Failed to tap: {result.stderr}"
                )

            return ToolResult(
                success=True,
                output=f"Tapped at ({x}, {y})",
                data=GestureResult(
                    success=True,
                    action="tap",
                    coordinates=(x, y)
                ).to_dict()
            )

        except Exception as e:
            self._logger.error(f"Failed to tap: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to tap: {e!s}"
            )

    async def swipe(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration: int = 300
    ) -> ToolResult:
        """滑动屏幕

        Args:
            x1: 起始X坐标
            y1: 起始Y坐标
            x2: 结束X坐标
            y2: 结束Y坐标
            duration: 滑动持续时间（毫秒）

        Returns:
            ToolResult: 操作结果
        """
        if self._state != ToolState.ACTIVE:
            return ToolResult(
                success=False,
                error="Tool not activated"
            )

        try:
            result = subprocess.run(
                [
                    self._adb_path, "shell", "input", "swipe",
                    str(x1), str(y1), str(x2), str(y2), str(duration)
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Failed to swipe: {result.stderr}"
                )

            return ToolResult(
                success=True,
                output=f"Swiped from ({x1}, {y1}) to ({x2}, {y2})",
                data=GestureResult(
                    success=True,
                    action="swipe",
                    coordinates=(x1, y1, x2, y2),
                    duration_ms=duration
                ).to_dict()
            )

        except Exception as e:
            self._logger.error(f"Failed to swipe: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to swipe: {e!s}"
            )

    async def input_text(self, text: str) -> ToolResult:
        """输入文本

        Args:
            text: 要输入的文本

        Returns:
            ToolResult: 操作结果
        """
        if self._state != ToolState.ACTIVE:
            return ToolResult(
                success=False,
                error="Tool not activated"
            )

        try:
            escaped_text = text.replace(" ", "%s").replace("'", "\\'")

            result = subprocess.run(
                [self._adb_path, "shell", "input", "text", escaped_text],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Failed to input text: {result.stderr}"
                )

            return ToolResult(
                success=True,
                output=f"Input text: {text}",
                data={
                    "text": text,
                    "length": len(text),
                }
            )

        except Exception as e:
            self._logger.error(f"Failed to input text: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to input text: {e!s}"
            )

    async def get_screen_info(self) -> ToolResult:
        """获取屏幕信息

        Returns:
            ToolResult: 包含屏幕信息
        """
        if self._screen_info is None:
            self._screen_info = await self._detect_screen_info()

        return ToolResult(
            success=True,
            output="Screen info retrieved",
            data=self._screen_info.to_dict()
        )

    async def press_key(self, keycode: str) -> ToolResult:
        """按下按键

        Args:
            keycode: 按键代码（如 KEYCODE_HOME, KEYCODE_BACK）

        Returns:
            ToolResult: 操作结果
        """
        if self._state != ToolState.ACTIVE:
            return ToolResult(
                success=False,
                error="Tool not activated"
            )

        try:
            result = subprocess.run(
                [self._adb_path, "shell", "input", "keyevent", keycode],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Failed to press key: {result.stderr}"
                )

            return ToolResult(
                success=True,
                output=f"Pressed key: {keycode}",
                data={"keycode": keycode}
            )

        except Exception as e:
            self._logger.error(f"Failed to press key: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to press key: {e!s}"
            )

    async def long_press(self, x: int, y: int, duration: int = 1000) -> ToolResult:
        """长按屏幕指定位置

        Args:
            x: X坐标
            y: Y坐标
            duration: 长按持续时间（毫秒）

        Returns:
            ToolResult: 操作结果
        """
        if self._state != ToolState.ACTIVE:
            return ToolResult(
                success=False,
                error="Tool not activated"
            )

        try:
            result = subprocess.run(
                [
                    self._adb_path, "shell", "input", "swipe",
                    str(x), str(y), str(x), str(y), str(duration)
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Failed to long press: {result.stderr}"
                )

            return ToolResult(
                success=True,
                output=f"Long pressed at ({x}, {y}) for {duration}ms",
                data=GestureResult(
                    success=True,
                    action="long_press",
                    coordinates=(x, y),
                    duration_ms=duration
                ).to_dict()
            )

        except Exception as e:
            self._logger.error(f"Failed to long press: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to long press: {e!s}"
            )

    def cleanup_screenshots(self, max_age_hours: int = 24) -> int:
        """清理旧的截图文件

        Args:
            max_age_hours: 最大保留时间（小时）

        Returns:
            int: 删除的文件数量
        """
        if not self._screenshot_dir.exists():
            return 0

        deleted = 0
        now = datetime.now()

        for file in self._screenshot_dir.glob("screenshot_*.png"):
            try:
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                age_hours = (now - mtime).total_seconds() / 3600

                if age_hours > max_age_hours:
                    file.unlink()
                    deleted += 1

            except Exception:
                pass

        return deleted
