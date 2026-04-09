"""
PyAgent 浏览器自动化模块 - 动作执行器

提供浏览器动作执行功能，包括点击、输入、滚动等。
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """动作类型"""
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    TYPE = "type"
    FILL = "fill"
    CLEAR = "clear"
    SELECT = "select"
    SCROLL = "scroll"
    HOVER = "hover"
    DRAG = "drag"
    UPLOAD = "upload"
    PRESS = "press"
    WAIT = "wait"
    FOCUS = "focus"
    BLUR = "blur"
    CHECK = "check"
    UNCHECK = "uncheck"


@dataclass
class ActionResult:
    """动作执行结果"""
    success: bool
    action_type: str
    message: str = ""
    error: str = ""
    data: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "action_type": self.action_type,
            "message": self.message,
            "error": self.error,
            "data": self.data,
            "metadata": self.metadata
        }


class ActionExecutor:
    """动作执行器"""

    def __init__(self, controller, dom_serializer=None):
        """
        初始化动作执行器

        Args:
            controller: BrowserController实例
            dom_serializer: DOMSerializer实例（可选）
        """
        self._controller = controller
        self._dom_serializer = dom_serializer

    @property
    def page(self):
        return self._controller.page

    async def click(
        self,
        element_id: str | None = None,
        selector: str | None = None,
        xpath: str | None = None,
        button: str = "left",
        click_count: int = 1,
        delay: int = 0,
        force: bool = False,
        timeout: int | None = None
    ) -> ActionResult:
        """
        点击元素

        Args:
            element_id: 元素ID（通过DOMSerializer获取）
            selector: CSS选择器
            xpath: XPath表达式
            button: 鼠标按钮 (left/right/middle)
            click_count: 点击次数
            delay: 点击延迟（毫秒）
            force: 是否强制点击（忽略可见性检查）
            timeout: 超时时间

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.CLICK.value,
                error="浏览器未启动"
            )

        try:
            locator = self._get_locator(element_id, selector, xpath)
            if not locator:
                return ActionResult(
                    success=False,
                    action_type=ActionType.CLICK.value,
                    error="未找到元素"
                )

            options = {
                "button": button,
                "clickCount": click_count,
                "delay": delay,
                "force": force
            }
            if timeout:
                options["timeout"] = timeout

            await locator.click(**options)

            return ActionResult(
                success=True,
                action_type=ActionType.CLICK.value,
                message="成功点击元素"
            )

        except Exception as e:
            logger.error(f"点击失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.CLICK.value,
                error=str(e)
            )

    async def double_click(
        self,
        element_id: str | None = None,
        selector: str | None = None,
        xpath: str | None = None
    ) -> ActionResult:
        """
        双击元素

        Returns:
            ActionResult: 执行结果
        """
        return await self.click(
            element_id=element_id,
            selector=selector,
            xpath=xpath,
            click_count=2
        )

    async def right_click(
        self,
        element_id: str | None = None,
        selector: str | None = None,
        xpath: str | None = None
    ) -> ActionResult:
        """
        右键点击元素

        Returns:
            ActionResult: 执行结果
        """
        return await self.click(
            element_id=element_id,
            selector=selector,
            xpath=xpath,
            button="right"
        )

    async def type_text(
        self,
        text: str,
        element_id: str | None = None,
        selector: str | None = None,
        xpath: str | None = None,
        delay: int = 0,
        clear_first: bool = False,
        timeout: int | None = None
    ) -> ActionResult:
        """
        输入文本

        Args:
            text: 要输入的文本
            element_id: 元素ID
            selector: CSS选择器
            xpath: XPath表达式
            delay: 输入延迟（毫秒）
            clear_first: 是否先清空
            timeout: 超时时间

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.TYPE.value,
                error="浏览器未启动"
            )

        try:
            locator = self._get_locator(element_id, selector, xpath)
            if not locator:
                return ActionResult(
                    success=False,
                    action_type=ActionType.TYPE.value,
                    error="未找到元素"
                )

            options = {"delay": delay}
            if timeout:
                options["timeout"] = timeout

            if clear_first:
                await locator.clear()

            await locator.type(text, **options)

            return ActionResult(
                success=True,
                action_type=ActionType.TYPE.value,
                message=f"成功输入文本: {text[:50]}..."
            )

        except Exception as e:
            logger.error(f"输入文本失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.TYPE.value,
                error=str(e)
            )

    async def fill(
        self,
        value: str,
        element_id: str | None = None,
        selector: str | None = None,
        xpath: str | None = None,
        timeout: int | None = None
    ) -> ActionResult:
        """
        填充表单字段（会清空原有内容）

        Args:
            value: 要填充的值
            element_id: 元素ID
            selector: CSS选择器
            xpath: XPath表达式
            timeout: 超时时间

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.FILL.value,
                error="浏览器未启动"
            )

        try:
            locator = self._get_locator(element_id, selector, xpath)
            if not locator:
                return ActionResult(
                    success=False,
                    action_type=ActionType.FILL.value,
                    error="未找到元素"
                )

            options = {}
            if timeout:
                options["timeout"] = timeout

            await locator.fill(value, **options)

            return ActionResult(
                success=True,
                action_type=ActionType.FILL.value,
                message="成功填充值"
            )

        except Exception as e:
            logger.error(f"填充失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.FILL.value,
                error=str(e)
            )

    async def clear(
        self,
        element_id: str | None = None,
        selector: str | None = None,
        xpath: str | None = None
    ) -> ActionResult:
        """
        清空输入框

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.CLEAR.value,
                error="浏览器未启动"
            )

        try:
            locator = self._get_locator(element_id, selector, xpath)
            if not locator:
                return ActionResult(
                    success=False,
                    action_type=ActionType.CLEAR.value,
                    error="未找到元素"
                )

            await locator.clear()

            return ActionResult(
                success=True,
                action_type=ActionType.CLEAR.value,
                message="成功清空"
            )

        except Exception as e:
            logger.error(f"清空失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.CLEAR.value,
                error=str(e)
            )

    async def select_option(
        self,
        value: str | list[str] | None = None,
        label: str | list[str] | None = None,
        index: int | list[int] | None = None,
        element_id: str | None = None,
        selector: str | None = None,
        xpath: str | None = None
    ) -> ActionResult:
        """
        选择下拉选项

        Args:
            value: 选项值
            label: 选项文本
            index: 选项索引
            element_id: 元素ID
            selector: CSS选择器
            xpath: XPath表达式

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.SELECT.value,
                error="浏览器未启动"
            )

        try:
            locator = self._get_locator(element_id, selector, xpath)
            if not locator:
                return ActionResult(
                    success=False,
                    action_type=ActionType.SELECT.value,
                    error="未找到元素"
                )

            if value is not None:
                await locator.select_option(value=value)
            elif label is not None:
                await locator.select_option(label=label)
            elif index is not None:
                await locator.select_option(index=index)
            else:
                return ActionResult(
                    success=False,
                    action_type=ActionType.SELECT.value,
                    error="必须提供value、label或index参数"
                )

            return ActionResult(
                success=True,
                action_type=ActionType.SELECT.value,
                message="成功选择选项"
            )

        except Exception as e:
            logger.error(f"选择选项失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.SELECT.value,
                error=str(e)
            )

    async def scroll(
        self,
        direction: str = "down",
        amount: int = 300,
        selector: str | None = None
    ) -> ActionResult:
        """
        滚动页面

        Args:
            direction: 滚动方向 (up/down/left/right)
            amount: 滚动量（像素）
            selector: 滚动特定元素（可选）

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.SCROLL.value,
                error="浏览器未启动"
            )

        try:
            scroll_map = {
                "up": (0, -amount),
                "down": (0, amount),
                "left": (-amount, 0),
                "right": (amount, 0)
            }

            x, y = scroll_map.get(direction, (0, amount))

            if selector:
                await self.page.locator(selector).evaluate(
                    f"el => el.scrollBy({x}, {y})"
                )
            else:
                await self.page.evaluate(f"window.scrollBy({x}, {y})")

            return ActionResult(
                success=True,
                action_type=ActionType.SCROLL.value,
                message=f"成功向{direction}滚动{amount}像素"
            )

        except Exception as e:
            logger.error(f"滚动失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.SCROLL.value,
                error=str(e)
            )

    async def scroll_to_element(
        self,
        element_id: str | None = None,
        selector: str | None = None,
        xpath: str | None = None
    ) -> ActionResult:
        """
        滚动到元素可见

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.SCROLL.value,
                error="浏览器未启动"
            )

        try:
            locator = self._get_locator(element_id, selector, xpath)
            if not locator:
                return ActionResult(
                    success=False,
                    action_type=ActionType.SCROLL.value,
                    error="未找到元素"
                )

            await locator.scroll_into_view_if_needed()

            return ActionResult(
                success=True,
                action_type=ActionType.SCROLL.value,
                message="成功滚动到元素"
            )

        except Exception as e:
            logger.error(f"滚动到元素失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.SCROLL.value,
                error=str(e)
            )

    async def hover(
        self,
        element_id: str | None = None,
        selector: str | None = None,
        xpath: str | None = None,
        modifiers: list[str] | None = None
    ) -> ActionResult:
        """
        悬停在元素上

        Args:
            element_id: 元素ID
            selector: CSS选择器
            xpath: XPath表达式
            modifiers: 修饰键 (Alt/Control/Meta/Shift)

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.HOVER.value,
                error="浏览器未启动"
            )

        try:
            locator = self._get_locator(element_id, selector, xpath)
            if not locator:
                return ActionResult(
                    success=False,
                    action_type=ActionType.HOVER.value,
                    error="未找到元素"
                )

            options = {}
            if modifiers:
                options["modifiers"] = modifiers

            await locator.hover(**options)

            return ActionResult(
                success=True,
                action_type=ActionType.HOVER.value,
                message="成功悬停"
            )

        except Exception as e:
            logger.error(f"悬停失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.HOVER.value,
                error=str(e)
            )

    async def drag_and_drop(
        self,
        source_id: str | None = None,
        source_selector: str | None = None,
        source_xpath: str | None = None,
        target_id: str | None = None,
        target_selector: str | None = None,
        target_xpath: str | None = None
    ) -> ActionResult:
        """
        拖拽元素

        Args:
            source_*: 源元素定位
            target_*: 目标元素定位

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.DRAG.value,
                error="浏览器未启动"
            )

        try:
            source_locator = self._get_locator(
                source_id, source_selector, source_xpath
            )
            target_locator = self._get_locator(
                target_id, target_selector, target_xpath
            )

            if not source_locator or not target_locator:
                return ActionResult(
                    success=False,
                    action_type=ActionType.DRAG.value,
                    error="未找到源元素或目标元素"
                )

            await source_locator.drag_to(target_locator)

            return ActionResult(
                success=True,
                action_type=ActionType.DRAG.value,
                message="成功拖拽"
            )

        except Exception as e:
            logger.error(f"拖拽失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.DRAG.value,
                error=str(e)
            )

    async def upload_file(
        self,
        file_path: str,
        element_id: str | None = None,
        selector: str | None = None,
        xpath: str | None = None
    ) -> ActionResult:
        """
        上传文件

        Args:
            file_path: 文件路径
            element_id: 元素ID
            selector: CSS选择器
            xpath: XPath表达式

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.UPLOAD.value,
                error="浏览器未启动"
            )

        try:
            path = Path(file_path)
            if not path.exists():
                return ActionResult(
                    success=False,
                    action_type=ActionType.UPLOAD.value,
                    error=f"文件不存在: {file_path}"
                )

            locator = self._get_locator(element_id, selector, xpath)
            if not locator:
                locator = self.page.locator('input[type="file"]')

            await locator.set_input_files(str(path.absolute()))

            return ActionResult(
                success=True,
                action_type=ActionType.UPLOAD.value,
                message=f"成功上传文件: {file_path}"
            )

        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.UPLOAD.value,
                error=str(e)
            )

    async def press_key(
        self,
        key: str,
        element_id: str | None = None,
        selector: str | None = None,
        xpath: str | None = None,
        delay: int = 0
    ) -> ActionResult:
        """
        按下键盘按键

        Args:
            key: 按键 (如 Enter, Tab, Escape, ArrowDown 等)
            element_id: 元素ID（可选，不传则在页面上按键）
            selector: CSS选择器
            xpath: XPath表达式
            delay: 延迟（毫秒）

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.PRESS.value,
                error="浏览器未启动"
            )

        try:
            if element_id or selector or xpath:
                locator = self._get_locator(element_id, selector, xpath)
                if locator:
                    await locator.press(key, delay=delay)
                else:
                    return ActionResult(
                        success=False,
                        action_type=ActionType.PRESS.value,
                        error="未找到元素"
                    )
            else:
                await self.page.keyboard.press(key, delay=delay)

            return ActionResult(
                success=True,
                action_type=ActionType.PRESS.value,
                message=f"成功按下按键: {key}"
            )

        except Exception as e:
            logger.error(f"按键失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.PRESS.value,
                error=str(e)
            )

    async def wait(
        self,
        timeout: int = 1000,
        selector: str | None = None,
        state: str = "visible"
    ) -> ActionResult:
        """
        等待

        Args:
            timeout: 超时时间（毫秒）
            selector: 等待元素选择器（可选）
            state: 等待状态 (visible/hidden/attached/detached)

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.WAIT.value,
                error="浏览器未启动"
            )

        try:
            if selector:
                await self.page.wait_for_selector(
                    selector,
                    timeout=timeout,
                    state=state
                )
            else:
                await self.page.wait_for_timeout(timeout)

            return ActionResult(
                success=True,
                action_type=ActionType.WAIT.value,
                message="等待完成"
            )

        except Exception as e:
            logger.error(f"等待失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.WAIT.value,
                error=str(e)
            )

    async def focus(
        self,
        element_id: str | None = None,
        selector: str | None = None,
        xpath: str | None = None
    ) -> ActionResult:
        """
        聚焦元素

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.FOCUS.value,
                error="浏览器未启动"
            )

        try:
            locator = self._get_locator(element_id, selector, xpath)
            if not locator:
                return ActionResult(
                    success=False,
                    action_type=ActionType.FOCUS.value,
                    error="未找到元素"
                )

            await locator.focus()

            return ActionResult(
                success=True,
                action_type=ActionType.FOCUS.value,
                message="成功聚焦"
            )

        except Exception as e:
            logger.error(f"聚焦失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.FOCUS.value,
                error=str(e)
            )

    async def blur(
        self,
        element_id: str | None = None,
        selector: str | None = None,
        xpath: str | None = None
    ) -> ActionResult:
        """
        取消聚焦

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.BLUR.value,
                error="浏览器未启动"
            )

        try:
            locator = self._get_locator(element_id, selector, xpath)
            if not locator:
                return ActionResult(
                    success=False,
                    action_type=ActionType.BLUR.value,
                    error="未找到元素"
                )

            await locator.evaluate("el => el.blur()")

            return ActionResult(
                success=True,
                action_type=ActionType.BLUR.value,
                message="成功取消聚焦"
            )

        except Exception as e:
            logger.error(f"取消聚焦失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.BLUR.value,
                error=str(e)
            )

    async def check(
        self,
        element_id: str | None = None,
        selector: str | None = None,
        xpath: str | None = None,
        force: bool = False
    ) -> ActionResult:
        """
        勾选复选框

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.CHECK.value,
                error="浏览器未启动"
            )

        try:
            locator = self._get_locator(element_id, selector, xpath)
            if not locator:
                return ActionResult(
                    success=False,
                    action_type=ActionType.CHECK.value,
                    error="未找到元素"
                )

            await locator.check(force=force)

            return ActionResult(
                success=True,
                action_type=ActionType.CHECK.value,
                message="成功勾选"
            )

        except Exception as e:
            logger.error(f"勾选失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.CHECK.value,
                error=str(e)
            )

    async def uncheck(
        self,
        element_id: str | None = None,
        selector: str | None = None,
        xpath: str | None = None,
        force: bool = False
    ) -> ActionResult:
        """
        取消勾选复选框

        Returns:
            ActionResult: 执行结果
        """
        if not self.page:
            return ActionResult(
                success=False,
                action_type=ActionType.UNCHECK.value,
                error="浏览器未启动"
            )

        try:
            locator = self._get_locator(element_id, selector, xpath)
            if not locator:
                return ActionResult(
                    success=False,
                    action_type=ActionType.UNCHECK.value,
                    error="未找到元素"
                )

            await locator.uncheck(force=force)

            return ActionResult(
                success=True,
                action_type=ActionType.UNCHECK.value,
                message="成功取消勾选"
            )

        except Exception as e:
            logger.error(f"取消勾选失败: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.UNCHECK.value,
                error=str(e)
            )

    def _get_locator(self, element_id: str | None, selector: str | None, xpath: str | None):
        """获取元素定位器"""
        if not self.page:
            return None

        if element_id:
            return self.page.locator(f'[data-element-id="{element_id}"]')
        if selector:
            return self.page.locator(selector)
        if xpath:
            return self.page.locator(f"xpath={xpath}")

        return None

    async def execute_action(
        self,
        action_type: str,
        **kwargs
    ) -> ActionResult:
        """
        执行动作（统一入口）

        Args:
            action_type: 动作类型
            **kwargs: 动作参数

        Returns:
            ActionResult: 执行结果
        """
        action_map = {
            ActionType.CLICK.value: self.click,
            ActionType.DOUBLE_CLICK.value: self.double_click,
            ActionType.RIGHT_CLICK.value: self.right_click,
            ActionType.TYPE.value: self.type_text,
            ActionType.FILL.value: self.fill,
            ActionType.CLEAR.value: self.clear,
            ActionType.SELECT.value: self.select_option,
            ActionType.SCROLL.value: self.scroll,
            ActionType.HOVER.value: self.hover,
            ActionType.DRAG.value: self.drag_and_drop,
            ActionType.UPLOAD.value: self.upload_file,
            ActionType.PRESS.value: self.press_key,
            ActionType.WAIT.value: self.wait,
            ActionType.FOCUS.value: self.focus,
            ActionType.BLUR.value: self.blur,
            ActionType.CHECK.value: self.check,
            ActionType.UNCHECK.value: self.uncheck
        }

        action_func = action_map.get(action_type)
        if not action_func:
            return ActionResult(
                success=False,
                action_type=action_type,
                error=f"未知动作类型: {action_type}"
            )

        return await action_func(**kwargs)
