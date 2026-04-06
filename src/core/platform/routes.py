"""
移动端特定路由

提供移动端特有的API路由。
"""

from typing import Any

from src.core.platform.adapter import get_platform_adapter
from src.mobile.notification import NotificationReader
from src.mobile.screen_tools import ScreenTools
from src.mobile.sms import SMSTools


async def handle_mobile_status() -> dict[str, Any]:
    adapter = get_platform_adapter()
    return adapter.get_status_info()


async def handle_capabilities() -> dict[str, Any]:
    adapter = get_platform_adapter()
    return adapter.capabilities.to_dict()


async def handle_screen_capture() -> dict[str, Any]:
    adapter = get_platform_adapter()
    if not adapter.capabilities.has_screen:
        return {"success": False, "error": "Screen not available"}

    if adapter.is_android():
        tools = ScreenTools()
        result = await tools.capture_screen()
        return result.to_dict()

    return {"success": False, "error": "Screen capture not supported on this platform"}


async def handle_screen_tap(data: dict[str, Any]) -> dict[str, Any]:
    adapter = get_platform_adapter()
    if not adapter.capabilities.has_screen:
        return {"success": False, "error": "Screen not available"}

    if adapter.is_android():
        tools = ScreenTools()
        x = data.get("x", 0)
        y = data.get("y", 0)
        result = await tools.tap(x, y)
        return result.to_dict()

    return {"success": False, "error": "Screen tap not supported on this platform"}


async def handle_screen_swipe(data: dict[str, Any]) -> dict[str, Any]:
    adapter = get_platform_adapter()
    if not adapter.capabilities.has_screen:
        return {"success": False, "error": "Screen not available"}

    if adapter.is_android():
        tools = ScreenTools()
        x1 = data.get("x1", 0)
        y1 = data.get("y1", 0)
        x2 = data.get("x2", 0)
        y2 = data.get("y2", 0)
        result = await tools.swipe(x1, y1, x2, y2)
        return result.to_dict()

    return {"success": False, "error": "Screen swipe not supported on this platform"}


async def handle_get_notifications() -> dict[str, Any]:
    adapter = get_platform_adapter()
    if not adapter.config.enable_notification:
        return {"success": False, "error": "Notification disabled"}

    if adapter.is_android():
        reader = NotificationReader()
        notifications = await reader.get_notifications()
        return {"success": True, "notifications": notifications}

    return {"success": False, "error": "Notifications not supported on this platform"}


async def handle_get_sms() -> dict[str, Any]:
    adapter = get_platform_adapter()
    if not adapter.config.enable_sms:
        return {"success": False, "error": "SMS disabled"}

    if adapter.is_android():
        tools = SMSTools()
        messages = await tools.get_messages()
        return {"success": True, "messages": messages}

    return {"success": False, "error": "SMS not supported on this platform"}


async def handle_send_sms(data: dict[str, Any]) -> dict[str, Any]:
    adapter = get_platform_adapter()
    if not adapter.config.enable_sms:
        return {"success": False, "error": "SMS disabled"}

    if adapter.is_android():
        tools = SMSTools()
        to = data.get("to", "")
        body = data.get("body", "")
        result = await tools.send_message(to, body)
        return result.to_dict()

    return {"success": False, "error": "SMS not supported on this platform"}


def get_mobile_routes() -> list[tuple[str, str, Any]]:
    return [
        ("/api/mobile/status", "GET", handle_mobile_status),
        ("/api/mobile/capabilities", "GET", handle_capabilities),
        ("/api/mobile/screen/capture", "POST", handle_screen_capture),
        ("/api/mobile/screen/tap", "POST", handle_screen_tap),
        ("/api/mobile/screen/swipe", "POST", handle_screen_swipe),
        ("/api/mobile/notifications", "GET", handle_get_notifications),
        ("/api/mobile/sms", "GET", handle_get_sms),
        ("/api/mobile/sms/send", "POST", handle_send_sms),
    ]
