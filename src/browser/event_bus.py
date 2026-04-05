"""
PyAgent 浏览器自动化模块 - 事件总线系统

提供事件驱动架构的核心组件，支持异步事件处理、优先级管理和事件链路追踪。
参考 browser-use 项目的 bubus 库设计实现。
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Generic, Protocol, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)

T = TypeVar("T")


class EventPriority(int, Enum):
    """事件处理器优先级"""
    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100
    MONITOR = 200


class EventState(str, Enum):
    """事件状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@runtime_checkable
class EventHandler(Protocol[T]):
    """事件处理器协议
    
    定义事件处理器的标准接口，支持同步和异步处理。
    """
    
    async def __call__(self, event: "BaseEvent[T]") -> T:
        """处理事件
        
        Args:
            event: 要处理的事件对象
            
        Returns:
            处理结果
        """
        ...


@dataclass
class EventResult(Generic[T]):
    """事件处理结果
    
    存储单个事件处理器的执行结果，支持异常捕获和传播。
    """
    handler_name: str
    result: T | None = None
    error: Exception | None = None
    executed_at: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0
    
    @property
    def success(self) -> bool:
        """是否成功执行"""
        return self.error is None
    
    def get_result(self) -> T:
        """获取结果，如果有错误则抛出
        
        Returns:
            处理结果
            
        Raises:
            Exception: 处理过程中发生的异常
        """
        if self.error:
            raise self.error
        return self.result


