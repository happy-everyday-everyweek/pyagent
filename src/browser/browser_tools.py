"""
PyAgent 浏览器自动化模块 - 内置动作集

提供完整的浏览器动作实现，包括导航、交互、提取、标签页和文件系统动作。
参考 browser-use 项目的动作设计实现。
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .registry import ActionResult, Registry

logger = logging.getLogger(__name__)


class NavigateParams(BaseModel):
    """导航参数"""
    url: str = Field(description="要导航到的 URL")


class SearchParams(BaseModel):
    """搜索参数"""
    query: str = Field(description="搜索查询")


class ClickParams(BaseModel):
    """点击参数"""
    index: int = Field(description="元素索引")
    num_clicks: int = Field(default=1, ge=1, le=3, description="点击次数")


class InputParams(BaseModel):
    """输入参数"""
    index: int = Field(description="元素索引")
    text: str = Field(description="要输入的文本")
    press_enter: bool = Field(default=False, description="是否按回车")
    clear_first: bool = Field(default=True, description="是否先清空")


class ScrollParams(BaseModel):
    """滚动参数"""
    direction: str = Field(default="down", description="滚动方向: up/down")
    amount: int = Field(default=300, ge=1, le=2000, description="滚动像素数")


class SelectParams(BaseModel):
    """选择参数"""
    index: int = Field(description="元素索引")
    value: str | None = Field(default=None, description="选项值")
    label: str | None = Field(default=None, description="选项文本")


class SwitchTabParams(BaseModel):
    """切换标签页参数"""
    tab_id: int = Field(description="标签页索引")


class CloseTabParams(BaseModel):
    """关闭标签页参数"""
    tab_id: int | None = Field(default=None, description="标签页索引，不指定则关闭当前")


class ExtractParams(BaseModel):
    """提取参数"""
    schema_: dict | None = Field(default=None, alias="schema", description="输出 Schema")


class ReadFileParams(BaseModel):
    """读取文件参数"""
    path: str = Field(description="文件路径")


class WriteFileParams(BaseModel):
    """写入文件参数"""
    path: str = Field(description="文件路径")
    content: str = Field(description="文件内容")


def create_browser_tools(browser_session: Any) -> Registry:
    """
    创建浏览器工具注册中心
    
    Args:
        browser_session: 浏览器会话对象
        
    Returns:
        Registry: 配置好的注册中心
    """
    registry = Registry()

    @registry.action(
        "Navigate to a URL",
        param_model=NavigateParams,
    )
    async def navigate(params: NavigateParams) -> ActionResult:
        """导航到指定 URL"""
        try:
            page = browser_session.page
            if not page:
                return ActionResult(success=False, error="浏览器未启动")

            await page.goto(params.url, wait_until="domcontentloaded", timeout=30000)

            return ActionResult(
                success=True,
                extracted_content=f"Navigated to {params.url}",
                long_term_memory=f"Navigated to {params.url}",
            )
        except Exception as e:
            logger.error(f"Navigate failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Go back to the previous page",
    )
    async def go_back() -> ActionResult:
        """后退到上一页"""
        try:
            page = browser_session.page
            if not page:
                return ActionResult(success=False, error="浏览器未启动")

            await page.go_back(wait_until="domcontentloaded", timeout=30000)

            return ActionResult(
                success=True,
                extracted_content="Went back to previous page",
                long_term_memory="Navigated back",
            )
        except Exception as e:
            logger.error(f"Go back failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Go forward to the next page",
    )
    async def go_forward() -> ActionResult:
        """前进到下一页"""
        try:
            page = browser_session.page
            if not page:
                return ActionResult(success=False, error="浏览器未启动")

            await page.go_forward(wait_until="domcontentloaded", timeout=30000)

            return ActionResult(
                success=True,
                extracted_content="Went forward to next page",
                long_term_memory="Navigated forward",
            )
        except Exception as e:
            logger.error(f"Go forward failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Refresh the current page",
    )
    async def refresh() -> ActionResult:
        """刷新当前页面"""
        try:
            page = browser_session.page
            if not page:
                return ActionResult(success=False, error="浏览器未启动")

            await page.reload(wait_until="domcontentloaded", timeout=30000)

            return ActionResult(
                success=True,
                extracted_content="Page refreshed",
                long_term_memory="Refreshed page",
            )
        except Exception as e:
            logger.error(f"Refresh failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Click on an element by its index",
        param_model=ClickParams,
    )
    async def click(params: ClickParams) -> ActionResult:
        """点击元素"""
        try:
            page = browser_session.page
            if not page:
                return ActionResult(success=False, error="浏览器未启动")

            dom = browser_session.dom_serializer
            if not dom:
                return ActionResult(success=False, error="DOM 序列化器未初始化")

            element = dom.get_element_by_highlight_index(params.index)
            if not element:
                return ActionResult(
                    success=False,
                    error=f"Element with index {params.index} not found",
                )

            if element.css_selector:
                locator = page.locator(element.css_selector)
            elif element.xpath:
                locator = page.locator(f"xpath={element.xpath}")
            else:
                bounds = element.bounding_box
                if bounds:
                    x = bounds.get("x", 0) + bounds.get("width", 0) / 2
                    y = bounds.get("y", 0) + bounds.get("height", 0) / 2
                    await page.mouse.click(x, y, click_count=params.num_clicks)
                    return ActionResult(
                        success=True,
                        extracted_content=f"Clicked element [{params.index}]",
                        long_term_memory=f"Clicked element {params.index}",
                    )
                return ActionResult(success=False, error="无法定位元素")

            await locator.click(click_count=params.num_clicks, timeout=10000)

            return ActionResult(
                success=True,
                extracted_content=f"Clicked element [{params.index}]",
                long_term_memory=f"Clicked element {params.index}",
            )
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Type text into an input element by its index",
        param_model=InputParams,
    )
    async def input_text(params: InputParams) -> ActionResult:
        """输入文本"""
        try:
            page = browser_session.page
            if not page:
                return ActionResult(success=False, error="浏览器未启动")

            dom = browser_session.dom_serializer
            if not dom:
                return ActionResult(success=False, error="DOM 序列化器未初始化")

            element = dom.get_element_by_highlight_index(params.index)
            if not element:
                return ActionResult(
                    success=False,
                    error=f"Element with index {params.index} not found",
                )

            if element.css_selector:
                locator = page.locator(element.css_selector)
            elif element.xpath:
                locator = page.locator(f"xpath={element.xpath}")
            else:
                return ActionResult(success=False, error="无法定位元素")

            if params.clear_first:
                await locator.clear()

            await locator.type(params.text, delay=10)

            if params.press_enter:
                await locator.press("Enter")

            return ActionResult(
                success=True,
                extracted_content=f"Typed '{params.text[:50]}...' into element [{params.index}]",
                long_term_memory=f"Input text into element {params.index}",
            )
        except Exception as e:
            logger.error(f"Input failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Scroll the page in a direction",
        param_model=ScrollParams,
    )
    async def scroll(params: ScrollParams) -> ActionResult:
        """滚动页面"""
        try:
            page = browser_session.page
            if not page:
                return ActionResult(success=False, error="浏览器未启动")

            if params.direction == "down":
                await page.evaluate(f"window.scrollBy(0, {params.amount})")
            elif params.direction == "up":
                await page.evaluate(f"window.scrollBy(0, -{params.amount})")
            else:
                return ActionResult(success=False, error=f"Invalid direction: {params.direction}")

            return ActionResult(
                success=True,
                extracted_content=f"Scrolled {params.direction} by {params.amount}px",
                long_term_memory=f"Scrolled {params.direction}",
            )
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Select an option from a dropdown by element index",
        param_model=SelectParams,
    )
    async def select_option(params: SelectParams) -> ActionResult:
        """选择下拉选项"""
        try:
            page = browser_session.page
            if not page:
                return ActionResult(success=False, error="浏览器未启动")

            dom = browser_session.dom_serializer
            if not dom:
                return ActionResult(success=False, error="DOM 序列化器未初始化")

            element = dom.get_element_by_highlight_index(params.index)
            if not element:
                return ActionResult(
                    success=False,
                    error=f"Element with index {params.index} not found",
                )

            if element.css_selector:
                locator = page.locator(element.css_selector)
            elif element.xpath:
                locator = page.locator(f"xpath={element.xpath}")
            else:
                return ActionResult(success=False, error="无法定位元素")

            if params.value:
                await locator.select_option(value=params.value)
            elif params.label:
                await locator.select_option(label=params.label)
            else:
                return ActionResult(success=False, error="必须提供 value 或 label 参数")

            return ActionResult(
                success=True,
                extracted_content=f"Selected option in element [{params.index}]",
                long_term_memory=f"Selected option in element {params.index}",
            )
        except Exception as e:
            logger.error(f"Select failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Switch to a different browser tab by index",
        param_model=SwitchTabParams,
    )
    async def switch_tab(params: SwitchTabParams) -> ActionResult:
        """切换标签页"""
        try:
            context = browser_session.context
            if not context:
                return ActionResult(success=False, error="浏览器上下文未初始化")

            pages = context.pages
            if params.tab_id < 0 or params.tab_id >= len(pages):
                return ActionResult(
                    success=False,
                    error=f"Invalid tab index: {params.tab_id}, available: 0-{len(pages)-1}",
                )

            page = pages[params.tab_id]
            await page.bring_to_front()

            browser_session.page = page

            return ActionResult(
                success=True,
                extracted_content=f"Switched to tab {params.tab_id}",
                long_term_memory=f"Switched to tab {params.tab_id}",
            )
        except Exception as e:
            logger.error(f"Switch tab failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Close a browser tab by index",
        param_model=CloseTabParams,
    )
    async def close_tab(params: CloseTabParams) -> ActionResult:
        """关闭标签页"""
        try:
            context = browser_session.context
            if not context:
                return ActionResult(success=False, error="浏览器上下文未初始化")

            pages = context.pages

            if params.tab_id is not None:
                if params.tab_id < 0 or params.tab_id >= len(pages):
                    return ActionResult(
                        success=False,
                        error=f"Invalid tab index: {params.tab_id}",
                    )
                page = pages[params.tab_id]
            else:
                page = browser_session.page
                if not page:
                    return ActionResult(success=False, error="没有活动标签页")

            await page.close()

            if context.pages:
                browser_session.page = context.pages[-1]
            else:
                browser_session.page = None

            return ActionResult(
                success=True,
                extracted_content="Closed tab",
                long_term_memory="Closed browser tab",
            )
        except Exception as e:
            logger.error(f"Close tab failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Open a new browser tab",
    )
    async def new_tab() -> ActionResult:
        """新建标签页"""
        try:
            context = browser_session.context
            if not context:
                return ActionResult(success=False, error="浏览器上下文未初始化")

            page = await context.new_page()
            browser_session.page = page

            return ActionResult(
                success=True,
                extracted_content="Opened new tab",
                long_term_memory="Opened new browser tab",
            )
        except Exception as e:
            logger.error(f"New tab failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Extract content from the current page",
        param_model=ExtractParams,
    )
    async def extract(params: ExtractParams) -> ActionResult:
        """提取页面内容"""
        try:
            page = browser_session.page
            if not page:
                return ActionResult(success=False, error="浏览器未启动")

            text = await page.evaluate("""
                () => {
                    const body = document.body;
                    return body.innerText || body.textContent || '';
                }
            """)

            text = text[:5000] if len(text) > 5000 else text

            return ActionResult(
                success=True,
                extracted_content=text,
                long_term_memory="Extracted page content",
            )
        except Exception as e:
            logger.error(f"Extract failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Search for text on the current page",
    )
    async def search_page(query: str) -> ActionResult:
        """在页面上搜索文本"""
        try:
            page = browser_session.page
            if not page:
                return ActionResult(success=False, error="浏览器未启动")

            content = await page.evaluate("""
                (query) => {
                    const body = document.body;
                    const text = body.innerText || body.textContent || '';
                    return text.toLowerCase().includes(query.toLowerCase());
                }
            """, query)

            if content:
                return ActionResult(
                    success=True,
                    extracted_content=f"Found '{query}' on page",
                    long_term_memory=f"Searched for '{query}' - found",
                )
            return ActionResult(
                success=True,
                extracted_content=f"'{query}' not found on page",
                long_term_memory=f"Searched for '{query}' - not found",
            )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Read content from a file",
        param_model=ReadFileParams,
    )
    async def read_file(params: ReadFileParams) -> ActionResult:
        """读取文件内容"""
        try:
            path = Path(params.path)
            if not path.exists():
                return ActionResult(success=False, error=f"File not found: {params.path}")

            content = path.read_text(encoding="utf-8")
            content_preview = content[:2000] if len(content) > 2000 else content

            return ActionResult(
                success=True,
                extracted_content=content_preview,
                long_term_memory=f"Read file: {params.path}",
            )
        except Exception as e:
            logger.error(f"Read file failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Write content to a file",
        param_model=WriteFileParams,
    )
    async def write_file(params: WriteFileParams) -> ActionResult:
        """写入文件内容"""
        try:
            path = Path(params.path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(params.content, encoding="utf-8")

            return ActionResult(
                success=True,
                extracted_content=f"Wrote {len(params.content)} chars to {params.path}",
                long_term_memory=f"Wrote file: {params.path}",
            )
        except Exception as e:
            logger.error(f"Write file failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Take a screenshot of the current page",
    )
    async def screenshot() -> ActionResult:
        """截图"""
        try:
            page = browser_session.page
            if not page:
                return ActionResult(success=False, error="浏览器未启动")

            screenshot_bytes = await page.screenshot(type="png")

            import base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

            return ActionResult(
                success=True,
                extracted_content="Screenshot captured",
                long_term_memory="Captured screenshot",
                images=[{
                    "type": "image/png",
                    "data": screenshot_base64,
                }],
            )
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return ActionResult(success=False, error=str(e))

    @registry.action(
        "Wait for a specified number of seconds",
    )
    async def wait(seconds: int = 3) -> ActionResult:
        """等待"""
        actual_seconds = min(max(seconds, 0), 30)
        await asyncio.sleep(actual_seconds)
        return ActionResult(
            extracted_content=f"Waited for {seconds} seconds",
            long_term_memory=f"Waited for {seconds} seconds",
        )

    @registry.action(
        "Complete the task with a message",
        terminates_sequence=True,
    )
    async def done(text: str = "", success: bool = True) -> ActionResult:
        """完成任务"""
        return ActionResult(
            is_done=True,
            success=success,
            extracted_content=text,
            long_term_memory=f"Task completed: {success} - {text[:100]}",
        )

    return registry


class BrowserTools:
    """浏览器工具类"""

    def __init__(self, browser_session: Any):
        """
        初始化浏览器工具
        
        Args:
            browser_session: 浏览器会话对象
        """
        self.browser_session = browser_session
        self.registry = create_browser_tools(browser_session)

    def get_action_schemas(self) -> dict[str, dict]:
        """获取所有动作的 Schema"""
        return self.registry.get_action_schemas()

    def get_action_descriptions(self) -> dict[str, str]:
        """获取所有动作的描述"""
        return self.registry.get_action_descriptions()

    async def execute(self, action_name: str, params: dict | None = None) -> ActionResult:
        """执行动作"""
        return await self.registry.execute_action(action_name, params)
