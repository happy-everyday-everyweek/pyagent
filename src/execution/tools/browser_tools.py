"""
PyAgent 执行模块工具系统 - 浏览器自动化工具

提供浏览器自动化相关的工具集成。
"""

import logging
from pathlib import Path
from typing import Any

import yaml

from .base import BaseTool, RiskLevel, ToolCategory, ToolParameter, ToolResult

logger = logging.getLogger(__name__)


class BrowserLaunchTool(BaseTool):
    """浏览器启动工具"""

    name = "browser_launch"
    description = "启动浏览器实例"
    category = ToolCategory.BROWSER
    risk_level = RiskLevel.LOW

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="headless",
                type="boolean",
                description="是否无头模式",
                required=False,
                default=True
            ),
            ToolParameter(
                name="browser_type",
                type="string",
                description="浏览器类型",
                required=False,
                default="chromium",
                enum=["chromium", "firefox", "webkit"]
            )
        ]
        self._controller = None

    async def execute(self, **kwargs) -> ToolResult:
        """启动浏览器"""
        try:
            from browser import BrowserConfig, BrowserController

            browser_config = self._load_config()
            browser_config.headless = kwargs.get("headless", True)
            browser_type_str = kwargs.get("browser_type", "chromium")
            browser_config.browser_type = BrowserConfig.BrowserType(browser_type_str)

            self._controller = BrowserController(browser_config)
            session = await self._controller.launch()

            return ToolResult(
                success=True,
                output=f"浏览器已启动: session_id={session.session_id}",
                data=session.to_dict()
            )

        except ImportError:
            return ToolResult(
                success=False,
                error="Playwright未安装，请运行: pip install playwright && playwright install"
            )
        except Exception as e:
            logger.error(f"启动浏览器失败: {e}")
            return ToolResult(success=False, error=str(e))

    def _load_config(self) -> Any:
        """加载配置"""
        try:
            from browser import BrowserConfig

            config_path = Path("config/browser.yaml")
            if config_path.exists():
                with open(config_path, encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)
                    return BrowserConfig.from_dict(
                        config_data.get("browser", {})
                    )
        except Exception:
            pass

        from browser import BrowserConfig
        return BrowserConfig()


class BrowserCloseTool(BaseTool):
    """浏览器关闭工具"""

    name = "browser_close"
    description = "关闭浏览器实例"
    category = ToolCategory.BROWSER
    risk_level = RiskLevel.SAFE

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._controller = None

    def set_controller(self, controller):
        """设置浏览器控制器"""
        self._controller = controller

    async def execute(self, **kwargs) -> ToolResult:
        """关闭浏览器"""
        if not self._controller:
            return ToolResult(success=True, output="浏览器未运行")

        try:
            success = await self._controller.close()
            return ToolResult(
                success=success,
                output="浏览器已关闭" if success else "关闭失败"
            )
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")
            return ToolResult(success=False, error=str(e))


class BrowserNavigateTool(BaseTool):
    """浏览器导航工具"""

    name = "browser_navigate"
    description = "导航到指定URL"
    category = ToolCategory.BROWSER
    risk_level = RiskLevel.LOW

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="url",
                type="string",
                description="目标URL",
                required=True
            ),
            ToolParameter(
                name="wait_until",
                type="string",
                description="等待条件",
                required=False,
                default="load",
                enum=["load", "domcontentloaded", "networkidle"]
            )
        ]
        self._controller = None

    def set_controller(self, controller):
        self._controller = controller

    async def execute(self, **kwargs) -> ToolResult:
        """导航到URL"""
        if not self._controller or not self._controller.is_launched:
            return ToolResult(success=False, error="浏览器未启动")

        url = kwargs.get("url", "")
        wait_until = kwargs.get("wait_until", "load")

        try:
            final_url = await self._controller.navigate(url, wait_until)
            return ToolResult(
                success=True,
                output=f"已导航到: {final_url}",
                data={"url": final_url}
            )
        except Exception as e:
            logger.error(f"导航失败: {e}")
            return ToolResult(success=False, error=str(e))


