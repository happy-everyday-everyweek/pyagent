"""
PyAgent 移动端模块 - 手势执行器
移植自 OpenKiwi GuiActionExecutor
整合 ScreenTools 提供低延迟手势执行
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.mobile.screen_tools import ScreenTools
from src.tools.base import ToolContext, ToolResult


class GestureType(Enum):
    """手势类型"""
    TAP = "tap"
    DOUBLE_TAP = "double_tap"
    LONG_PRESS = "long_press"
    SWIPE = "swipe"
    PINCH = "pinch"
    ZOOM = "zoom"
    SCROLL = "scroll"


@dataclass
class GestureSpec:
    """手势规格"""
    gesture_type: GestureType
    x: int = 0
    y: int = 0
    x2: int = 0
    y2: int = 0
    duration_ms: int = 100
    delay_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "gesture_type": self.gesture_type.value,
            "x": self.x,
            "y": self.y,
            "x2": self.x2,
            "y2": self.y2,
            "duration_ms": self.duration_ms,
            "delay_ms": self.delay_ms,
        }


@dataclass
class GestureResult:
    """手势执行结果"""
    success: bool
    spec: GestureSpec
    duration_ms: int = 0
    error: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "spec": self.spec.to_dict(),
            "duration_ms": self.duration_ms,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class NodeCache:
    """节点缓存

    带TTL的界面节点缓存，避免重复遍历节点树。
    """

    def __init__(self, ttl_ms: int = 500):
        self._ttl_ms = ttl_ms
        self._cache: dict[str, Any] = {}
        self._timestamp: float = 0
        self._logger = logging.getLogger(__name__)

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        if self._is_expired():
            self._cache.clear()
            return None

        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        self._cache[key] = value
        self._timestamp = time.time() * 1000

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._timestamp = 0

    def _is_expired(self) -> bool:
        """检查缓存是否过期"""
        if not self._timestamp:
            return True

        elapsed = time.time() * 1000 - self._timestamp
        return elapsed > self._ttl_ms


class GestureExecutor:
    """手势执行器

    执行低延迟的屏幕手势操作。
    移植自 OpenKiwi 的 GuiActionExecutor。
    整合 ScreenTools 提供统一的手势执行接口。
    """

    def __init__(self, adb_path: str = "adb", device_id: str = ""):
        self._adb_path = adb_path
        self._device_id = device_id
        self._screen_tools: ScreenTools | None = None
        self._tool_context: ToolContext | None = None
        self._node_cache = NodeCache(ttl_ms=500)
        self._callbacks: list[Callable[[GestureResult], None]] = []
        self._last_gesture_time: float = 0
        self._min_interval_ms: int = 50
        self._initialized = False
        self._logger = logging.getLogger(__name__)

    async def initialize(self) -> bool:
        """初始化执行器"""
        if self._initialized:
            return True

        try:
            self._screen_tools = ScreenTools(device_id=self._device_id, adb_path=self._adb_path)
            self._tool_context = ToolContext(device_id=self._device_id)

            result = await self._screen_tools.activate(self._tool_context)
            if result:
                self._initialized = True
                self._logger.info("GestureExecutor initialized successfully")
                return True
            self._logger.error("Failed to initialize GestureExecutor")
            return False
        except Exception as e:
            self._logger.error(f"Error initializing GestureExecutor: {e}")
            return False

    async def cleanup(self) -> None:
        """清理资源"""
        if self._screen_tools and self._tool_context:
            try:
                await self._screen_tools.dormant(self._tool_context)
            except Exception as e:
                self._logger.error(f"Error cleaning up GestureExecutor: {e}")

        self._initialized = False
        self._node_cache.clear()

    def add_callback(self, callback: Callable[[GestureResult], None]) -> None:
        """添加回调函数"""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[GestureResult], None]) -> None:
        """移除回调函数"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def execute(self, spec: GestureSpec) -> GestureResult:
        """执行手势

        Args:
            spec: 手势规格

        Returns:
            GestureResult: 执行结果
        """
        if not self._initialized:
            if not await self.initialize():
                return GestureResult(
                    success=False,
                    spec=spec,
                    error="GestureExecutor not initialized",
                )

        await self._wait_for_interval()

        start_time = time.time() * 1000

        try:
            success = await self._execute_gesture(spec)

            duration_ms = int(time.time() * 1000 - start_time)

            result = GestureResult(
                success=success,
                spec=spec,
                duration_ms=duration_ms,
            )

        except Exception as e:
            self._logger.error(f"Failed to execute gesture: {e}")
            result = GestureResult(
                success=False,
                spec=spec,
                error=str(e),
            )

        self._last_gesture_time = time.time() * 1000
        self._node_cache.clear()

        for callback in self._callbacks:
            try:
                callback(result)
            except Exception as e:
                self._logger.error(f"Callback error: {e}")

        return result

    async def _wait_for_interval(self) -> None:
        """等待最小间隔"""
        elapsed = time.time() * 1000 - self._last_gesture_time
        if elapsed < self._min_interval_ms:
            await asyncio.sleep((self._min_interval_ms - elapsed) / 1000)

    async def _execute_gesture(self, spec: GestureSpec) -> bool:
        """执行具体手势"""
        if not self._screen_tools:
            return False

        if spec.gesture_type == GestureType.TAP:
            result = await self._screen_tools.tap(spec.x, spec.y)
            return result.success

        if spec.gesture_type == GestureType.DOUBLE_TAP:
            result1 = await self._screen_tools.tap(spec.x, spec.y)
            await asyncio.sleep(0.1)
            result2 = await self._screen_tools.tap(spec.x, spec.y)
            return result1.success and result2.success

        if spec.gesture_type == GestureType.LONG_PRESS:
            result = await self._screen_tools.long_press(spec.x, spec.y, spec.duration_ms)
            return result.success

        if spec.gesture_type == GestureType.SWIPE:
            result = await self._screen_tools.swipe(
                spec.x, spec.y, spec.x2, spec.y2, spec.duration_ms
            )
            return result.success

        if spec.gesture_type == GestureType.PINCH:
            return await self._pinch(spec.x, spec.y, spec.x2)

        if spec.gesture_type == GestureType.ZOOM:
            return await self._zoom(spec.x, spec.y, spec.x2)

        if spec.gesture_type == GestureType.SCROLL:
            result = await self._screen_tools.swipe(
                spec.x, spec.y, spec.x2, spec.y2, spec.duration_ms
            )
            return result.success

        raise ValueError(f"Unknown gesture type: {spec.gesture_type}")

    async def _pinch(self, cx: int, cy: int, distance: int = 100) -> bool:
        """捏合（缩小）"""
        half = distance // 2

        result1 = await self._screen_tools.swipe(cx - half, cy, cx - 10, cy, 300)
        if not result1.success:
            return False

        result2 = await self._screen_tools.swipe(cx + half, cy, cx + 10, cy, 300)
        return result2.success

    async def _zoom(self, cx: int, cy: int, distance: int = 100) -> bool:
        """放大"""
        half = distance // 2

        result1 = await self._screen_tools.swipe(cx - 10, cy, cx - half, cy, 300)
        if not result1.success:
            return False

        result2 = await self._screen_tools.swipe(cx + 10, cy, cx + half, cy, 300)
        return result2.success

    async def capture_screen(self) -> ToolResult:
        """截取屏幕"""
        if not self._initialized:
            if not await self.initialize():
                return ToolResult(success=False, error="GestureExecutor not initialized")

        if self._screen_tools:
            return await self._screen_tools.capture_screen()
        return ToolResult(success=False, error="ScreenTools not available")

    async def tap(self, x: int, y: int) -> GestureResult:
        """便捷方法：点击"""
        return await self.execute(GestureSpec(
            gesture_type=GestureType.TAP,
            x=x,
            y=y,
        ))

    async def double_tap(self, x: int, y: int) -> GestureResult:
        """便捷方法：双击"""
        return await self.execute(GestureSpec(
            gesture_type=GestureType.DOUBLE_TAP,
            x=x,
            y=y,
        ))

    async def long_press(self, x: int, y: int, duration_ms: int = 1000) -> GestureResult:
        """便捷方法：长按"""
        return await self.execute(GestureSpec(
            gesture_type=GestureType.LONG_PRESS,
            x=x,
            y=y,
            duration_ms=duration_ms,
        ))

    async def swipe(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        duration_ms: int = 300
    ) -> GestureResult:
        """便捷方法：滑动"""
        return await self.execute(GestureSpec(
            gesture_type=GestureType.SWIPE,
            x=x1,
            y=y1,
            x2=x2,
            y2=y2,
            duration_ms=duration_ms,
        ))

    async def scroll_up(self, width: int, height: int, distance: int = 500) -> GestureResult:
        """便捷方法：向上滚动"""
        cx = width // 2
        return await self.swipe(cx, height // 2 + distance // 2, cx, height // 2 - distance // 2)

    async def scroll_down(self, width: int, height: int, distance: int = 500) -> GestureResult:
        """便捷方法：向下滚动"""
        cx = width // 2
        return await self.swipe(cx, height // 2 - distance // 2, cx, height // 2 + distance // 2)

    async def scroll_left(self, width: int, height: int, distance: int = 500) -> GestureResult:
        """便捷方法：向左滚动"""
        cy = height // 2
        return await self.swipe(width // 2 + distance // 2, cy, width // 2 - distance // 2, cy)

    async def scroll_right(self, width: int, height: int, distance: int = 500) -> GestureResult:
        """便捷方法：向右滚动"""
        cy = height // 2
        return await self.swipe(width // 2 - distance // 2, cy, width // 2 + distance // 2, cy)

    async def input_text(self, text: str) -> ToolResult:
        """输入文本"""
        if not self._initialized:
            if not await self.initialize():
                return ToolResult(success=False, error="GestureExecutor not initialized")

        if self._screen_tools:
            return await self._screen_tools.input_text(text)
        return ToolResult(success=False, error="ScreenTools not available")

    async def press_key(self, keycode: str) -> ToolResult:
        """按下按键"""
        if not self._initialized:
            if not await self.initialize():
                return ToolResult(success=False, error="GestureExecutor not initialized")

        if self._screen_tools:
            return await self._screen_tools.press_key(keycode)
        return ToolResult(success=False, error="ScreenTools not available")

    @property
    def node_cache(self) -> NodeCache:
        """获取节点缓存"""
        return self._node_cache

    @property
    def screen_tools(self) -> ScreenTools | None:
        """获取屏幕工具"""
        return self._screen_tools


gesture_executor = GestureExecutor()
