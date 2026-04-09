"""
PyAgent 浏览器自动化模块 - 事件类型定义

定义浏览器自动化所需的所有事件类型，使用 Pydantic BaseModel 确保可序列化。
参考 browser-use 项目的事件系统设计。
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """事件类型枚举"""
    NAVIGATE_TO_URL = "navigate_to_url"
    GO_BACK = "go_back"
    GO_FORWARD = "go_forward"
    REFRESH = "refresh"
    CLICK_ELEMENT = "click_element"
    CLICK_COORDINATE = "click_coordinate"
    TYPE_TEXT = "type_text"
    SCROLL = "scroll"
    SEND_KEYS = "send_keys"
    SWITCH_TAB = "switch_tab"
    CLOSE_TAB = "close_tab"
    NEW_TAB = "new_tab"
    SELECT_DROPDOWN_OPTION = "select_dropdown_option"
    GET_DROPDOWN_OPTIONS = "get_dropdown_options"
    UPLOAD_FILE = "upload_file"
    SCREENSHOT = "screenshot"
    EXECUTE_SCRIPT = "execute_script"
    EXTRACT_CONTENT = "extract_content"


class EventStatus(str, Enum):
    """事件状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BrowserEvent(BaseModel):
    """浏览器事件基类"""
    event_id: str = Field(default_factory=lambda: str(id(object())))
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    target_id: str | None = None
    status: EventStatus = EventStatus.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class NavigateToUrlEvent(BrowserEvent):
    """导航到URL事件"""
    event_type: EventType = EventType.NAVIGATE_TO_URL
    url: str
    wait_until: str = "load"
    timeout: int | None = None


class GoBackEvent(BrowserEvent):
    """后退事件"""
    event_type: EventType = EventType.GO_BACK
    wait_until: str = "load"
    timeout: int | None = None


class GoForwardEvent(BrowserEvent):
    """前进事件"""
    event_type: EventType = EventType.GO_FORWARD
    wait_until: str = "load"
    timeout: int | None = None


class RefreshEvent(BrowserEvent):
    """刷新事件"""
    event_type: EventType = EventType.REFRESH
    wait_until: str = "load"
    timeout: int | None = None


class ClickElementEvent(BrowserEvent):
    """点击元素事件"""
    event_type: EventType = EventType.CLICK_ELEMENT
    element_id: str | None = None
    selector: str | None = None
    xpath: str | None = None
    button: str = "left"
    click_count: int = 1
    delay: int = 0
    force: bool = False
    timeout: int | None = None


class ClickCoordinateEvent(BrowserEvent):
    """坐标点击事件"""
    event_type: EventType = EventType.CLICK_COORDINATE
    x: int
    y: int
    button: str = "left"
    click_count: int = 1
    delay: int = 0


class TypeTextEvent(BrowserEvent):
    """输入文本事件"""
    event_type: EventType = EventType.TYPE_TEXT
    text: str
    element_id: str | None = None
    selector: str | None = None
    xpath: str | None = None
    delay: int = 0
    clear_first: bool = False
    timeout: int | None = None


class ScrollEvent(BrowserEvent):
    """滚动事件"""
    event_type: EventType = EventType.SCROLL
    direction: str = "down"
    amount: int = 300
    selector: str | None = None
    element_id: str | None = None
    xpath: str | None = None


class SendKeysEvent(BrowserEvent):
    """发送按键事件"""
    event_type: EventType = EventType.SEND_KEYS
    keys: str
    delay: int = 0
    element_id: str | None = None
    selector: str | None = None
    xpath: str | None = None


class SwitchTabEvent(BrowserEvent):
    """切换标签页事件"""
    event_type: EventType = EventType.SWITCH_TAB
    tab_index: int | None = None
    tab_id: str | None = None


class CloseTabEvent(BrowserEvent):
    """关闭标签页事件"""
    event_type: EventType = EventType.CLOSE_TAB
    tab_index: int | None = None
    tab_id: str | None = None


class NewTabEvent(BrowserEvent):
    """新建标签页事件"""
    event_type: EventType = EventType.NEW_TAB
    url: str | None = None


class SelectDropdownOptionEvent(BrowserEvent):
    """选择下拉选项事件"""
    event_type: EventType = EventType.SELECT_DROPDOWN_OPTION
    value: str | list[str] | None = None
    label: str | list[str] | None = None
    index: int | list[int] | None = None
    element_id: str | None = None
    selector: str | None = None
    xpath: str | None = None


class GetDropdownOptionsEvent(BrowserEvent):
    """获取下拉选项事件"""
    event_type: EventType = EventType.GET_DROPDOWN_OPTIONS
    element_id: str | None = None
    selector: str | None = None
    xpath: str | None = None


class UploadFileEvent(BrowserEvent):
    """上传文件事件"""
    event_type: EventType = EventType.UPLOAD_FILE
    file_path: str
    element_id: str | None = None
    selector: str | None = None
    xpath: str | None = None


class ScreenshotEvent(BrowserEvent):
    """截图事件"""
    event_type: EventType = EventType.SCREENSHOT
    full_page: bool = False
    save_path: str | None = None
    return_base64: bool = True
    selector: str | None = None


class ExecuteScriptEvent(BrowserEvent):
    """执行脚本事件"""
    event_type: EventType = EventType.EXECUTE_SCRIPT
    script: str
    args: list[Any] = Field(default_factory=list)


class ExtractContentEvent(BrowserEvent):
    """提取内容事件"""
    event_type: EventType = EventType.EXTRACT_CONTENT
    selector: str | None = None
    xpath: str | None = None
    extract_type: str = "text"
    attribute: str | None = None
    multiple: bool = False


EVENT_CLASS_MAP: dict[EventType, type[BrowserEvent]] = {
    EventType.NAVIGATE_TO_URL: NavigateToUrlEvent,
    EventType.GO_BACK: GoBackEvent,
    EventType.GO_FORWARD: GoForwardEvent,
    EventType.REFRESH: RefreshEvent,
    EventType.CLICK_ELEMENT: ClickElementEvent,
    EventType.CLICK_COORDINATE: ClickCoordinateEvent,
    EventType.TYPE_TEXT: TypeTextEvent,
    EventType.SCROLL: ScrollEvent,
    EventType.SEND_KEYS: SendKeysEvent,
    EventType.SWITCH_TAB: SwitchTabEvent,
    EventType.CLOSE_TAB: CloseTabEvent,
    EventType.NEW_TAB: NewTabEvent,
    EventType.SELECT_DROPDOWN_OPTION: SelectDropdownOptionEvent,
    EventType.GET_DROPDOWN_OPTIONS: GetDropdownOptionsEvent,
    EventType.UPLOAD_FILE: UploadFileEvent,
    EventType.SCREENSHOT: ScreenshotEvent,
    EventType.EXECUTE_SCRIPT: ExecuteScriptEvent,
    EventType.EXTRACT_CONTENT: ExtractContentEvent,
}


def create_event(event_type: EventType, **kwargs) -> BrowserEvent:
    """
    创建事件实例的工厂函数

    Args:
        event_type: 事件类型
        **kwargs: 事件参数

    Returns:
        BrowserEvent: 事件实例
    """
    event_class = EVENT_CLASS_MAP.get(event_type)
    if not event_class:
        raise ValueError(f"Unknown event type: {event_type}")
    return event_class(**kwargs)