class BrowserScreenshotTool(BaseTool):
    """浏览器截图工具"""

    name = "browser_screenshot"
    description = "截取当前页面截图"
    category = ToolCategory.BROWSER
    risk_level = RiskLevel.SAFE

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="full_page",
                type="boolean",
                description="是否截取整个页面",
                required=False,
                default=False
            ),
            ToolParameter(
                name="save_path",
                type="string",
                description="保存路径（可选）",
                required=False
            )
        ]
        self._controller = None

    def set_controller(self, controller):
        self._controller = controller

    async def execute(self, **kwargs) -> ToolResult:
        """截取截图"""
        if not self._controller or not self._controller.is_launched:
            return ToolResult(success=False, error="浏览器未启动")

        full_page = kwargs.get("full_page", False)
        save_path = kwargs.get("save_path")

        try:
            screenshot_base64 = await self._controller.take_screenshot(
                full_page=full_page,
                save_path=save_path,
                return_base64=True
            )
            return ToolResult(
                success=True,
                output="截图成功",
                data={"screenshot": screenshot_base64[:100] + "..."}
            )
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return ToolResult(success=False, error=str(e))


class BrowserClickTool(BaseTool):
    """浏览器点击工具"""

    name = "browser_click"
    description = "点击页面元素"
    category = ToolCategory.BROWSER
    risk_level = RiskLevel.MEDIUM

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="selector",
                type="string",
                description="CSS选择器",
                required=False
            ),
            ToolParameter(
                name="xpath",
                type="string",
                description="XPath表达式",
                required=False
            ),
            ToolParameter(
                name="text",
                type="string",
                description="元素文本内容",
                required=False
            )
        ]
        self._controller = None

    def set_controller(self, controller):
        self._controller = controller

    async def execute(self, **kwargs) -> ToolResult:
        """点击元素"""
        if not self._controller or not self._controller.is_launched:
            return ToolResult(success=False, error="浏览器未启动")

        from browser import ActionExecutor

        executor = ActionExecutor(self._controller)

        selector = kwargs.get("selector")
        xpath = kwargs.get("xpath")
        text = kwargs.get("text")

        if text:
            selector = f"text={text}"

        result = await executor.click(selector=selector, xpath=xpath)

        return ToolResult(
            success=result.success,
            output=result.message,
            error=result.error
        )


class BrowserTypeTool(BaseTool):
    """浏览器输入工具"""

    name = "browser_type"
    description = "在输入框中输入文本"
    category = ToolCategory.BROWSER
    risk_level = RiskLevel.MEDIUM

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="text",
                type="string",
                description="要输入的文本",
                required=True
            ),
            ToolParameter(
                name="selector",
                type="string",
                description="CSS选择器",
                required=False
            ),
            ToolParameter(
                name="xpath",
                type="string",
                description="XPath表达式",
                required=False
            ),
            ToolParameter(
                name="clear_first",
                type="boolean",
                description="是否先清空",
                required=False,
                default=True
            )
        ]
        self._controller = None

    def set_controller(self, controller):
        self._controller = controller

    async def execute(self, **kwargs) -> ToolResult:
        """输入文本"""
        if not self._controller or not self._controller.is_launched:
            return ToolResult(success=False, error="浏览器未启动")

        from browser import ActionExecutor

        executor = ActionExecutor(self._controller)

        text = kwargs.get("text", "")
        selector = kwargs.get("selector")
        xpath = kwargs.get("xpath")
        clear_first = kwargs.get("clear_first", True)

        result = await executor.type_text(
            text=text,
            selector=selector,
            xpath=xpath,
            clear_first=clear_first
        )

        return ToolResult(
            success=result.success,
            output=result.message,
            error=result.error
        )


