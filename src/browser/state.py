"""
PyAgent 浏览器自动化模块 - 状态管理系统

提供浏览器状态捕获、存储、恢复和差异检测功能。
参考 browser-use 项目的状态管理设计。
"""

import logging
from datetime import datetime
from difflib import SequenceMatcher
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PageLoadState(str, Enum):
    """页面加载状态枚举"""
    LOADING = "loading"
    DOM_CONTENT_LOADED = "dom_content_loaded"
    LOAD = "load"
    NETWORK_IDLE = "network_idle"
    ERROR = "error"


class DOMElement(BaseModel):
    """DOM元素状态"""
    element_id: str
    tag_name: str
    text: str = ""
    attributes: dict[str, str] = Field(default_factory=dict)
    bounding_box: dict[str, float] = Field(default_factory=dict)
    is_visible: bool = True
    is_clickable: bool = False
    is_input: bool = False
    xpath: str = ""
    css_selector: str = ""

    def to_llm_text(self, include_attributes: bool = True) -> str:
        """
        生成LLM友好的文本表示

        Args:
            include_attributes: 是否包含属性信息

        Returns:
            str: LLM友好的文本
        """
        parts = [f"[{self.element_id}] <{self.tag_name}>"]

        if self.text:
            text_preview = self.text[:100].replace("\n", " ").strip()
            parts.append(f' text="{text_preview}"')

        if include_attributes and self.attributes:
            important_attrs = ["id", "class", "name", "type", "placeholder", "href", "src"]
            attrs_str = " ".join(
                f'{k}="{v}"'
                for k, v in self.attributes.items()
                if k in important_attrs and v
            )
            if attrs_str:
                parts.append(f" {attrs_str}")

        if self.is_clickable:
            parts.append(" [clickable]")
        if self.is_input:
            parts.append(" [input]")

        return "".join(parts)


class TabState(BaseModel):
    """标签页状态"""
    tab_id: str
    url: str = ""
    title: str = ""
    is_active: bool = False
    load_state: PageLoadState = PageLoadState.LOAD
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "tab_id": self.tab_id,
            "url": self.url,
            "title": self.title,
            "is_active": self.is_active,
            "load_state": self.load_state.value,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TabState":
        """从字典创建"""
        return cls(
            tab_id=data["tab_id"],
            url=data.get("url", ""),
            title=data.get("title", ""),
            is_active=data.get("is_active", False),
            load_state=PageLoadState(data.get("load_state", "load")),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            last_updated=datetime.fromisoformat(data["last_updated"]) if "last_updated" in data else datetime.now(),
        )


class DOMState(BaseModel):
    """DOM状态"""
    elements: list[DOMElement] = Field(default_factory=list)
    selector_map: dict[str, str] = Field(default_factory=dict)
    clickable_count: int = 0
    input_count: int = 0
    captured_at: datetime = Field(default_factory=datetime.now)

    def get_element_by_id(self, element_id: str) -> DOMElement | None:
        """通过ID获取元素"""
        for elem in self.elements:
            if elem.element_id == element_id:
                return elem
        return None

    def get_clickable_elements(self) -> list[DOMElement]:
        """获取所有可点击元素"""
        return [elem for elem in self.elements if elem.is_clickable]

    def get_input_elements(self) -> list[DOMElement]:
        """获取所有输入元素"""
        return [elem for elem in self.elements if elem.is_input]

    def to_llm_text(
        self,
        max_elements: int = 100,
        include_clickable_only: bool = False
    ) -> str:
        """
        生成LLM友好的文本表示

        Args:
            max_elements: 最大元素数量
            include_clickable_only: 是否只包含可点击元素

        Returns:
            str: LLM友好的DOM文本
        """
        elements = self.elements
        if include_clickable_only:
            elements = self.get_clickable_elements()

        elements = elements[:max_elements]

        lines = [
            f"[DOM State] {len(elements)} elements ({self.clickable_count} clickable, {self.input_count} inputs)",
            "",
        ]

        for elem in elements:
            lines.append(elem.to_llm_text())

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "elements": [elem.model_dump() for elem in self.elements],
            "selector_map": self.selector_map,
            "clickable_count": self.clickable_count,
            "input_count": self.input_count,
            "captured_at": self.captured_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DOMState":
        """从字典创建"""
        elements = [DOMElement(**elem) for elem in data.get("elements", [])]
        clickable_count = sum(1 for e in elements if e.is_clickable)
        input_count = sum(1 for e in elements if e.is_input)

        return cls(
            elements=elements,
            selector_map=data.get("selector_map", {}),
            clickable_count=data.get("clickable_count", clickable_count),
            input_count=data.get("input_count", input_count),
            captured_at=datetime.fromisoformat(data["captured_at"]) if "captured_at" in data else datetime.now(),
        )


