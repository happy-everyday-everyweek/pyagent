"""
PyAgent 浏览器自动化模块

基于 Playwright 实现的浏览器自动化功能，支持：
- 浏览器控制（启动、关闭、导航等）
- DOM序列化（元素提取、文本提取等）
- 动作执行（点击、输入、滚动等）
- 多标签页管理
- 事件系统（事件类型定义和事件处理）
- CDP 会话管理（Chrome DevTools Protocol）
"""

from .actions import ActionExecutor, ActionResult
from .agent import (
    AgentHistory,
    AgentState,
    AgentStatus,
    BrowserAgent,
    MessageManager,
    StepResult,
)
from .browser_tools import (
    BrowserTools,
    create_browser_tools,
)
from .cdp_session import (
    CDPCommandResult,
    CDPCommands,
    CDPSessionInfo,
    CDPSessionManager,
    CDPSessionWrapper,
    SessionState,
)
from .controller import BrowserController, BrowserSession
from .dom_enhanced import (
    DOMElementEnhanced,
    EnhancedDOMSerializer,
)
from .dom_serializer import DOMElement, DOMSerializer
from .event_bus import (
    BaseEvent,
    BrowserEvent,
    BrowserStartEvent,
    BrowserStopEvent,
    ErrorEvent,
    EventBus,
    EventHandler,
    EventPriority,
    EventResult,
    EventState,
    FileDownloadedEvent,
    NavigateEvent,
    PageLoadedEvent,
    ScreenshotEvent,
    ScriptExecutedEvent,
    TabClosedEvent,
    TabCreatedEvent,
    TabSwitchedEvent,
    get_event_bus,
    set_event_bus,
)
from .events import (
    BrowserEvent as BrowserActionEvent,
)
from .events import (
    ClickCoordinateEvent,
    ClickElementEvent,
    CloseTabEvent,
    EventStatus,
    EventType,
    ExecuteScriptEvent,
    ExtractContentEvent,
    GetDropdownOptionsEvent,
    GoBackEvent,
    GoForwardEvent,
    NavigateToUrlEvent,
    NewTabEvent,
    RefreshEvent,
    ScrollEvent,
    SelectDropdownOptionEvent,
    SendKeysEvent,
    SwitchTabEvent,
    TypeTextEvent,
    UploadFileEvent,
    create_event,
)
from .events import (
    ScreenshotEvent as ScreenshotActionEvent,
)
from .locator import (
    ClickElementParams,
    ElementInfo,
    ElementLocator,
    InputTextParams,
    LocateResult,
    LocatorType,
)
from .loop_detector import (
    ActionRecord,
    LoopAlert,
    LoopDetector,
    LoopDetectorConfig,
    LoopType,
    PageFingerprint,
)
from .planner import (
    Plan,
    PlanStatus,
    PlanStep,
    StepStatus,
    TaskPlanner,
)
from .registry import (
    ActionModel,
    Controller,
    RegisteredAction,
    Registry,
    Tools,
)
from .registry import (
    ActionResult as RegistryActionResult,
)
from .sensitive import (
    SensitiveDataConfig,
    SensitiveDataHandler,
    SensitiveDataType,
    SensitiveField,
    SensitiveLogFilter,
)
from .sensitive import (
    SensitiveDataHandler as SensitiveHandler,
)
from .state import (
    BrowserState,
    BrowserStateHistory,
    DOMState,
    PageLoadState,
    StateDiff,
    StateManager,
    TabState,
)
from .state import (
    DOMElement as StateDOMElement,
)
from .structured_output import (
    ExtractedItem,
    ExtractionResult,
    StructuredOutputProcessor,
)
from .tab_manager import TabInfo, TabManager
from .vision import (
    BoundingBox,
    ScreenshotResult,
    VisionAnalysisResult,
    VisionMode,
    VisionProcessor,
)

__all__ = [
    "ActionExecutor",
    "ActionModel",
    "ActionRecord",
    "ActionResult",
    "AgentHistory",
    "AgentState",
    "AgentStatus",
    "BaseEvent",
    "BoundingBox",
    "BrowserActionEvent",
    "BrowserAgent",
    "BrowserController",
    "BrowserEvent",
    "BrowserSession",
    "BrowserStartEvent",
    "BrowserState",
    "BrowserStateHistory",
    "BrowserStopEvent",
    "BrowserTools",
    "CDPCommandResult",
    "CDPCommands",
    "CDPSessionInfo",
    "CDPSessionManager",
    "CDPSessionWrapper",
    "ClickCoordinateEvent",
    "ClickElementEvent",
    "ClickElementParams",
    "CloseTabEvent",
    "Controller",
    "DOMElement",
    "DOMElementEnhanced",
    "DOMElementEnhanced",
    "DOMSerializer",
    "DOMState",
    "ElementInfo",
    "ElementLocator",
    "EnhancedDOMSerializer",
    "EnhancedDOMSerializer",
    "ErrorEvent",
    "EventBus",
    "EventHandler",
    "EventPriority",
    "EventResult",
    "EventState",
    "EventStatus",
    "EventType",
    "ExecuteScriptEvent",
    "ExtractContentEvent",
    "ExtractedItem",
    "ExtractionResult",
    "FileDownloadedEvent",
    "GetDropdownOptionsEvent",
    "GoBackEvent",
    "GoForwardEvent",
    "InputTextParams",
    "LocateResult",
    "LocatorType",
    "LoopAlert",
    "LoopDetector",
    "LoopDetectorConfig",
    "LoopType",
    "MessageManager",
    "NavigateEvent",
    "NavigateToUrlEvent",
    "NewTabEvent",
    "PageFingerprint",
    "PageLoadState",
    "PageLoadedEvent",
    "Plan",
    "PlanStatus",
    "PlanStep",
    "RefreshEvent",
    "RegisteredAction",
    "Registry",
    "RegistryActionResult",
    "ScreenshotActionEvent",
    "ScreenshotEvent",
    "ScreenshotResult",
    "ScriptExecutedEvent",
    "ScrollEvent",
    "SelectDropdownOptionEvent",
    "SendKeysEvent",
    "SensitiveDataConfig",
    "SensitiveDataHandler",
    "SensitiveDataType",
    "SensitiveField",
    "SensitiveHandler",
    "SensitiveLogFilter",
    "SessionState",
    "StateDOMElement",
    "StateDiff",
    "StateManager",
    "StepResult",
    "StepStatus",
    "StructuredOutputProcessor",
    "SwitchTabEvent",
    "TabClosedEvent",
    "TabCreatedEvent",
    "TabInfo",
    "TabManager",
    "TabState",
    "TabSwitchedEvent",
    "TaskPlanner",
    "Tools",
    "TypeTextEvent",
    "UploadFileEvent",
    "VisionAnalysisResult",
    "VisionMode",
    "VisionProcessor",
    "create_browser_tools",
    "create_event",
    "get_event_bus",
    "set_event_bus",
]

__version__ = "0.8.2"
