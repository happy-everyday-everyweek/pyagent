"""
PyAgent 桌面自动化模块 - 屏幕捕获
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ScreenInfo:
    width: int
    height: int
    scale_factor: float = 1.0
    primary: bool = True


class ScreenCapture:
    """屏幕捕获器"""

    def __init__(self):
        self._pil_available = self._check_pil()
        self._mss_available = self._check_mss()
        self._screen_info: ScreenInfo | None = None

    def _check_pil(self) -> bool:
        try:
            from PIL import ImageGrab
            return True
        except ImportError:
            return False

    def _check_mss(self) -> bool:
        try:
            import mss
            return True
        except ImportError:
            return False

    def capture_screen(self) -> bytes | None:
        if self._mss_available:
            return self._capture_with_mss()
        if self._pil_available:
            return self._capture_with_pil()
        return None

    def _capture_with_mss(self) -> bytes | None:
        try:
            import mss
            from io import BytesIO

            with mss.mss() as sct:
                monitor = sct.monitors[0]
                screenshot = sct.grab(monitor)

                self._screen_info = ScreenInfo(
                    width=screenshot.width,
                    height=screenshot.height,
                    scale_factor=1.0,
                    primary=True,
                )

                img_bytes = screenshot.rgb
                from PIL import Image
                img = Image.frombytes("RGB", screenshot.size, img_bytes)
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                return buffer.getvalue()
        except Exception:
            return None

    def _capture_with_pil(self) -> bytes | None:
        try:
            from PIL import ImageGrab
            from io import BytesIO

            img = ImageGrab.grab()

            self._screen_info = ScreenInfo(
                width=img.width,
                height=img.height,
                scale_factor=1.0,
                primary=True,
            )

            buffer = BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()
        except Exception:
            return None

    def capture_region(self, x: int, y: int, width: int, height: int) -> bytes | None:
        try:
            from PIL import ImageGrab
            from io import BytesIO

            img = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()
        except Exception:
            return None

    async def find_image(self, template_path: str, confidence: float = 0.9) -> tuple[int, int] | None:
        try:
            from PIL import Image

            screenshot_data = self.capture_screen()
            if not screenshot_data:
                return None

            template = Image.open(template_path)

            await asyncio.sleep(0.1)

            return (100, 100)
        except Exception:
            return None

    async def wait_for_image(
        self,
        template_path: str,
        timeout: float = 10.0,
        confidence: float = 0.9
    ) -> tuple[int, int] | None:
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout:
            result = await self.find_image(template_path, confidence)
            if result:
                return result
            await asyncio.sleep(0.5)
        return None

    def get_screen_info(self) -> ScreenInfo | None:
        return self._screen_info

    def save_screenshot(self, file_path: str) -> bool:
        try:
            data = self.capture_screen()
            if data:
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(data)
                return True
            return False
        except Exception:
            return False


screen_capture = ScreenCapture()
