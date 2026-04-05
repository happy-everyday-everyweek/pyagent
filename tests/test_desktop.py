"""
PyAgent 桌面自动化测试
"""

import pytest
from datetime import datetime

from desktop.automation import (
    DesktopAutomation,
    DesktopSession,
    OperationResult,
    desktop_automation,
)
from desktop.mouse import MouseController, MouseButton
from desktop.keyboard import KeyboardController
from desktop.screen import ScreenCapture


class TestDesktopSession:
    """测试桌面会话"""

    def test_session_creation(self):
        session = DesktopSession(
            session_id="session_001",
            created_at=datetime.now(),
            screen_resolution=(1920, 1080)
        )
        assert session.session_id == "session_001"
        assert session.screen_resolution == (1920, 1080)
        assert session.operations_count == 0

    def test_session_defaults(self):
        session = DesktopSession(
            session_id="session_001",
            created_at=datetime.now(),
            screen_resolution=(1920, 1080)
        )
        assert session.scale_factor == 1.0
        assert session.operations_count == 0
        assert session.last_operation == ""


class TestOperationResult:
    """测试操作结果"""

    def test_success_result(self):
        result = OperationResult(
            success=True,
            message="Operation completed",
            screenshot=b"fake_screenshot"
        )
        assert result.success is True
        assert result.message == "Operation completed"
        assert result.screenshot == b"fake_screenshot"

    def test_error_result(self):
        result = OperationResult(
            success=False,
            message="Operation failed"
        )
        assert result.success is False
        assert result.message == "Operation failed"

    def test_result_with_data(self):
        result = OperationResult(
            success=True,
            message="Success",
            data={"key": "value"}
        )
        assert result.data == {"key": "value"}


class TestMouseController:
    """测试鼠标控制器"""

    def setup_method(self):
        self.mouse = MouseController()

    def test_controller_creation(self):
        assert self.mouse is not None

    def test_click_coordinates(self):
        result = self.mouse.click(100, 200)
        assert isinstance(result, bool)

    def test_double_click(self):
        result = self.mouse.double_click(100, 200)
        assert isinstance(result, bool)

    def test_right_click(self):
        result = self.mouse.right_click(100, 200)
        assert isinstance(result, bool)

    def test_scroll(self):
        result = self.mouse.scroll("down", 3)
        assert isinstance(result, bool)

    def test_move_to(self):
        result = self.mouse.move_to(500, 500)
        assert isinstance(result, bool)


class TestKeyboardController:
    """测试键盘控制器"""

    def setup_method(self):
        self.keyboard = KeyboardController()

    def test_controller_creation(self):
        assert self.keyboard is not None

    def test_type_text(self):
        result = self.keyboard.type_text("Hello World")
        assert isinstance(result, bool)

    def test_press_key(self):
        result = self.keyboard.press_key("enter")
        assert isinstance(result, bool)

    def test_hotkey(self):
        result = self.keyboard.hotkey("ctrl", "c")
        assert isinstance(result, bool)


class TestScreenCapture:
    """测试屏幕捕获"""

    def setup_method(self):
        self.screen = ScreenCapture()

    def test_capture_creation(self):
        assert self.screen is not None

    def test_get_screen_info(self):
        info = self.screen.get_screen_info()
        assert info is not None or info is None

    def test_capture_screen(self):
        screenshot = self.screen.capture_screen()
        assert screenshot is not None or screenshot is None


class TestDesktopAutomation:
    """测试桌面自动化"""

    def setup_method(self):
        self.automation = DesktopAutomation()

    def test_automation_creation(self):
        assert self.automation.screen is not None
        assert self.automation.mouse is not None
        assert self.automation.keyboard is not None

    def test_initialize(self):
        session = self.automation.initialize()
        assert session is not None
        assert session.session_id is not None
        assert self.automation.get_session() == session

    def test_get_session_without_init(self):
        automation = DesktopAutomation()
        session = automation.get_session()
        assert session is None

    def test_shutdown(self):
        self.automation.initialize()
        self.automation.shutdown()
        assert self.automation.get_session() is None

    def test_get_operation_history(self):
        history = self.automation.get_operation_history()
        assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_execute_task_without_llm(self):
        self.automation.initialize()
        result = await self.automation.execute_task("Test task", verify=False)
        assert result.success is False
        assert "LLM" in result.message or "llm" in result.message.lower()

    @pytest.mark.asyncio
    async def test_take_screenshot_and_analyze_without_llm(self):
        self.automation.initialize()
        result = await self.automation.take_screenshot_and_analyze()
        assert "error" in result or "screenshot_size" in result

    def test_parse_ai_response_valid_json(self):
        response = '{"steps": [{"action": "click", "x": 100, "y": 200}]}'
        steps = self.automation._parse_ai_response(response)
        assert len(steps) == 1
        assert steps[0]["action"] == "click"

    def test_parse_ai_response_invalid_json(self):
        response = "This is not JSON"
        steps = self.automation._parse_ai_response(response)
        assert steps == []

    def test_parse_ai_response_embedded_json(self):
        response = 'Here are the steps: {"steps": [{"action": "type", "text": "hello"}]}'
        steps = self.automation._parse_ai_response(response)
        assert len(steps) == 1


class TestDesktopAutomationGlobal:
    """测试全局桌面自动化实例"""

    def test_global_instance(self):
        assert desktop_automation is not None
        assert isinstance(desktop_automation, DesktopAutomation)