@dataclass
class BaseEvent(Generic[T]):
    """事件基类
    
    所有事件的基类，提供事件ID、时间戳、父事件追踪等核心功能。
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = field(default="")
    timestamp: datetime = field(default_factory=datetime.now)
    event_parent_id: str | None = None
    _state: EventState = field(default=EventState.PENDING, repr=False)
    _results: list[EventResult[T]] = field(default_factory=list, repr=False)
    _waiters: list[asyncio.Future] = field(default_factory=list, repr=False)
    
    def __post_init__(self) -> None:
        if not self.event_type:
            self.event_type = self.__class__.__name__
    
    def add_result(self, result: EventResult[T]) -> None:
        """添加处理结果"""
        self._results.append(result)
    
    def get_results(self) -> list[EventResult[T]]:
        """获取所有处理结果"""
        return self._results.copy()
    
    def set_state(self, state: EventState) -> None:
        """设置事件状态"""
        self._state = state
        if state in (EventState.COMPLETED, EventState.FAILED):
            for waiter in self._waiters:
                if not waiter.done():
                    waiter.set_result(self)
    
    async def event_result(self, timeout: float | None = None) -> "BaseEvent[T]":
        """等待事件处理完成
        
        Args:
            timeout: 超时时间（秒），None表示无限等待
            
        Returns:
            处理完成后的事件对象
            
        Raises:
            asyncio.TimeoutError: 超时
        """
        if self._state in (EventState.COMPLETED, EventState.FAILED):
            return self
        
        loop = asyncio.get_event_loop()
        future: asyncio.Future[BaseEvent[T]] = loop.create_future()
        self._waiters.append(future)
        
        try:
            if timeout is not None:
                return await asyncio.wait_for(future, timeout=timeout)
            return await future
        except asyncio.TimeoutError:
            self._waiters.remove(future)
            raise
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "event_parent_id": self.event_parent_id,
            "state": self._state.value,
        }


@dataclass
class HandlerRegistration(Generic[T]):
    """处理器注册信息"""
    event_type: type[BaseEvent[T]] | str
    handler: Callable[[BaseEvent[T]], T] | Callable[[BaseEvent[T]], asyncio.Future[T]]
    priority: EventPriority = EventPriority.NORMAL
    handler_name: str = ""
    
    def __post_init__(self) -> None:
        if not self.handler_name:
            self.handler_name = getattr(
                self.handler, "__name__", 
                f"handler_{id(self.handler)}"
            )


class EventBus:
    """事件总线
    
    提供事件的发布订阅功能，支持：
    - 类型安全的事件处理
    - 异步事件处理
    - 事件优先级管理
    - 通配符订阅
    - 事件链路追踪
    - 中间件模式
    """
    
    def __init__(self, name: str = "default") -> None:
        self.name = name
        self._handlers: dict[
            type[BaseEvent[Any]] | str, 
            list[HandlerRegistration[Any]]
        ] = {}
        self._middlewares: list[Callable[[BaseEvent[Any]], bool]] = []
        self._event_history: list[BaseEvent[Any]] = []
        self._max_history: int = 1000
        self._lock = asyncio.Lock()
    
    def on(
        self, 
        event_type: type[BaseEvent[T]] | str,
        handler: Callable[[BaseEvent[T]], T] | Callable[[BaseEvent[T]], asyncio.Future[T]],
        priority: EventPriority = EventPriority.NORMAL
    ) -> str:
        """注册事件监听器
        
        Args:
            event_type: 事件类型或通配符 '*'
            handler: 事件处理函数（同步或异步）
            priority: 处理器优先级
            
        Returns:
            处理器名称，用于后续移除
        """
        registration = HandlerRegistration(
            event_type=event_type,
            handler=handler,
            priority=priority
        )
        
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(registration)
        self._handlers[event_type].sort(
            key=lambda r: r.priority.value, 
            reverse=True
        )
        
        logger.debug(
            f"[{self.name}] 注册事件处理器: "
            f"{registration.handler_name} -> {event_type}"
        )
        
        return registration.handler_name
    
    def off(
        self, 
        event_type: type[BaseEvent[T]] | str,
        handler: Callable[[BaseEvent[T]], Any] | str | None = None
    ) -> bool:
        """移除事件监听器
        
        Args:
            event_type: 事件类型
            handler: 处理函数或处理器名称，None则移除该类型所有处理器
            
        Returns:
            是否成功移除
        """
        if event_type not in self._handlers:
            return False
        
        if handler is None:
            del self._handlers[event_type]
            logger.debug(f"[{self.name}] 移除所有处理器: {event_type}")
            return True
        
        handler_name = handler if isinstance(handler, str) else getattr(
            handler, "__name__", None
        )
        
        if handler_name is None:
            return False
        
        original_count = len(self._handlers[event_type])
        self._handlers[event_type] = [
            r for r in self._handlers[event_type]
            if r.handler_name != handler_name
        ]
        
        removed = len(self._handlers[event_type]) < original_count
        
        if removed:
            logger.debug(
                f"[{self.name}] 移除事件处理器: {handler_name} -> {event_type}"
            )
        
        return removed
    
    def add_middleware(
        self, 
        middleware: Callable[[BaseEvent[Any]], bool]
    ) -> None:
        """添加事件中间件
        
        中间件在事件分发前执行，返回False可阻止事件分发。
        
        Args:
            middleware: 中间件函数，返回True继续分发，False阻止
        """
        self._middlewares.append(middleware)
    
    def remove_middleware(
        self, 
        middleware: Callable[[BaseEvent[Any]], bool]
    ) -> bool:
        """移除事件中间件
        
        Args:
            middleware: 要移除的中间件函数
            
        Returns:
            是否成功移除
        """
        try:
            self._middlewares.remove(middleware)
            return True
        except ValueError:
            return False
    
    def get_handlers(
        self, 
        event_type: type[BaseEvent[T]] | str
    ) -> list[HandlerRegistration[T]]:
        """获取指定事件类型的所有处理器
        
        Args:
            event_type: 事件类型
            
        Returns:
            处理器列表
        """
        return self._handlers.get(event_type, []).copy()
    
    async def dispatch(self, event: BaseEvent[T]) -> BaseEvent[T]:
        """分发事件到所有注册的处理器
        
        按优先级顺序调用处理器，支持异步处理。
        
        Args:
            event: 要分发的事件对象
            
        Returns:
            处理完成后的事件对象
        """
        event.set_state(EventState.PROCESSING)
        
        for middleware in self._middlewares:
            try:
                if not middleware(event):
                    logger.debug(f"[{self.name}] 中间件阻止事件分发: {event.event_type}")
                    event.set_state(EventState.COMPLETED)
                    return event
            except Exception as e:
                logger.error(f"[{self.name}] 中间件执行错误: {e}")
        
        handlers = self._get_handlers_for_event(event)
        
        if not handlers:
            logger.debug(f"[{self.name}] 无处理器: {event.event_type}")
            event.set_state(EventState.COMPLETED)
            return event
        
        for registration in handlers:
            await self._execute_handler(event, registration)
        
        event.set_state(EventState.COMPLETED)
        self._add_to_history(event)
        
        return event
    
    async def _execute_handler(
        self, 
        event: BaseEvent[T], 
        registration: HandlerRegistration[T]
    ) -> None:
        """执行单个处理器"""
        start_time = datetime.now()
        result = EventResult[T](handler_name=registration.handler_name)
        
        try:
            handler_result = registration.handler(event)
            
            if asyncio.iscoroutine(handler_result):
                result.result = await handler_result
            else:
                result.result = handler_result
                
        except Exception as e:
            result.error = e
            logger.error(
                f"[{self.name}] 处理器执行错误: "
                f"{registration.handler_name} -> {e}"
            )
        finally:
            result.duration_ms = (
                datetime.now() - start_time
            ).total_seconds() * 1000
            event.add_result(result)
    
    def _get_handlers_for_event(
        self, 
        event: BaseEvent[T]
    ) -> list[HandlerRegistration[T]]:
        """获取事件的所有处理器（包括通配符处理器）"""
        handlers: list[HandlerRegistration[T]] = []
        
        wildcard_handlers = self._handlers.get("*", [])
        handlers.extend(wildcard_handlers)
        
        event_class = type(event)
        type_handlers = self._handlers.get(event_class, [])
        handlers.extend(type_handlers)
        
        name_handlers = self._handlers.get(event.event_type, [])
        handlers.extend(name_handlers)
        
        seen_names: set[str] = set()
        unique_handlers: list[HandlerRegistration[T]] = []
        for h in handlers:
            if h.handler_name not in seen_names:
                seen_names.add(h.handler_name)
                unique_handlers.append(h)
        
        unique_handlers.sort(key=lambda r: r.priority.value, reverse=True)
        
        return unique_handlers
    
    def _add_to_history(self, event: BaseEvent[T]) -> None:
        """添加事件到历史记录"""
        self._event_history.append(event)
        
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
    
    def get_history(
        self, 
        event_type: type[BaseEvent[T]] | str | None = None,
        limit: int = 100
    ) -> list[BaseEvent[Any]]:
        """获取事件历史记录
        
        Args:
            event_type: 事件类型过滤，None表示所有类型
            limit: 最大返回数量
            
        Returns:
            事件列表
        """
        if event_type is None:
            return self._event_history[-limit:]
        
        filtered = [
            e for e in self._event_history
            if isinstance(e, event_type) or e.event_type == event_type
        ]
        return filtered[-limit:]
    
    def clear_history(self) -> None:
        """清空事件历史记录"""
        self._event_history.clear()
    
    async def emit(self, event: BaseEvent[T]) -> BaseEvent[T]:
        """发射事件（dispatch的别名）"""
        return await self.dispatch(event)
    
    def subscribe(
        self, 
        event_type: type[BaseEvent[T]] | str,
        priority: EventPriority = EventPriority.NORMAL
    ) -> Callable[
        [Callable[[BaseEvent[T]], T]], 
        Callable[[BaseEvent[T]], T]
    ]:
        """装饰器方式订阅事件
        
        Args:
            event_type: 事件类型
            priority: 优先级
            
        Returns:
            装饰器函数
            
        Example:
            @event_bus.subscribe(MyEvent, priority=EventPriority.HIGH)
            async def handle_my_event(event: MyEvent) -> None:
                print(f"处理事件: {event}")
        """
        def decorator(
            handler: Callable[[BaseEvent[T]], T]
        ) -> Callable[[BaseEvent[T]], T]:
            self.on(event_type, handler, priority)
            return handler
        return decorator
    
    def __repr__(self) -> str:
        handler_count = sum(len(h) for h in self._handlers.values())
        return (
            f"EventBus(name={self.name!r}, "
            f"handlers={handler_count}, "
            f"history={len(self._event_history)})"
        )


class BrowserEvent(BaseEvent[None]):
    """浏览器事件基类"""
    pass


@dataclass
class BrowserStartEvent(BrowserEvent):
    """浏览器启动事件"""
    session_id: str = ""
    browser_type: str = ""
    headless: bool = True


@dataclass
class BrowserStopEvent(BrowserEvent):
    """浏览器停止事件"""
    session_id: str = ""
    reason: str = ""


@dataclass
class NavigateEvent(BrowserEvent):
    """页面导航事件"""
    url: str = ""
    final_url: str = ""


@dataclass
class PageLoadedEvent(BrowserEvent):
    """页面加载完成事件"""
    url: str = ""
    title: str = ""


@dataclass
class ScreenshotEvent(BrowserEvent):
    """截图事件"""
    file_path: str = ""
    base64_data: str = ""


@dataclass
class ScriptExecutedEvent(BrowserEvent):
    """脚本执行事件"""
    script: str = ""
    result: Any = None


@dataclass
class TabCreatedEvent(BrowserEvent):
    """标签页创建事件"""
    tab_id: str = ""
    url: str = ""


@dataclass
class TabClosedEvent(BrowserEvent):
    """标签页关闭事件"""
    tab_id: str = ""


@dataclass
class TabSwitchedEvent(BrowserEvent):
    """标签页切换事件"""
    from_tab_id: str = ""
    to_tab_id: str = ""


@dataclass
class FileDownloadedEvent(BrowserEvent):
    """文件下载事件"""
    file_path: str = ""
    file_name: str = ""
    file_size: int = 0


@dataclass
class ErrorEvent(BrowserEvent):
    """错误事件"""
    error_type: str = ""
    error_message: str = ""
    stack_trace: str = ""


_global_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus(name="global")
    return _global_event_bus


def set_event_bus(event_bus: EventBus) -> None:
    """设置全局事件总线实例"""
    global _global_event_bus
    _global_event_bus = event_bus
