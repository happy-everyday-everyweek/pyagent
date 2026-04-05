"""
PyAgent 浏览器自动化模块 - DOM序列化器

提供DOM元素序列化、提取和查询功能。
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DOMElement:
    """DOM元素数据类"""
    element_id: str
    tag_name: str
    text: str = ""
    attributes: dict[str, str] = field(default_factory=dict)
    bounding_box: dict[str, float] = field(default_factory=dict)
    is_visible: bool = True
    is_clickable: bool = False
    is_input: bool = False
    children: list["DOMElement"] = field(default_factory=list)
    xpath: str = ""
    css_selector: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "element_id": self.element_id,
            "tag_name": self.tag_name,
            "text": self.text,
            "attributes": self.attributes,
            "bounding_box": self.bounding_box,
            "is_visible": self.is_visible,
            "is_clickable": self.is_clickable,
            "is_input": self.is_input,
            "children": [c.to_dict() for c in self.children],
            "xpath": self.xpath,
            "css_selector": self.css_selector
        }


class DOMSerializer:
    """DOM序列化器"""

    CLICKABLE_TAGS = {
        "a", "button", "input", "select", "textarea",
        "label", "option", "optgroup"
    }

    INPUT_TAGS = {
        "input", "textarea", "select"
    }

    INPUT_TYPES = {
        "text", "password", "email", "number", "tel",
        "url", "search", "date", "datetime-local"
    }

    def __init__(self, controller):
        """
        初始化DOM序列化器

        Args:
            controller: BrowserController实例
        """
        self._controller = controller

    @property
    def page(self):
        return self._controller.page

    async def serialize_dom(
        self,
        include_hidden: bool = False,
        max_depth: int = 10
    ) -> list[DOMElement]:
        """
        序列化当前页面DOM

        Args:
            include_hidden: 是否包含隐藏元素
            max_depth: 最大递归深度

        Returns:
            list[DOMElement]: DOM元素列表
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")

        try:
            elements = await self._extract_elements(
                include_hidden=include_hidden,
                max_depth=max_depth
            )
            return elements
        except Exception as e:
            logger.error(f"序列化DOM失败: {e}")
            raise

    async def _extract_elements(
        self,
        include_hidden: bool,
        max_depth: int
    ) -> list[DOMElement]:
        """提取页面元素"""
        script = """
        (args) => {
            const { includeHidden, maxDepth } = args;
            const elements = [];
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

            function processElement(element, depth) {
                if (depth > maxDepth) return null;
                if (!includeHidden && !isVisible(element)) return null;

                const elementIdStr = 'elem_' + (elementId++);
                const tagName = element.tagName.toLowerCase();
                const text = element.innerText || element.textContent || '';
                const visible = isVisible(element);
                const clickable = isClickable(element);
                const input = isInputElement(element);

                const domElement = {
                    element_id: elementIdStr,
                    tag_name: tagName,
                    text: text.substring(0, 500),
                    attributes: getAttributes(element),
                    bounding_box: getBoundingBox(element),
                    is_visible: visible,
                    is_clickable: clickable,
                    is_input: input,
                    children: [],
                    xpath: getXPath(element),
                    css_selector: getCssSelector(element)
                };

                for (const child of element.children) {
                    const childElement = processElement(child, depth + 1);
                    if (childElement) {
                        domElement.children.push(childElement);
                    }
                }

                return domElement;
            }

            const body = document.body;
            for (const child of body.children) {
                const element = processElement(child, 0);
                if (element) {
                    elements.push(element);
                }
            }

            return elements;
        }
        """

        raw_elements = await self.page.evaluate(
            script,
            {"includeHidden": include_hidden, "maxDepth": max_depth}
        )

        return [self._parse_element(e) for e in raw_elements]

    def _parse_element(self, data: dict) -> DOMElement:
        """解析元素数据"""
        return DOMElement(
            element_id=data["element_id"],
            tag_name=data["tag_name"],
            text=data["text"],
            attributes=data["attributes"],
            bounding_box=data["bounding_box"],
            is_visible=data["is_visible"],
            is_clickable=data["is_clickable"],
            is_input=data["is_input"],
            children=[self._parse_element(c) for c in data.get("children", [])],
            xpath=data["xpath"],
            css_selector=data["css_selector"]
        )

    async def get_clickable_elements(
        self,
        include_hidden: bool = False
    ) -> list[DOMElement]:
        """
        获取所有可点击元素

        Args:
            include_hidden: 是否包含隐藏元素

        Returns:
            list[DOMElement]: 可点击元素列表
        """
        all_elements = await self.serialize_dom(include_hidden=include_hidden)
        return self._filter_elements(all_elements, lambda e: e.is_clickable)

    async def get_input_elements(
        self,
        include_hidden: bool = False
    ) -> list[DOMElement]:
        """
        获取所有输入元素

        Args:
            include_hidden: 是否包含隐藏元素

        Returns:
            list[DOMElement]: 输入元素列表
        """
        all_elements = await self.serialize_dom(include_hidden=include_hidden)
        return self._filter_elements(all_elements, lambda e: e.is_input)

    def _filter_elements(
        self,
        elements: list[DOMElement],
        predicate
    ) -> list[DOMElement]:
        """递归过滤元素"""
        result = []
        for elem in elements:
            if predicate(elem):
                result.append(elem)
            result.extend(self._filter_elements(elem.children, predicate))
        return result

    async def get_element_by_id(self, element_id: str) -> DOMElement | None:
        """
        通过元素ID获取元素

        Args:
            element_id: 元素ID

        Returns:
            DOMElement | None: 元素或None
        """
        all_elements = await self.serialize_dom()
        return self._find_element(all_elements, lambda e: e.element_id == element_id)

    async def get_elements_by_selector(
        self,
        selector: str,
        include_hidden: bool = False
    ) -> list[DOMElement]:
        """
        通过CSS选择器获取元素

        Args:
            selector: CSS选择器
            include_hidden: 是否包含隐藏元素

        Returns:
            list[DOMElement]: 元素列表
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")

        try:
            handles = await self.page.query_selector_all(selector)
            elements = []

            for i, handle in enumerate(handles):
                element = await self._element_handle_to_dom(handle, f"selector_{i}")
                if element and (include_hidden or element.is_visible):
                    elements.append(element)

            return elements
        except Exception as e:
            logger.error(f"获取元素失败: {e}")
            return []

    async def _element_handle_to_dom(
        self,
        handle,
        element_id: str
    ) -> DOMElement | None:
        """将ElementHandle转换为DOMElement"""
        try:
            tag_name = await handle.evaluate("el => el.tagName.toLowerCase()")
            text = await handle.evaluate("el => (el.innerText || el.textContent || '').substring(0, 500)")
            attributes = await handle.evaluate("""
                el => {
                    const attrs = {};
                    for (const attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }
            """)
            bounding_box = await handle.bounding_box() or {}
            is_visible = await handle.is_visible()

            return DOMElement(
                element_id=element_id,
                tag_name=tag_name,
                text=text,
                attributes=attributes,
                bounding_box=bounding_box,
                is_visible=is_visible,
                is_clickable=tag_name in self.CLICKABLE_TAGS,
                is_input=tag_name in self.INPUT_TAGS
            )
        except Exception:
            return None

    async def get_element_by_xpath(self, xpath: str) -> DOMElement | None:
        """
        通过XPath获取元素

        Args:
            xpath: XPath表达式

        Returns:
            DOMElement | None: 元素或None
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")

        try:
            handle = await self.page.locator(f"xpath={xpath}").first.element_handle()
            if handle:
                return await self._element_handle_to_dom(handle, f"xpath_{xpath}")
            return None
        except Exception as e:
            logger.error(f"获取元素失败: {e}")
            return None

    def _find_element(
        self,
        elements: list[DOMElement],
        predicate
    ) -> DOMElement | None:
        """递归查找元素"""
        for elem in elements:
            if predicate(elem):
                return elem
            found = self._find_element(elem.children, predicate)
            if found:
                return found
        return None

    async def extract_text(self) -> str:
        """
        提取页面文本内容

        Returns:
            str: 页面文本
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")

        try:
            text = await self.page.evaluate("""
                () => {
                    const body = document.body;
                    const walker = document.createTreeWalker(
                        body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );

                    const texts = [];
                    let node;
                    while (node = walker.nextNode()) {
                        const text = node.textContent.trim();
                        if (text) {
                            texts.push(text);
                        }
                    }

                    return texts.join('\\n');
                }
            """)
            return text
        except Exception as e:
            logger.error(f"提取文本失败: {e}")
            raise

    async def extract_links(self) -> list[dict[str, str]]:
        """
        提取页面所有链接

        Returns:
            list[dict[str, str]]: 链接列表，包含href和text
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")

        try:
            links = await self.page.evaluate("""
                () => {
                    const links = [];
                    const anchors = document.querySelectorAll('a[href]');

                    for (const anchor of anchors) {
                        links.push({
                            href: anchor.href,
                            text: (anchor.innerText || anchor.textContent || '').trim(),
                            title: anchor.title || '',
                            target: anchor.target || ''
                        });
                    }

                    return links;
                }
            """)
            return links
        except Exception as e:
            logger.error(f"提取链接失败: {e}")
            raise

    async def extract_images(self) -> list[dict[str, str]]:
        """
        提取页面所有图片

        Returns:
            list[dict[str, str]]: 图片列表
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")

        try:
            images = await self.page.evaluate("""
                () => {
                    const images = [];
                    const imgs = document.querySelectorAll('img');

                    for (const img of imgs) {
                        images.push({
                            src: img.src,
                            alt: img.alt || '',
                            title: img.title || '',
                            width: img.naturalWidth || img.width,
                            height: img.naturalHeight || img.height
                        });
                    }

                    return images;
                }
            """)
            return images
        except Exception as e:
            logger.error(f"提取图片失败: {e}")
            raise

    async def extract_forms(self) -> list[dict[str, Any]]:
        """
        提取页面所有表单

        Returns:
            list[dict[str, Any]]: 表单列表
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")

        try:
            forms = await self.page.evaluate("""
                () => {
                    const forms = [];
                    const formElements = document.querySelectorAll('form');

                    for (const form of formElements) {
                        const inputs = [];
                        const inputElements = form.querySelectorAll('input, select, textarea');

                        for (const input of inputElements) {
                            inputs.push({
                                type: input.type || input.tagName.toLowerCase(),
                                name: input.name || '',
                                id: input.id || '',
                                placeholder: input.placeholder || '',
                                value: input.value || '',
                                required: input.required
                            });
                        }

                        forms.push({
                            action: form.action || '',
                            method: form.method || 'GET',
                            id: form.id || '',
                            name: form.name || '',
                            inputs: inputs
                        });
                    }

                    return forms;
                }
            """)
            return forms
        except Exception as e:
            logger.error(f"提取表单失败: {e}")
            raise

    async def find_element_by_text(
        self,
        text: str,
        exact: bool = False
    ) -> DOMElement | None:
        """
        通过文本内容查找元素

        Args:
            text: 文本内容
            exact: 是否精确匹配

        Returns:
            DOMElement | None: 元素或None
        """
        all_elements = await self.serialize_dom()

        def matcher(elem: DOMElement) -> bool:
            if exact:
                return elem.text.strip() == text.strip()
            return text.lower() in elem.text.lower()

        return self._find_element(all_elements, matcher)

    async def get_element_at_point(
        self,
        x: float,
        y: float
    ) -> DOMElement | None:
        """
        获取指定坐标位置的元素

        Args:
            x: X坐标
            y: Y坐标

        Returns:
            DOMElement | None: 元素或None
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")

        try:
            handle = await self.page.evaluate_handle(
                f"document.elementFromPoint({x}, {y})"
            )

            if handle:
                return await self._element_handle_to_dom(handle, f"point_{x}_{y}")
            return None
        except Exception as e:
            logger.error(f"获取坐标元素失败: {e}")
            return None