class BrowserScrollTool(BaseTool):
    """浏览器滚动工具"""

    name = "browser_scroll"
    description = "滚动页面"
    category = ToolCategory.BROWSER
    risk_level = RiskLevel.SAFE

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="direction",
                type="string",
                description="滚动方向",
                required=False,
                default="down",
                enum=["up", "down", "left", "right"]
            ),
            ToolParameter(
                name="amount",
                type="integer",
                description="滚动量（像素）",
                required=False,
                default=300
            )
        ]
        self._controller = None

    def set_controller(self, controller):
        self._controller = controller

    async def execute(self, **kwargs) -> ToolResult:
        """滚动页面"""
        if not self._controller or not self._controller.is_launched:
            return ToolResult(success=False, error="浏览器未启动")

        from browser import ActionExecutor

        executor = ActionExecutor(self._controller)

        direction = kwargs.get("direction", "down")
        amount = kwargs.get("amount", 300)

        result = await executor.scroll(direction=direction, amount=amount)

        return ToolResult(
            success=result.success,
            output=result.message,
            error=result.error
        )


class BrowserExtractTool(BaseTool):
    """浏览器内容提取工具"""

    name = "browser_extract"
    description = "提取页面内容"
    category = ToolCategory.BROWSER
    risk_level = RiskLevel.SAFE

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="type",
                type="string",
                description="提取类型",
                required=False,
                default="text",
                enum=["text", "links", "images", "forms", "html"]
            )
        ]
        self._controller = None

    def set_controller(self, controller):
        self._controller = controller

    async def execute(self, **kwargs) -> ToolResult:
        """提取内容"""
        if not self._controller or not self._controller.is_launched:
            return ToolResult(success=False, error="浏览器未启动")

        from browser import DOMSerializer

        serializer = DOMSerializer(self._controller)

        extract_type = kwargs.get("type", "text")

        try:
            if extract_type == "text":
                content = await serializer.extract_text()
            elif extract_type == "links":
                content = await serializer.extract_links()
            elif extract_type == "images":
                content = await serializer.extract_images()
            elif extract_type == "forms":
                content = await serializer.extract_forms()
            elif extract_type == "html":
                content = await self._controller.get_page_content()
            else:
                content = await serializer.extract_text()

            return ToolResult(
                success=True,
                output=f"已提取{extract_type}内容",
                data={"content": content}
            )
        except Exception as e:
            logger.error(f"提取内容失败: {e}")
            return ToolResult(success=False, error=str(e))


class BrowserWaitTool(BaseTool):
    """浏览器等待工具"""

    name = "browser_wait"
    description = "等待元素或时间"
    category = ToolCategory.BROWSER
    risk_level = RiskLevel.SAFE

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="selector",
                type="string",
                description="CSS选择器（可选）",
                required=False
            ),
            ToolParameter(
                name="timeout",
                type="integer",
                description="超时时间（毫秒）",
                required=False,
                default=5000
            ),
            ToolParameter(
                name="state",
                type="string",
                description="等待状态",
                required=False,
                default="visible",
                enum=["visible", "hidden", "attached", "detached"]
            )
        ]
        self._controller = None

    def set_controller(self, controller):
        self._controller = controller

    async def execute(self, **kwargs) -> ToolResult:
        """等待"""
        if not self._controller or not self._controller.is_launched:
            return ToolResult(success=False, error="浏览器未启动")

        selector = kwargs.get("selector")
        timeout = kwargs.get("timeout", 5000)
        state = kwargs.get("state", "visible")

        try:
            if selector:
                success = await self._controller.wait_for_selector(
                    selector, timeout=timeout, state=state
                )
                return ToolResult(
                    success=success,
                    output=f"等待元素{'成功' if success else '超时'}"
                )
            else:
                await self._controller.page.wait_for_timeout(timeout)
                return ToolResult(success=True, output=f"等待{timeout}毫秒完成")
        except Exception as e:
            logger.error(f"等待失败: {e}")
            return ToolResult(success=False, error=str(e))