class BrowserState(BaseModel):
    """浏览器状态"""
    url: str = ""
    title: str = ""
    tabs: list[TabState] = Field(default_factory=list)
    active_tab_id: str | None = None
    dom_state: DOMState | None = None
    screenshot: str | None = None
    scroll_position: dict[str, int] = Field(default_factory=lambda: {"x": 0, "y": 0})
    viewport_size: dict[str, int] = Field(default_factory=lambda: {"width": 1920, "height": 1080})
    captured_at: datetime = Field(default_factory=datetime.now)

    def get_active_tab(self) -> TabState | None:
        """获取当前活动标签页"""
        for tab in self.tabs:
            if tab.tab_id == self.active_tab_id:
                return tab
        return None

    def get_tab_by_id(self, tab_id: str) -> TabState | None:
        """通过ID获取标签页"""
        for tab in self.tabs:
            if tab.tab_id == tab_id:
                return tab
        return None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "url": self.url,
            "title": self.title,
            "tabs": [tab.to_dict() for tab in self.tabs],
            "active_tab_id": self.active_tab_id,
            "dom_state": self.dom_state.to_dict() if self.dom_state else None,
            "screenshot": self.screenshot,
            "scroll_position": self.scroll_position,
            "viewport_size": self.viewport_size,
            "captured_at": self.captured_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BrowserState":
        """从字典创建"""
        tabs = [TabState.from_dict(tab) for tab in data.get("tabs", [])]
        dom_state = DOMState.from_dict(data["dom_state"]) if data.get("dom_state") else None

        return cls(
            url=data.get("url", ""),
            title=data.get("title", ""),
            tabs=tabs,
            active_tab_id=data.get("active_tab_id"),
            dom_state=dom_state,
            screenshot=data.get("screenshot"),
            scroll_position=data.get("scroll_position", {"x": 0, "y": 0}),
            viewport_size=data.get("viewport_size", {"width": 1920, "height": 1080}),
            captured_at=datetime.fromisoformat(data["captured_at"]) if "captured_at" in data else datetime.now(),
        )

    def to_llm_text(self, include_screenshot_info: bool = True) -> str:
        """
        生成LLM友好的文本表示

        Args:
            include_screenshot_info: 是否包含截图信息

        Returns:
            str: LLM友好的状态文本
        """
        lines = [
            "[Browser State]",
            f"URL: {self.url}",
            f"Title: {self.title}",
            f"Tabs: {len(self.tabs)} (active: {self.active_tab_id})",
            f"Viewport: {self.viewport_size['width']}x{self.viewport_size['height']}",
            f"Scroll: ({self.scroll_position['x']}, {self.scroll_position['y']})",
        ]

        if include_screenshot_info and self.screenshot:
            lines.append("Screenshot: available")

        if self.dom_state:
            lines.append("")
            lines.append(self.dom_state.to_llm_text())

        return "\n".join(lines)


