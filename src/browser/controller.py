"""
PyAgent 浏览器自动化模块 - 浏览器控制器

提供浏览器生命周期管理和基础操作功能。
"""

import base64
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BrowserType(Enum):
    """浏览器类型"""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


@dataclass
class BrowserSession:
    """浏览器会话数据类"""
    session_id: str
    browser_type: str
    headless: bool
    user_agent: str
    cookies: list[dict] = field(default_factory=list)
    localStorage: dict = field(default_factory=dict)  # noqa: N815
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "browser_type": self.browser_type,
            "headless": self.headless,
            "user_agent": self.user_agent,
            "cookies": self.cookies,
            "localStorage": self.localStorage,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class BrowserConfig:
    """浏览器配置"""
    browser_type: BrowserType = BrowserType.CHROMIUM
    headless: bool = True
    user_agent: str = ""
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout: int = 30000
    slow_mo: int = 0
    downloads_path: str = ""
    proxy: dict[str, str] = field(default_factory=dict)
    args: list[str] = field(default_factory=list)
    ignore_https_errors: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BrowserConfig":
        browser_type = BrowserType(data.get("browser_type", "chromium"))
        return cls(
            browser_type=browser_type,
            headless=data.get("headless", True),
            user_agent=data.get("user_agent", ""),
            viewport_width=data.get("viewport_width", 1920),
            viewport_height=data.get("viewport_height", 1080),
            timeout=data.get("timeout", 30000),
            slow_mo=data.get("slow_mo", 0),
            downloads_path=data.get("downloads_path", ""),
            proxy=data.get("proxy", {}),
            args=data.get("args", []),
            ignore_https_errors=data.get("ignore_https_errors", False)
        )


