"""
PyAgent 桌面自动化模块 - 自动化核心
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .keyboard import KeyboardController
from .mouse import MouseController
from .screen import ScreenCapture


@dataclass
class DesktopSession:
    session_id: str
    created_at: datetime
    screen_resolution: tuple[int, int]
    scale_factor: float = 1.0
    operations_count: int = 0
    last_operation: str = ""


@dataclass
class OperationResult:
    success: bool
    message: str
    screenshot: bytes | None = None
    data: dict[str, Any] = field(default_factory=dict)


class DesktopAutomation:
    """桌面自动化核心"""

    def __init__(self):
        self.screen = ScreenCapture()
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self._session: DesktopSession | None = None
        self._llm_client: Any = None
        self._operation_history: list[dict[str, Any]] = []

    def initialize(self, llm_client: Any | None = None) -> DesktopSession:
        import uuid

        screen_info = self.screen.get_screen_info()
        resolution = (
            screen_info.width if screen_info else 1920,
            screen_info.height if screen_info else 1080
        )

        self._session = DesktopSession(
            session_id=str(uuid.uuid4())[:8],
            created_at=datetime.now(),
            screen_resolution=resolution,
            scale_factor=screen_info.scale_factor if screen_info else 1.0,
        )

        self._llm_client = llm_client
        return self._session

    def get_session(self) -> DesktopSession | None:
        return self._session

    async def execute_task(
        self,
        task_description: str,
        verify: bool = True
    ) -> OperationResult:
        if not self._session:
            self.initialize()

        screenshot_before = self.screen.capture_screen()

        result = await self._execute_with_ai(task_description)

        if verify and result.success:
            verification = await self.verify_operation(screenshot_before)
            if not verification.success:
                result.success = False
                result.message = f"操作验证失败: {verification.message}"

        if self._session:
            self._session.operations_count += 1
            self._session.last_operation = task_description

        self._operation_history.append({
            "task": task_description,
            "success": result.success,
            "timestamp": datetime.now().isoformat(),
        })

        return result

    async def _execute_with_ai(self, task_description: str) -> OperationResult:
        if not self._llm_client:
            return OperationResult(
                success=False,
                message="LLM客户端未初始化"
            )

        screenshot = self.screen.capture_screen()
        if not screenshot:
            return OperationResult(
                success=False,
                message="无法捕获屏幕"
            )

        try:
            response = await self._llm_client.chat(
                f"""分析当前屏幕并执行以下任务: {task_description}

请返回操作步骤的JSON格式:
{{
    "steps": [
        {{"action": "click", "x": 100, "y": 200}},
        {{"action": "type", "text": "hello"}}
    ]
}}"""
            )

            steps = self._parse_ai_response(response.get("content", ""))
            for step in steps:
                await self._execute_step(step)

            return OperationResult(
                success=True,
                message="任务执行完成",
                screenshot=self.screen.capture_screen()
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"执行失败: {e!s}"
            )

    def _parse_ai_response(self, response: str) -> list[dict[str, Any]]:
        import json
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])
                return data.get("steps", [])
        except Exception:
            pass
        return []

    async def _execute_step(self, step: dict[str, Any]) -> bool:
        action = step.get("action", "")

        if action == "click":
            x, y = step.get("x", 0), step.get("y", 0)
            return self.mouse.click(x, y)
        if action == "double_click":
            x, y = step.get("x", 0), step.get("y", 0)
            return self.mouse.double_click(x, y)
        if action == "type":
            text = step.get("text", "")
            return self.keyboard.type_text(text)
        if action == "hotkey":
            keys = step.get("keys", [])
            return self.keyboard.hotkey(*keys)
        if action == "scroll":
            direction = step.get("direction", "down")
            amount = step.get("amount", 3)
            return self.mouse.scroll(direction, amount)
        if action == "wait":
            duration = step.get("duration", 1.0)
            await asyncio.sleep(duration)
            return True

        return False

    async def verify_operation(
        self,
        screenshot_before: bytes | None = None
    ) -> OperationResult:
        if not self._llm_client:
            return OperationResult(
                success=True,
                message="无LLM客户端，跳过验证"
            )

        screenshot_after = self.screen.capture_screen()
        if not screenshot_after:
            return OperationResult(
                success=False,
                message="无法捕获验证截图"
            )

        try:
            response = await self._llm_client.chat(
                '请验证操作是否成功执行。返回JSON: {"success": true/false, "message": "描述"}'
            )

            import json
            start = response.get("content", "").find("{")
            end = response.get("content", "").rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response.get("content", "")[start:end])
                return OperationResult(
                    success=result.get("success", False),
                    message=result.get("message", ""),
                    screenshot=screenshot_after
                )
        except Exception:
            pass

        return OperationResult(
            success=True,
            message="验证完成"
        )

    async def take_screenshot_and_analyze(self) -> dict[str, Any]:
        screenshot = self.screen.capture_screen()
        if not screenshot:
            return {"error": "无法捕获屏幕"}

        if self._llm_client:
            try:
                response = await self._llm_client.chat(
                    "请分析当前屏幕内容，返回JSON格式的分析结果。"
                )
                return {
                    "screenshot_size": len(screenshot),
                    "analysis": response.get("content", ""),
                }
            except Exception:
                pass

        return {
            "screenshot_size": len(screenshot),
            "analysis": "屏幕已捕获",
        }

    def get_operation_history(self) -> list[dict[str, Any]]:
        return self._operation_history.copy()

    def shutdown(self) -> None:
        self._session = None
        self._operation_history.clear()


desktop_automation = DesktopAutomation()