class StateDiff(BaseModel):
    """状态差异"""
    url_changed: bool = False
    old_url: str = ""
    new_url: str = ""
    title_changed: bool = False
    old_title: str = ""
    new_title: str = ""
    tabs_added: list[str] = Field(default_factory=list)
    tabs_removed: list[str] = Field(default_factory=list)
    tabs_changed: list[str] = Field(default_factory=list)
    dom_elements_added: int = 0
    dom_elements_removed: int = 0
    dom_elements_changed: int = 0
    dom_similarity: float = 1.0
    has_screenshot_change: bool = False

    @property
    def has_changes(self) -> bool:
        """是否有变化"""
        return (
            self.url_changed
            or self.title_changed
            or len(self.tabs_added) > 0
            or len(self.tabs_removed) > 0
            or len(self.tabs_changed) > 0
            or self.dom_elements_added > 0
            or self.dom_elements_removed > 0
            or self.dom_elements_changed > 0
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "url_changed": self.url_changed,
            "old_url": self.old_url,
            "new_url": self.new_url,
            "title_changed": self.title_changed,
            "old_title": self.old_title,
            "new_title": self.new_title,
            "tabs_added": self.tabs_added,
            "tabs_removed": self.tabs_removed,
            "tabs_changed": self.tabs_changed,
            "dom_elements_added": self.dom_elements_added,
            "dom_elements_removed": self.dom_elements_removed,
            "dom_elements_changed": self.dom_elements_changed,
            "dom_similarity": self.dom_similarity,
            "has_screenshot_change": self.has_screenshot_change,
        }

    def to_summary(self) -> str:
        """生成差异摘要"""
        changes = []

        if self.url_changed:
            changes.append(f"URL: {self.old_url} -> {self.new_url}")
        if self.title_changed:
            changes.append(f"Title: {self.old_title} -> {self.new_title}")
        if self.tabs_added:
            changes.append(f"Tabs added: {len(self.tabs_added)}")
        if self.tabs_removed:
            changes.append(f"Tabs removed: {len(self.tabs_removed)}")
        if self.tabs_changed:
            changes.append(f"Tabs changed: {len(self.tabs_changed)}")
        if self.dom_elements_added or self.dom_elements_removed or self.dom_elements_changed:
            changes.append(
                f"DOM: +{self.dom_elements_added} -{self.dom_elements_removed} ~{self.dom_elements_changed} (similarity: {self.dom_similarity:.2%})"
            )

        if not changes:
            return "No changes detected"

        return "; ".join(changes)


class BrowserStateHistory(BaseModel):
    """浏览器状态历史记录"""
    states: list[BrowserState] = Field(default_factory=list)
    max_history: int = 50
    current_index: int = -1

    def add_state(self, state: BrowserState) -> None:
        """
        添加状态到历史记录

        Args:
            state: 浏览器状态
        """
        if self.current_index < len(self.states) - 1:
            self.states = self.states[: self.current_index + 1]

        self.states.append(state)

        if len(self.states) > self.max_history:
            self.states = self.states[-self.max_history :]

        self.current_index = len(self.states) - 1

        logger.debug(f"State added to history, total: {len(self.states)}")

    def get_current_state(self) -> BrowserState | None:
        """获取当前状态"""
        if 0 <= self.current_index < len(self.states):
            return self.states[self.current_index]
        return None

    def get_previous_state(self) -> BrowserState | None:
        """获取上一个状态"""
        if self.current_index > 0:
            return self.states[self.current_index - 1]
        return None

    def get_next_state(self) -> BrowserState | None:
        """获取下一个状态"""
        if self.current_index < len(self.states) - 1:
            return self.states[self.current_index + 1]
        return None

    def go_back(self) -> BrowserState | None:
        """回退到上一个状态"""
        if self.current_index > 0:
            self.current_index -= 1
            return self.states[self.current_index]
        return None

    def go_forward(self) -> BrowserState | None:
        """前进到下一个状态"""
        if self.current_index < len(self.states) - 1:
            self.current_index += 1
            return self.states[self.current_index]
        return None

    def can_go_back(self) -> bool:
        """是否可以回退"""
        return self.current_index > 0

    def can_go_forward(self) -> bool:
        """是否可以前进"""
        return self.current_index < len(self.states) - 1

    def get_state_at(self, index: int) -> BrowserState | None:
        """
        获取指定索引的状态

        Args:
            index: 状态索引

        Returns:
            BrowserState | None: 状态或None
        """
        if 0 <= index < len(self.states):
            return self.states[index]
        return None

    def clear(self) -> None:
        """清空历史记录"""
        self.states.clear()
        self.current_index = -1

    def get_history_length(self) -> int:
        """获取历史记录长度"""
        return len(self.states)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "states": [state.to_dict() for state in self.states],
            "max_history": self.max_history,
            "current_index": self.current_index,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BrowserStateHistory":
        """从字典创建"""
        states = [BrowserState.from_dict(s) for s in data.get("states", [])]
        return cls(
            states=states,
            max_history=data.get("max_history", 50),
            current_index=data.get("current_index", -1),
        )