class BrowserController:
    """浏览器控制器"""

    def __init__(self, config: BrowserConfig | None = None):
        self.config = config or BrowserConfig()
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._session: BrowserSession | None = None
        self._is_launched = False

    @property
    def page(self):
        return self._page

    @property
    def context(self):
        return self._context

    @property
    def browser(self):
        return self._browser

    @property
    def session(self) -> BrowserSession | None:
        return self._session

    @property
    def is_launched(self) -> bool:
        return self._is_launched

    async def launch(self, headless: bool | None = None) -> BrowserSession:
        """
        启动浏览器

        Args:
            headless: 是否无头模式，None则使用配置值

        Returns:
            BrowserSession: 浏览器会话信息
        """
        if self._is_launched:
            logger.warning("浏览器已经启动")
            return self._session

        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()

            headless_mode = headless if headless is not None else self.config.headless

            browser_launcher = getattr(
                self._playwright,
                self.config.browser_type.value
            )

            launch_options = {
                "headless": headless_mode,
                "args": self.config.args,
            }

            if self.config.proxy:
                launch_options["proxy"] = self.config.proxy

            self._browser = await browser_launcher.launch(**launch_options)

            context_options = {
                "viewport": {
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height
                },
                "ignore_https_errors": self.config.ignore_https_errors,
            }

            if self.config.user_agent:
                context_options["user_agent"] = self.config.user_agent

            if self.config.downloads_path:
                context_options["downloads_path"] = self.config.downloads_path

            self._context = await self._browser.new_context(**context_options)

            self._context.set_default_timeout(self.config.timeout)

            if self.config.slow_mo > 0:
                self._context.set_default_navigation_timeout(self.config.timeout)

            self._page = await self._context.new_page()

            user_agent = await self._page.evaluate("navigator.userAgent")

            self._session = BrowserSession(
                session_id=str(uuid.uuid4()),
                browser_type=self.config.browser_type.value,
                headless=headless_mode,
                user_agent=user_agent
            )

            self._is_launched = True
            logger.info(f"浏览器已启动: session_id={self._session.session_id}")

            return self._session

        except ImportError as e:
            raise RuntimeError(
                "Playwright未安装，请运行: pip install playwright && playwright install"
            ) from e
        except Exception as e:
            logger.error(f"启动浏览器失败: {e}")
            raise RuntimeError(f"启动浏览器失败: {e}") from e

    async def close(self) -> bool:
        """
        关闭浏览器

        Returns:
            bool: 是否成功关闭
        """
        if not self._is_launched:
            return True

        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()

            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
            self._session = None
            self._is_launched = False

            logger.info("浏览器已关闭")
            return True

        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")
            return False

    async def navigate(self, url: str, wait_until: str = "load") -> str:
        """
        导航到URL

        Args:
            url: 目标URL
            wait_until: 等待条件 (load/domcontentloaded/networkidle)

        Returns:
            str: 最终URL（可能被重定向）
        """
        if not self._is_launched or not self._page:
            raise RuntimeError("浏览器未启动")

        try:
            _ = await self._page.goto(url, wait_until=wait_until)
            final_url = self._page.url
            logger.info(f"导航到: {url} -> {final_url}")
            return final_url
        except Exception as e:
            logger.error(f"导航失败: {e}")
            raise RuntimeError(f"导航失败: {e}") from e

    async def get_current_url(self) -> str:
        """
        获取当前URL

        Returns:
            str: 当前页面URL
        """
        if not self._is_launched or not self._page:
            raise RuntimeError("浏览器未启动")

        return self._page.url

    async def take_screenshot(
        self,
        full_page: bool = False,
        save_path: str | None = None,
        return_base64: bool = True
    ) -> str:
        """
        截取屏幕截图

        Args:
            full_page: 是否截取整个页面
            save_path: 保存路径（可选）
            return_base64: 是否返回base64编码

        Returns:
            str: base64编码的图片或文件路径
        """
        if not self._is_launched or not self._page:
            raise RuntimeError("浏览器未启动")

        try:
            screenshot_bytes = await self._page.screenshot(
                full_page=full_page,
                type="png"
            )

            if save_path:
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(screenshot_bytes)
                logger.info(f"截图已保存: {save_path}")

            if return_base64:
                return base64.b64encode(screenshot_bytes).decode("utf-8")

            return save_path or ""

        except Exception as e:
            logger.error(f"截图失败: {e}")
            raise

    async def execute_script(self, script: str, *args) -> Any:
        """
        执行JavaScript脚本

        Args:
            script: JavaScript代码
            *args: 脚本参数

        Returns:
            Any: 脚本执行结果
        """
        if not self._is_launched or not self._page:
            raise RuntimeError("浏览器未启动")

        try:
            result = await self._page.evaluate(script, *args)
            return result
        except Exception as e:
            logger.error(f"执行脚本失败: {e}")
            raise

    async def wait_for_selector(
        self,
        selector: str,
        timeout: int | None = None,
        state: str = "visible"
    ) -> bool:
        """
        等待选择器出现

        Args:
            selector: CSS选择器
            timeout: 超时时间（毫秒）
            state: 等待状态 (visible/hidden/attached/detached)

        Returns:
            bool: 是否成功等待到元素
        """
        if not self._is_launched or not self._page:
            raise RuntimeError("浏览器未启动")

        try:
            timeout_ms = timeout or self.config.timeout
            await self._page.wait_for_selector(
                selector,
                timeout=timeout_ms,
                state=state
            )
            return True
        except Exception as e:
            logger.error(f"等待选择器失败: {e}")
            return False

    async def get_page_content(self) -> str:
        """
        获取页面HTML内容

        Returns:
            str: 页面HTML
        """
        if not self._is_launched or not self._page:
            raise RuntimeError("浏览器未启动")

        try:
            content = await self._page.content()
            return content
        except Exception as e:
            logger.error(f"获取页面内容失败: {e}")
            raise

    async def get_page_title(self) -> str:
        """
        获取页面标题

        Returns:
            str: 页面标题
        """
        if not self._is_launched or not self._page:
            raise RuntimeError("浏览器未启动")

        return await self._page.title()

    async def reload(self, wait_until: str = "load") -> str:
        """
        刷新页面

        Args:
            wait_until: 等待条件

        Returns:
            str: 当前URL
        """
        if not self._is_launched or not self._page:
            raise RuntimeError("浏览器未启动")

        await self._page.reload(wait_until=wait_until)
        return self._page.url

    async def go_back(self, wait_until: str = "load") -> bool:
        """
        后退

        Returns:
            bool: 是否成功后退
        """
        if not self._is_launched or not self._page:
            raise RuntimeError("浏览器未启动")

        return await self._page.go_back(wait_until=wait_until) is not None

    async def go_forward(self, wait_until: str = "load") -> bool:
        """
        前进

        Returns:
            bool: 是否成功前进
        """
        if not self._is_launched or not self._page:
            raise RuntimeError("浏览器未启动")

        return await self._page.go_forward(wait_until=wait_until) is not None

    async def set_cookies(self, cookies: list[dict]) -> bool:
        """
        设置Cookies

        Args:
            cookies: Cookie列表

        Returns:
            bool: 是否成功
        """
        if not self._is_launched or not self._context:
            raise RuntimeError("浏览器未启动")

        try:
            await self._context.add_cookies(cookies)
            if self._session:
                self._session.cookies.extend(cookies)
            return True
        except Exception as e:
            logger.error(f"设置Cookies失败: {e}")
            return False

    async def get_cookies(self) -> list[dict]:
        """
        获取当前Cookies

        Returns:
            list[dict]: Cookie列表
        """
        if not self._is_launched or not self._context:
            raise RuntimeError("浏览器未启动")

        return await self._context.cookies()

    async def set_local_storage(self, key: str, value: str) -> bool:
        """
        设置LocalStorage

        Args:
            key: 键
            value: 值

        Returns:
            bool: 是否成功
        """
        if not self._is_launched or not self._page:
            raise RuntimeError("浏览器未启动")

        try:
            await self._page.evaluate(
                f"localStorage.setItem('{key}', '{value}')"
            )
            if self._session:
                self._session.localStorage[key] = value
            return True
        except Exception as e:
            logger.error(f"设置LocalStorage失败: {e}")
            return False

    async def get_local_storage(self, key: str | None = None) -> Any:
        """
        获取LocalStorage

        Args:
            key: 键（可选，不传则返回全部）

        Returns:
            Any: 存储值或全部存储
        """
        if not self._is_launched or not self._page:
            raise RuntimeError("浏览器未启动")

        if key:
            return await self._page.evaluate(
                f"localStorage.getItem('{key}')"
            )
        return await self._page.evaluate(
            "Object.assign({}, localStorage)"
        )

    async def wait_for_load_state(self, state: str = "load") -> None:
        """
        等待页面加载状态

        Args:
            state: 加载状态 (load/domcontentloaded/networkidle)
        """
        if not self._is_launched or not self._page:
            raise RuntimeError("浏览器未启动")

        await self._page.wait_for_load_state(state)

    async def set_viewport_size(self, width: int, height: int) -> None:
        """
        设置视口大小

        Args:
            width: 宽度
            height: 高度
        """
        if not self._is_launched or not self._page:
            raise RuntimeError("浏览器未启动")

        await self._page.set_viewport_size({"width": width, "height": height})

    async def emulate_media(
        self,
        media: str | None = None,
        color_scheme: str | None = None
    ) -> None:
        """
        模拟媒体类型

        Args:
            media: 媒体类型 (screen/print)
            color_scheme: 颜色方案 (light/dark/no-preference)
        """
        if not self._is_launched or not self._page:
            raise RuntimeError("浏览器未启动")

        await self._page.emulate_media(
            media=media,
            color_scheme=color_scheme
        )

    async def __aenter__(self) -> "BrowserController":
        await self.launch()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