class BrowserTabTool(BaseTool):
    """浏览器标签页工具"""

    name = "browser_tab"
    description = "管理浏览器标签页"
    category = ToolCategory.BROWSER
    risk_level = RiskLevel.LOW

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型",
                required=True,
                enum=["new", "close", "switch", "list", "active"]
            ),
            ToolParameter(
                name="url",
                type="string",
                description="URL（新建时使用）",
                required=False
            ),
            ToolParameter(
                name="tab_id",
                type="string",
                description="标签页ID",
                required=False
            )
        ]
        self._tab_manager = None

    def set_tab_manager(self, tab_manager):
        self._tab_manager = tab_manager

    async def execute(self, **kwargs) -> ToolResult:
        """执行标签页操作"""
        if not self._tab_manager:
            return ToolResult(success=False, error="标签页管理器未初始化")

        action = kwargs.get("action")
        url = kwargs.get("url", "about:blank")
        tab_id = kwargs.get("tab_id")

        try:
            if action == "new":
                tab = await self._tab_manager.new_tab(url=url)
                return ToolResult(
                    success=True,
                    output=f"新标签页已打开: {tab.tab_id}",
                    data=tab.to_dict()
                )
            elif action == "close":
                if not tab_id:
                    return ToolResult(success=False, error="缺少tab_id参数")
                success = await self._tab_manager.close_tab(tab_id)
                return ToolResult(
                    success=success,
                    output=f"标签页{'已关闭' if success else '关闭失败'}"
                )
            elif action == "switch":
                if not tab_id:
                    return ToolResult(success=False, error="缺少tab_id参数")
                success = await self._tab_manager.switch_tab(tab_id)
                return ToolResult(
                    success=success,
                    output=f"{'已切换' if success else '切换失败'}"
                )
            elif action == "list":
                tabs = await self._tab_manager.get_tabs()
                return ToolResult(
                    success=True,
                    output=f"当前有{len(tabs)}个标签页",
                    data={"tabs": [t.to_dict() for t in tabs]}
                )
            elif action == "active":
                tab = await self._tab_manager.get_active_tab()
                if tab:
                    return ToolResult(
                        success=True,
                        output=f"当前活动标签页: {tab.tab_id}",
                        data=tab.to_dict()
                    )
                return ToolResult(success=False, error="没有活动标签页")
            else:
                return ToolResult(success=False, error=f"未知操作: {action}")
        except Exception as e:
            logger.error(f"标签页操作失败: {e}")
            return ToolResult(success=False, error=str(e))


class BrowserExecuteScriptTool(BaseTool):
    """浏览器脚本执行工具"""

    name = "browser_execute_script"
    description = "执行JavaScript脚本"
    category = ToolCategory.BROWSER
    risk_level = RiskLevel.HIGH

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._parameters = [
            ToolParameter(
                name="script",
                type="string",
                description="JavaScript代码",
                required=True
            )
        ]
        self._controller = None

    def set_controller(self, controller):
        self._controller = controller

    async def execute(self, **kwargs) -> ToolResult:
        """执行脚本"""
        if not self._controller or not self._controller.is_launched:
            return ToolResult(success=False, error="浏览器未启动")

        script = kwargs.get("script", "")

        try:
            result = await self._controller.execute_script(script)
            return ToolResult(
                success=True,
                output="脚本执行成功",
                data={"result": result}
            )
        except Exception as e:
            logger.error(f"脚本执行失败: {e}")
            return ToolResult(success=False, error=str(e))


def get_browser_tools() -> list[type[BaseTool]]:
    """获取所有浏览器工具类"""
    return [
        BrowserLaunchTool,
        BrowserCloseTool,
        BrowserNavigateTool,
        BrowserScreenshotTool,
        BrowserClickTool,
        BrowserTypeTool,
        BrowserScrollTool,
        BrowserExtractTool,
        BrowserWaitTool,
        BrowserTabTool,
        BrowserExecuteScriptTool,
    ]