class StateManager:
    """状态管理器"""

    def __init__(self, controller, max_history: int = 50):
        """
        初始化状态管理器

        Args:
            controller: BrowserController实例
            max_history: 最大历史记录数
        """
        self._controller = controller
        self._history = BrowserStateHistory(max_history=max_history)
        self._current_state: BrowserState | None = None

    @property
    def current_state(self) -> BrowserState | None:
        return self._current_state

    @property
    def history(self) -> BrowserStateHistory:
        return self._history

    async def capture_state(
        self,
        include_screenshot: bool = False,
        include_dom: bool = True
    ) -> BrowserState:
        """
        捕获当前浏览器状态

        Args:
            include_screenshot: 是否包含截图
            include_dom: 是否包含DOM状态

        Returns:
            BrowserState: 捕获的状态
        """
        if not self._controller.is_launched or not self._controller.page:
            raise RuntimeError("浏览器未启动")

        try:
            page = self._controller.page

            url = page.url
            title = await page.title()

            scroll_position = await page.evaluate(
                "() => ({ x: window.scrollX, y: window.scrollY })"
            )

            viewport = page.viewport_size or {"width": 1920, "height": 1080}

            tabs = []
            active_tab_id = None
            if hasattr(self._controller, "_tab_manager") and self._controller._tab_manager:
                tab_list = await self._controller._tab_manager.get_tabs()
                tabs = [
                    TabState(
                        tab_id=tab.tab_id,
                        url=tab.url,
                        title=tab.title,
                        is_active=tab.is_active,
                    )
                    for tab in tab_list
                ]
                active_tab = await self._controller._tab_manager.get_active_tab()
                if active_tab:
                    active_tab_id = active_tab.tab_id
            else:
                tab_id = "default"
                tabs.append(
                    TabState(
                        tab_id=tab_id,
                        url=url,
                        title=title,
                        is_active=True,
                    )
                )
                active_tab_id = tab_id

            dom_state = None
            if include_dom:
                dom_state = await self._capture_dom_state()

            screenshot = None
            if include_screenshot:
                screenshot = await self._controller.take_screenshot(return_base64=True)

            state = BrowserState(
                url=url,
                title=title,
                tabs=tabs,
                active_tab_id=active_tab_id,
                dom_state=dom_state,
                screenshot=screenshot,
                scroll_position=scroll_position,
                viewport_size=viewport,
            )

            self._current_state = state
            self._history.add_state(state)

            logger.info(f"State captured: {url}")

            return state

        except Exception as e:
            logger.error(f"Capture state failed: {e}")
            raise

    async def _capture_dom_state(self) -> DOMState:
        """捕获DOM状态"""
        if not self._controller.page:
            raise RuntimeError("浏览器页面未初始化")

        page = self._controller.page

        script = """
        () => {
            const elements = [];
            const selectorMap = {};
            let elementId = 0;

            function isVisible(element) {
                if (!element) return false;
                const style = window.getComputedStyle(element);
                return style.display !== 'none' &&
                       style.visibility !== 'hidden' &&
                       style.opacity !== '0';
            }

            function isClickable(element) {
                if (!element) return false;
                const tagName = element.tagName.toLowerCase();
                const clickableTags = ['a', 'button', 'input', 'select', 'textarea', 'label'];
                if (clickableTags.includes(tagName)) return true;
                if (element.onclick) return true;
                if (element.getAttribute('role') === 'button') return true;
                const style = window.getComputedStyle(element);
                return style.cursor === 'pointer';
            }

            function isInputElement(element) {
                if (!element) return false;
                const tagName = element.tagName.toLowerCase();
                const inputTags = ['input', 'textarea', 'select'];
                if (!inputTags.includes(tagName)) return false;
                if (tagName === 'input') {
                    const type = element.getAttribute('type') || 'text';
                    const validTypes = ['text', 'password', 'email', 'number', 'tel', 'url', 'search', 'date'];
                    return validTypes.includes(type);
                }
                return true;
            }

            function getAttributes(element) {
                const attrs = {};
                for (const attr of element.attributes) {
                    attrs[attr.name] = attr.value;
                }
                return attrs;
            }

            function getBoundingBox(element) {
                const rect = element.getBoundingClientRect();
                return {
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height
                };
            }

            function getXPath(element) {
                if (element.id) return `//*[@id="${element.id}"]`;
                const parts = [];
                let current = element;
                while (current && current.nodeType === Node.ELEMENT_NODE) {
                    let index = 1;
                    let sibling = current.previousSibling;
                    while (sibling) {
                        if (sibling.nodeType === Node.ELEMENT_NODE &&
                            sibling.tagName === current.tagName) {
                            index++;
                        }
                        sibling = sibling.previousSibling;
                    }
                    const tagName = current.tagName.toLowerCase();
                    parts.unshift(`${tagName}[${index}]`);
                    current = current.parentNode;
                }
                return '/' + parts.join('/');
            }

            function getCssSelector(element) {
                if (element.id) return `#${element.id}`;
                const parts = [];
                let current = element;
                while (current && current.nodeType === Node.ELEMENT_NODE) {
                    let selector = current.tagName.toLowerCase();
                    if (current.className && typeof current.className === 'string') {
                        const classes = current.className.trim().split(/\\s+/);
                        if (classes.length > 0 && classes[0]) {
                            selector += '.' + classes.join('.');
                        }
                    }
                    parts.unshift(selector);
                    current = current.parentNode;
                    if (parts.length >= 3) break;
                }
                return parts.join(' > ');
            }

            function processElement(element) {
                if (!isVisible(element)) return null;

                const elemId = 'elem_' + (elementId++);
                const tagName = element.tagName.toLowerCase();
                const text = (element.innerText || element.textContent || '').substring(0, 100);
                const clickable = isClickable(element);
                const input = isInputElement(element);

                const elemData = {
                    element_id: elemId,
                    tag_name: tagName,
                    text: text,
                    attributes: getAttributes(element),
                    bounding_box: getBoundingBox(element),
                    is_visible: true,
                    is_clickable: clickable,
                    is_input: input,
                    xpath: getXPath(element),
                    css_selector: getCssSelector(element)
                };

                elements.push(elemData);

                if (clickable || input) {
                    selectorMap[elemId] = elemData.xpath || elemData.css_selector;
                }

                for (const child of element.children) {
                    processElement(child);
                }
            }

            const body = document.body;
            for (const child of body.children) {
                processElement(child);
            }

            return { elements, selectorMap };
        }
        """

        result = await page.evaluate(script)

        elements = [DOMElement(**elem) for elem in result["elements"]]
        clickable_count = sum(1 for e in elements if e.is_clickable)
        input_count = sum(1 for e in elements if e.is_input)

        return DOMState(
            elements=elements,
            selector_map=result["selectorMap"],
            clickable_count=clickable_count,
            input_count=input_count,
        )

    def compare_states(
        self,
        state1: BrowserState,
        state2: BrowserState
    ) -> StateDiff:
        """
        比较两个状态的差异

        Args:
            state1: 旧状态
            state2: 新状态

        Returns:
            StateDiff: 状态差异
        """
        diff = StateDiff()

        if state1.url != state2.url:
            diff.url_changed = True
            diff.old_url = state1.url
            diff.new_url = state2.url

        if state1.title != state2.title:
            diff.title_changed = True
            diff.old_title = state1.title
            diff.new_title = state2.title

        tabs1_ids = {tab.tab_id for tab in state1.tabs}
        tabs2_ids = {tab.tab_id for tab in state2.tabs}

        diff.tabs_added = list(tabs2_ids - tabs1_ids)
        diff.tabs_removed = list(tabs1_ids - tabs2_ids)

        common_tabs = tabs1_ids & tabs2_ids
        for tab_id in common_tabs:
            tab1 = state1.get_tab_by_id(tab_id)
            tab2 = state2.get_tab_by_id(tab_id)
            if tab1 and tab2 and (tab1.url != tab2.url or tab1.title != tab2.title):
                diff.tabs_changed.append(tab_id)

        if state1.dom_state and state2.dom_state:
            dom_diff = self._compare_dom_states(state1.dom_state, state2.dom_state)
            diff.dom_elements_added = dom_diff["added"]
            diff.dom_elements_removed = dom_diff["removed"]
            diff.dom_elements_changed = dom_diff["changed"]
            diff.dom_similarity = dom_diff["similarity"]

        if (state1.screenshot is None) != (state2.screenshot is None):
            diff.has_screenshot_change = True
        elif state1.screenshot and state2.screenshot:
            diff.has_screenshot_change = state1.screenshot != state2.screenshot

        return diff

    def _compare_dom_states(
        self,
        dom1: DOMState,
        dom2: DOMState
    ) -> dict[str, Any]:
        """
        比较两个DOM状态

        Args:
            dom1: 旧DOM状态
            dom2: 新DOM状态

        Returns:
            dict: 差异信息
        """
        elements1 = {elem.element_id: elem for elem in dom1.elements}
        elements2 = {elem.element_id: elem for elem in dom2.elements}

        ids1 = set(elements1.keys())
        ids2 = set(elements2.keys())

        added = len(ids2 - ids1)
        removed = len(ids1 - ids2)

        changed = 0
        common_ids = ids1 & ids2
        for elem_id in common_ids:
            elem1 = elements1[elem_id]
            elem2 = elements2[elem_id]
            if (
                elem1.text != elem2.text
                or elem1.attributes != elem2.attributes
                or elem1.is_visible != elem2.is_visible
            ):
                changed += 1

        text1 = " ".join(elem.text for elem in dom1.elements[:50])
        text2 = " ".join(elem.text for elem in dom2.elements[:50])
        similarity = SequenceMatcher(None, text1, text2).ratio()

        return {
            "added": added,
            "removed": removed,
            "changed": changed,
            "similarity": similarity,
        }

    async def restore_state(
        self,
        state: BrowserState,
        restore_url: bool = True,
        restore_scroll: bool = True
    ) -> bool:
        """
        恢复浏览器状态

        Args:
            state: 要恢复的状态
            restore_url: 是否恢复URL
            restore_scroll: 是否恢复滚动位置

        Returns:
            bool: 是否成功恢复
        """
        if not self._controller.is_launched or not self._controller.page:
            raise RuntimeError("浏览器未启动")

        try:
            page = self._controller.page

            if restore_url and state.url and page.url != state.url:
                await self._controller.navigate(state.url)

            if restore_scroll and state.scroll_position:
                await page.evaluate(
                    f"window.scrollTo({state.scroll_position['x']}, {state.scroll_position['y']})"
                )

            logger.info(f"State restored: {state.url}")
            return True

        except Exception as e:
            logger.error(f"Restore state failed: {e}")
            return False

    def get_state_diff_from_last(self) -> StateDiff | None:
        """
        获取与上一个状态的差异

        Returns:
            StateDiff | None: 状态差异或None
        """
        current = self._history.get_current_state()
        previous = self._history.get_previous_state()

        if current and previous:
            return self.compare_states(previous, current)

        return None

    def find_state_by_url(self, url: str) -> BrowserState | None:
        """
        通过URL查找状态

        Args:
            url: 目标URL

        Returns:
            BrowserState | None: 找到的状态或None
        """
        for state in reversed(self._history.states):
            if state.url == url:
                return state
        return None

    def find_state_by_title(self, title: str) -> BrowserState | None:
        """
        通过标题查找状态

        Args:
            title: 目标标题

        Returns:
            BrowserState | None: 找到的状态或None
        """
        for state in reversed(self._history.states):
            if title in state.title:
                return state
        return None

    def get_url_history(self) -> list[str]:
        """
        获取URL历史记录

        Returns:
            list[str]: URL列表
        """
        return [state.url for state in self._history.states if state.url]

    def export_history(self) -> dict[str, Any]:
        """
        导出历史记录

        Returns:
            dict: 历史记录数据
        """
        return self._history.to_dict()

    def import_history(self, data: dict[str, Any]) -> None:
        """
        导入历史记录

        Args:
            data: 历史记录数据
        """
        self._history = BrowserStateHistory.from_dict(data)
        self._current_state = self._history.get_current_state()
        logger.info(f"History imported: {len(self._history.states)} states")

    def clear_history(self) -> None:
        """清空历史记录"""
        self._history.clear()
        self._current_state = None
        logger.info("History cleared")
