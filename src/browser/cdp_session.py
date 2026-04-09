"""
PyAgent 浏览器自动化模块 - CDP 会话管理

提供 Chrome DevTools Protocol (CDP) 会话管理功能，支持：
- CDP 会话的创建、复用和销毁
- 多标签页的 CDP 会话管理
- 会话池管理和健康检查
- CDP 命令封装（DOM、Accessibility、Page、Runtime）
"""

import asyncio
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """CDP 会话状态"""
    IDLE = "idle"
    ACTIVE = "active"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class CDPSessionInfo:
    """CDP 会话信息"""
    session_id: str
    target_id: str
    state: SessionState = SessionState.IDLE
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: datetime = field(default_factory=datetime.now)
    command_count: int = 0
    error_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "target_id": self.target_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat(),
            "command_count": self.command_count,
            "error_count": self.error_count
        }

    def touch(self) -> None:
        """更新最后使用时间"""
        self.last_used_at = datetime.now()


@dataclass
class CDPCommandResult:
    """CDP 命令执行结果"""
    success: bool
    result: Any = None
    error: str | None = None
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms
        }


class CDPSessionWrapper:
    """
    CDP 会话封装类
    
    封装 Playwright 的 CDP 会话，提供便捷的 CDP 命令调用接口。
    """

    def __init__(self, session, info: CDPSessionInfo):
        """
        初始化 CDP 会话封装
        
        Args:
            session: Playwright CDPSession 对象
            info: 会话信息
        """
        self._session = session
        self._info = info
        self._event_handlers: dict[str, list[Callable]] = {}
        self._lock = asyncio.Lock()

    @property
    def session_id(self) -> str:
        return self._info.session_id

    @property
    def target_id(self) -> str:
        return self._info.target_id

    @property
    def state(self) -> SessionState:
        return self._info.state

    @property
    def info(self) -> CDPSessionInfo:
        return self._info

    @property
    def raw_session(self):
        return self._session

    async def execute(
        self,
        method: str,
        params: dict[str, Any] | None = None
    ) -> CDPCommandResult:
        """
        执行 CDP 命令
        
        Args:
            method: CDP 方法名
            params: 命令参数
            
        Returns:
            CDPCommandResult: 命令执行结果
        """
        start_time = time.perf_counter()

        async with self._lock:
            try:
                self._info.state = SessionState.ACTIVE
                self._info.touch()

                params = params or {}
                result = await self._session.send(method, params)

                self._info.command_count += 1
                self._info.state = SessionState.IDLE

                execution_time = (time.perf_counter() - start_time) * 1000

                logger.debug(
                    f"CDP 命令执行成功: {method}, "
                    f"耗时: {execution_time:.2f}ms"
                )

                return CDPCommandResult(
                    success=True,
                    result=result,
                    execution_time_ms=execution_time
                )

            except Exception as e:
                self._info.error_count += 1
                self._info.state = SessionState.ERROR

                execution_time = (time.perf_counter() - start_time) * 1000

                logger.error(f"CDP 命令执行失败: {method}, 错误: {e}")

                return CDPCommandResult(
                    success=False,
                    error=str(e),
                    execution_time_ms=execution_time
                )

    async def on(self, event: str, handler: Callable) -> None:
        """
        注册事件监听器
        
        Args:
            event: 事件名
            handler: 事件处理函数
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

        self._session.on(event, handler)
        logger.debug(f"已注册 CDP 事件监听器: {event}")

    async def off(self, event: str, handler: Callable | None = None) -> None:
        """
        移除事件监听器
        
        Args:
            event: 事件名
            handler: 事件处理函数，None 则移除所有
        """
        if event not in self._event_handlers:
            return

        if handler is None:
            for h in self._event_handlers[event]:
                self._session.remove_listener(event, h)
            self._event_handlers[event] = []
        else:
            self._session.remove_listener(event, handler)
            if handler in self._event_handlers[event]:
                self._event_handlers[event].remove(handler)

        logger.debug(f"已移除 CDP 事件监听器: {event}")

    async def close(self) -> bool:
        """
        关闭 CDP 会话
        
        Returns:
            bool: 是否成功关闭
        """
        try:
            for event, handlers in self._event_handlers.items():
                for handler in handlers:
                    try:
                        self._session.remove_listener(event, handler)
                    except Exception:
                        pass

            self._event_handlers.clear()

            await self._session.detach()

            self._info.state = SessionState.CLOSED

            logger.info(f"CDP 会话已关闭: {self.session_id}")
            return True

        except Exception as e:
            logger.error(f"关闭 CDP 会话失败: {e}")
            self._info.state = SessionState.ERROR
            return False

    async def is_alive(self) -> bool:
        """
        检查会话是否存活
        
        Returns:
            bool: 会话是否存活
        """
        try:
            await self._session.send("Target.getTargetInfo")
            return True
        except Exception:
            self._info.state = SessionState.ERROR
            return False


class CDPSessionManager:
    """
    CDP 会话管理器
    
    管理 CDP 会话的创建、复用和销毁，支持多标签页的 CDP 会话管理。
    """

    DEFAULT_SESSION_TIMEOUT = 300
    DEFAULT_HEALTH_CHECK_INTERVAL = 60
    MAX_SESSIONS = 50

    def __init__(self, controller, config: dict[str, Any] | None = None):
        """
        初始化 CDP 会话管理器
        
        Args:
            controller: BrowserController 实例
            config: 配置选项
        """
        self._controller = controller
        self._config = config or {}

        self._sessions: dict[str, CDPSessionWrapper] = {}
        self._target_sessions: dict[str, str] = {}

        self._session_timeout = self._config.get(
            "session_timeout",
            self.DEFAULT_SESSION_TIMEOUT
        )
        self._health_check_interval = self._config.get(
            "health_check_interval",
            self.DEFAULT_HEALTH_CHECK_INTERVAL
        )
        self._max_sessions = self._config.get(
            "max_sessions",
            self.MAX_SESSIONS
        )

        self._cleanup_task: asyncio.Task | None = None
        self._running = False
        self._lock = asyncio.Lock()

    @property
    def context(self):
        return self._controller.context

    @property
    def page(self):
        return self._controller.page

    @property
    def browser(self):
        return self._controller.browser

    @property
    def session_count(self) -> int:
        return len(self._sessions)

    async def start(self) -> None:
        """启动会话管理器"""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("CDP 会话管理器已启动")

    async def stop(self) -> None:
        """停止会话管理器"""
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

        await self.close_all_sessions()
        logger.info("CDP 会话管理器已停止")

    async def get_or_create_cdp_session(
        self,
        target_id: str | None = None,
        page=None
    ) -> CDPSessionWrapper | None:
        """
        获取或创建 CDP 会话
        
        Args:
            target_id: 目标 ID（页面 ID）
            page: Playwright Page 对象，用于获取 CDP 会话
            
        Returns:
            CDPSessionWrapper | None: CDP 会话封装
        """
        async with self._lock:
            if target_id and target_id in self._target_sessions:
                session_id = self._target_sessions[target_id]
                if session_id in self._sessions:
                    session = self._sessions[session_id]
                    if await session.is_alive():
                        session.info.touch()
                        return session
                    await self._remove_session(session_id)

            target_page = page or self.page
            if not target_page:
                logger.error("无法创建 CDP 会话：页面未初始化")
                return None

            try:
                cdp_session = await target_page.context.new_cdp_session(target_page)

                session_id = str(uuid.uuid4())[:8]
                actual_target_id = target_id or str(uuid.uuid4())[:8]

                info = CDPSessionInfo(
                    session_id=session_id,
                    target_id=actual_target_id,
                    state=SessionState.IDLE
                )

                wrapper = CDPSessionWrapper(cdp_session, info)

                self._sessions[session_id] = wrapper
                self._target_sessions[actual_target_id] = session_id

                logger.info(
                    f"CDP 会话已创建: session_id={session_id}, "
                    f"target_id={actual_target_id}"
                )

                return wrapper

            except Exception as e:
                logger.error(f"创建 CDP 会话失败: {e}")
                return None

    async def get_session(self, session_id: str) -> CDPSessionWrapper | None:
        """
        获取指定 CDP 会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            CDPSessionWrapper | None: CDP 会话封装
        """
        return self._sessions.get(session_id)

    async def get_session_by_target(self, target_id: str) -> CDPSessionWrapper | None:
        """
        通过目标 ID 获取 CDP 会话
        
        Args:
            target_id: 目标 ID
            
        Returns:
            CDPSessionWrapper | None: CDP 会话封装
        """
        session_id = self._target_sessions.get(target_id)
        if session_id:
            return self._sessions.get(session_id)
        return None

    async def close_session(self, session_id: str) -> bool:
        """
        关闭指定 CDP 会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            bool: 是否成功关闭
        """
        async with self._lock:
            return await self._remove_session(session_id)

    async def _remove_session(self, session_id: str) -> bool:
        """
        移除会话（内部方法）
        
        Args:
            session_id: 会话 ID
            
        Returns:
            bool: 是否成功移除
        """
        if session_id not in self._sessions:
            return False

        session = self._sessions[session_id]

        await session.close()

        target_id = session.target_id
        if target_id in self._target_sessions:
            del self._target_sessions[target_id]

        del self._sessions[session_id]

        logger.info(f"CDP 会话已移除: {session_id}")
        return True

    async def close_all_sessions(self) -> int:
        """
        关闭所有 CDP 会话
        
        Returns:
            int: 关闭的会话数量
        """
        async with self._lock:
            closed_count = 0

            for session_id in list(self._sessions.keys()):
                try:
                    await self._remove_session(session_id)
                    closed_count += 1
                except Exception as e:
                    logger.error(f"关闭会话失败 {session_id}: {e}")

            self._sessions.clear()
            self._target_sessions.clear()

            logger.info(f"已关闭所有 CDP 会话: {closed_count} 个")
            return closed_count

    async def execute_cdp_command(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        session_id: str | None = None,
        target_id: str | None = None
    ) -> CDPCommandResult:
        """
        执行 CDP 命令
        
        Args:
            method: CDP 方法名
            params: 命令参数
            session_id: 会话 ID（优先使用）
            target_id: 目标 ID
            
        Returns:
            CDPCommandResult: 命令执行结果
        """
        session = None

        if session_id:
            session = await self.get_session(session_id)
        elif target_id:
            session = await self.get_session_by_target(target_id)

        if not session:
            session = await self.get_or_create_cdp_session(target_id)

        if not session:
            return CDPCommandResult(
                success=False,
                error="无法获取 CDP 会话"
            )

        return await session.execute(method, params)

    async def _cleanup_loop(self) -> None:
        """会话清理循环"""
        while self._running:
            try:
                await asyncio.sleep(self._health_check_interval)
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"会话清理出错: {e}")

    async def _cleanup_expired_sessions(self) -> int:
        """
        清理过期会话
        
        Returns:
            int: 清理的会话数量
        """
        now = datetime.now()
        expired_sessions = []

        for session_id, session in self._sessions.items():
            time_since_use = (now - session.info.last_used_at).total_seconds()

            if time_since_use > self._session_timeout or not await session.is_alive():
                expired_sessions.append(session_id)

        cleaned_count = 0
        for session_id in expired_sessions:
            try:
                await self._remove_session(session_id)
                cleaned_count += 1
            except Exception as e:
                logger.error(f"清理会话失败 {session_id}: {e}")

        if cleaned_count > 0:
            logger.info(f"已清理过期 CDP 会话: {cleaned_count} 个")

        return cleaned_count

    async def get_all_sessions(self) -> list[CDPSessionInfo]:
        """
        获取所有会话信息
        
        Returns:
            list[CDPSessionInfo]: 会话信息列表
        """
        return [session.info for session in self._sessions.values()]

    async def health_check(self) -> dict[str, Any]:
        """
        健康检查
        
        Returns:
            dict[str, Any]: 健康检查结果
        """
        total_sessions = len(self._sessions)
        active_sessions = 0
        error_sessions = 0
        idle_sessions = 0

        for session in self._sessions.values():
            if session.state == SessionState.ACTIVE:
                active_sessions += 1
            elif session.state == SessionState.ERROR:
                error_sessions += 1
            elif session.state == SessionState.IDLE:
                idle_sessions += 1

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "idle_sessions": idle_sessions,
            "error_sessions": error_sessions,
            "max_sessions": self._max_sessions,
            "session_timeout": self._session_timeout,
            "health_check_interval": self._health_check_interval
        }


class CDPCommands:
    """
    CDP 命令封装类
    
    提供常用的 CDP 命令封装，包括 DOM 操作、Accessibility、Page 和 Runtime 命令。
    """

    def __init__(self, session_manager: CDPSessionManager):
        """
        初始化 CDP 命令封装
        
        Args:
            session_manager: CDP 会话管理器
        """
        self._manager = session_manager

    async def get_document(
        self,
        session_id: str | None = None,
        depth: int = -1,
        pierce: bool = True
    ) -> CDPCommandResult:
        """
        获取 DOM 文档
        
        Args:
            session_id: 会话 ID
            depth: 递归深度，-1 表示无限
            pierce: 是否穿透 shadow DOM
            
        Returns:
            CDPCommandResult: 命令结果
        """
        params = {
            "depth": depth,
            "pierce": pierce
        }
        return await self._manager.execute_cdp_command(
            "DOM.getDocument",
            params,
            session_id=session_id
        )

    async def get_dom_snapshot(
        self,
        session_id: str | None = None,
        computed_styles: list[str] | None = None,
        include_event_listeners: bool = False
    ) -> CDPCommandResult:
        """
        获取 DOM 快照
        
        Args:
            session_id: 会话 ID
            computed_styles: 要包含的计算样式列表
            include_event_listeners: 是否包含事件监听器
            
        Returns:
            CDPCommandResult: 命令结果
        """
        params = {
            "computedStyles": computed_styles or [],
            "includeEventListeners": include_event_listeners
        }
        return await self._manager.execute_cdp_command(
            "DOMSnapshot.captureSnapshot",
            params,
            session_id=session_id
        )

    async def describe_node(
        self,
        node_id: int,
        session_id: str | None = None,
        depth: int = -1
    ) -> CDPCommandResult:
        """
        描述 DOM 节点
        
        Args:
            node_id: 节点 ID
            session_id: 会话 ID
            depth: 递归深度
            
        Returns:
            CDPCommandResult: 命令结果
        """
        params = {
            "nodeId": node_id,
            "depth": depth
        }
        return await self._manager.execute_cdp_command(
            "DOM.describeNode",
            params,
            session_id=session_id
        )

    async def query_selector(
        self,
        node_id: int,
        selector: str,
        session_id: str | None = None
    ) -> CDPCommandResult:
        """
        查询选择器
        
        Args:
            node_id: 节点 ID
            selector: CSS 选择器
            session_id: 会话 ID
            
        Returns:
            CDPCommandResult: 命令结果
        """
        params = {
            "nodeId": node_id,
            "selector": selector
        }
        return await self._manager.execute_cdp_command(
            "DOM.querySelector",
            params,
            session_id=session_id
        )

    async def get_full_ax_tree(
        self,
        session_id: str | None = None,
        depth: int = -1,
        frame_id: str | None = None
    ) -> CDPCommandResult:
        """
        获取完整无障碍树
        
        Args:
            session_id: 会话 ID
            depth: 递归深度
            frame_id: 帧 ID
            
        Returns:
            CDPCommandResult: 命令结果
        """
        params: dict[str, Any] = {"depth": depth}
        if frame_id:
            params["frameId"] = frame_id

        return await self._manager.execute_cdp_command(
            "Accessibility.getFullAXTree",
            params,
            session_id=session_id
        )

    async def get_partial_ax_tree(
        self,
        node_id: int,
        session_id: str | None = None,
        fetch_relatives: bool = True
    ) -> CDPCommandResult:
        """
        获取部分无障碍树
        
        Args:
            node_id: 节点 ID
            session_id: 会话 ID
            fetch_relatives: 是否获取相关节点
            
        Returns:
            CDPCommandResult: 命令结果
        """
        params = {
            "backendNodeId": node_id,
            "fetchRelatives": fetch_relatives
        }
        return await self._manager.execute_cdp_command(
            "Accessibility.getPartialAXTree",
            params,
            session_id=session_id
        )

    async def get_layout_metrics(
        self,
        session_id: str | None = None
    ) -> CDPCommandResult:
        """
        获取布局度量
        
        Args:
            session_id: 会话 ID
            
        Returns:
            CDPCommandResult: 命令结果
        """
        return await self._manager.execute_cdp_command(
            "Page.getLayoutMetrics",
            {},
            session_id=session_id
        )

    async def print_to_pdf(
        self,
        session_id: str | None = None,
        landscape: bool = False,
        display_header_footer: bool = False,
        print_background: bool = True,
        scale: float = 1.0,
        paper_width: float = 8.5,
        paper_height: float = 11.0,
        margin_top: float = 0.4,
        margin_bottom: float = 0.4,
        margin_left: float = 0.4,
        margin_right: float = 0.4
    ) -> CDPCommandResult:
        """
        打印为 PDF
        
        Args:
            session_id: 会话 ID
            landscape: 横向模式
            display_header_footer: 显示页眉页脚
            print_background: 打印背景
            scale: 缩放比例
            paper_width: 纸张宽度（英寸）
            paper_height: 纸张高度（英寸）
            margin_top: 上边距（英寸）
            margin_bottom: 下边距（英寸）
            margin_left: 左边距（英寸）
            margin_right: 右边距（英寸）
            
        Returns:
            CDPCommandResult: 命令结果
        """
        params = {
            "landscape": landscape,
            "displayHeaderFooter": display_header_footer,
            "printBackground": print_background,
            "scale": scale,
            "paperWidth": paper_width,
            "paperHeight": paper_height,
            "marginTop": margin_top,
            "marginBottom": margin_bottom,
            "marginLeft": margin_left,
            "marginRight": margin_right
        }
        return await self._manager.execute_cdp_command(
            "Page.printToPDF",
            params,
            session_id=session_id
        )

    async def capture_screenshot(
        self,
        session_id: str | None = None,
        format: str = "png",
        quality: int | None = None,
        clip: dict[str, Any] | None = None,
        from_surface: bool = True
    ) -> CDPCommandResult:
        """
        捕获屏幕截图
        
        Args:
            session_id: 会话 ID
            format: 图片格式（png/jpeg/webp）
            quality: 图片质量（jpeg/webp 时有效）
            clip: 裁剪区域
            from_surface: 是否从表面捕获
            
        Returns:
            CDPCommandResult: 命令结果
        """
        params: dict[str, Any] = {
            "format": format,
            "fromSurface": from_surface
        }
        if quality is not None:
            params["quality"] = quality
        if clip:
            params["clip"] = clip

        return await self._manager.execute_cdp_command(
            "Page.captureScreenshot",
            params,
            session_id=session_id
        )

    async def evaluate(
        self,
        expression: str,
        session_id: str | None = None,
        object_group: str | None = None,
        include_command_line_api: bool = True,
        return_by_value: bool = True,
        await_promise: bool = True
    ) -> CDPCommandResult:
        """
        执行 JavaScript 表达式
        
        Args:
            expression: JavaScript 表达式
            session_id: 会话 ID
            object_group: 对象组名
            include_command_line_api: 是否包含命令行 API
            return_by_value: 是否按值返回
            await_promise: 是否等待 Promise
            
        Returns:
            CDPCommandResult: 命令结果
        """
        params: dict[str, Any] = {
            "expression": expression,
            "includeCommandLineAPI": include_command_line_api,
            "returnByValue": return_by_value,
            "awaitPromise": await_promise
        }
        if object_group:
            params["objectGroup"] = object_group

        return await self._manager.execute_cdp_command(
            "Runtime.evaluate",
            params,
            session_id=session_id
        )

    async def call_function_on(
        self,
        function_declaration: str,
        session_id: str | None = None,
        object_id: str | None = None,
        arguments: list[dict[str, Any]] | None = None,
        return_by_value: bool = True,
        await_promise: bool = True
    ) -> CDPCommandResult:
        """
        在对象上调用函数
        
        Args:
            function_declaration: 函数声明
            session_id: 会话 ID
            object_id: 对象 ID
            arguments: 参数列表
            return_by_value: 是否按值返回
            await_promise: 是否等待 Promise
            
        Returns:
            CDPCommandResult: 命令结果
        """
        params: dict[str, Any] = {
            "functionDeclaration": function_declaration,
            "returnByValue": return_by_value,
            "awaitPromise": await_promise
        }
        if object_id:
            params["objectId"] = object_id
        if arguments:
            params["arguments"] = arguments

        return await self._manager.execute_cdp_command(
            "Runtime.callFunctionOn",
            params,
            session_id=session_id
        )

    async def get_properties(
        self,
        object_id: str,
        session_id: str | None = None,
        own_properties: bool = True
    ) -> CDPCommandResult:
        """
        获取对象属性
        
        Args:
            object_id: 对象 ID
            session_id: 会话 ID
            own_properties: 是否只获取自有属性
            
        Returns:
            CDPCommandResult: 命令结果
        """
        params = {
            "objectId": object_id,
            "ownProperties": own_properties
        }
        return await self._manager.execute_cdp_command(
            "Runtime.getProperties",
            params,
            session_id=session_id
        )

    async def enable_domains(
        self,
        domains: list[str],
        session_id: str | None = None
    ) -> dict[str, CDPCommandResult]:
        """
        启用 CDP 域
        
        Args:
            domains: 域名列表（如 ["DOM", "Page", "Runtime"]）
            session_id: 会话 ID
            
        Returns:
            dict[str, CDPCommandResult]: 各域的启用结果
        """
        results = {}
        for domain in domains:
            results[domain] = await self._manager.execute_cdp_command(
                f"{domain}.enable",
                {},
                session_id=session_id
            )
        return results

    async def disable_domains(
        self,
        domains: list[str],
        session_id: str | None = None
    ) -> dict[str, CDPCommandResult]:
        """
        禁用 CDP 域
        
        Args:
            domains: 域名列表
            session_id: 会话 ID
            
        Returns:
            dict[str, CDPCommandResult]: 各域的禁用结果
        """
        results = {}
        for domain in domains:
            results[domain] = await self._manager.execute_cdp_command(
                f"{domain}.disable",
                {},
                session_id=session_id
            )
        return results
