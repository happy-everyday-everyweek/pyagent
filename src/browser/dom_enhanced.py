"""
PyAgent 浏览器自动化模块 - 增强版 DOM 解析器

支持 CDP DOMSnapshot API、可访问性树解析、元素可见性检测和分页按钮检测。
参考 browser-use 项目的 DOM 解析设计实现。
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DOMElementEnhanced(BaseModel):
    """增强版 DOM 元素"""
    
    element_id: str
    tag_name: str
    text: str = ""
    attributes: dict[str, str] = Field(default_factory=dict)
    bounding_box: dict[str, float] = Field(default_factory=dict)
    is_visible: bool = True
    is_clickable: bool = False
    is_input: bool = False
    is_interactive: bool = False
    children: list["DOMElementEnhanced"] = Field(default_factory=list)
    xpath: str = ""
    css_selector: str = ""
    backend_node_id: int | None = None
    ax_node_id: str | None = None
    ax_role: str | None = None
    ax_name: str | None = None
    absolute_position: dict[str, float] | None = None
    highlight_index: int | None = None
    
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
            "is_interactive": self.is_interactive,
            "children": [c.to_dict() for c in self.children],
            "xpath": self.xpath,
            "css_selector": self.css_selector,
            "backend_node_id": self.backend_node_id,
            "ax_node_id": self.ax_node_id,
            "ax_role": self.ax_role,
            "ax_name": self.ax_name,
            "highlight_index": self.highlight_index,
        }
    
    def to_llm_text(self) -> str:
        """生成 LLM 友好的文本表示"""
        parts = [f"[{self.highlight_index}]" if self.highlight_index is not None else ""]
        
        if self.ax_role:
            parts.append(f"[{self.ax_role}]")
        
        parts.append(self.tag_name)
        
        if self.text:
            text_preview = self.text[:100].replace("\n", " ").strip()
            if len(self.text) > 100:
                text_preview += "..."
            parts.append(f'"{text_preview}"')
        
        if self.is_clickable:
            parts.append("[clickable]")
        if self.is_input:
            parts.append("[input]")
        
        return " ".join(parts)


INTERACTIVE_TAGS = {
    "a", "button", "input", "select", "textarea", "option",
    "label", "optgroup", "details", "summary", "dialog",
}

INPUT_TYPES = {
    "text", "password", "email", "number", "tel", "url", "search",
    "date", "datetime-local", "time", "week", "month", "color",
    "file", "range", "checkbox", "radio",
}

PAGINATION_PATTERNS = [
    r"next\s*»",
    r"»",
    r"›",
    r"››",
    r"next",
    r"下一页",
    r"后一页",
    r"previous",
    r"prev",
    r"«\s*prev",
    r"«",
    r"‹",
    r"‹‹",
    r"上一页",
    r"前一页",
    r"^\d+$",
    r"page\s*\d+",
    r"第\s*\d+\s*页",
]


class EnhancedDOMSerializer:
    """增强版 DOM 序列化器"""
    
    def __init__(self, controller, cdp_manager=None):
        """
        初始化增强版 DOM 序列化器
        
        Args:
            controller: BrowserController 实例
            cdp_manager: CDPSessionManager 实例（可选）
        """
        self._controller = controller
        self._cdp_manager = cdp_manager
        self._element_index: int = 0
        self._selector_map: dict[int, DOMElementEnhanced] = {}
    
    @property
    def page(self):
        return self._controller.page
    
    async def serialize_dom(
        self,
        include_hidden: bool = False,
        max_depth: int = 10,
        use_cdp: bool = False,
        include_ax_tree: bool = False,
    ) -> list[DOMElementEnhanced]:
        """
        序列化当前页面 DOM
        
        Args:
            include_hidden: 是否包含隐藏元素
            max_depth: 最大递归深度
            use_cdp: 是否使用 CDP DOMSnapshot API
            include_ax_tree: 是否包含可访问性树
            
        Returns:
            list[DOMElementEnhanced]: DOM 元素列表
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")
        
        self._element_index = 0
        self._selector_map.clear()
        
        try:
            if use_cdp and self._cdp_manager:
                return await self._serialize_with_cdp(
                    include_hidden=include_hidden,
                    include_ax_tree=include_ax_tree,
                )
            else:
                return await self._serialize_with_js(
                    include_hidden=include_hidden,
                    max_depth=max_depth,
                )
        except Exception as e:
            logger.error(f"序列化 DOM 失败: {e}")
            raise
    
    async def _serialize_with_cdp(
        self,
        include_hidden: bool,
        include_ax_tree: bool,
    ) -> list[DOMElementEnhanced]:
        """使用 CDP DOMSnapshot API 序列化"""
        try:
            cdp_commands = self._cdp_manager.get_commands(self.page)
            
            snapshot = await cdp_commands.get_dom_snapshot(
                computed_styles=["display", "visibility", "opacity", "cursor"],
                include_event_listeners=True,
            )
            
            ax_tree = None
            if include_ax_tree:
                try:
                    ax_result = await cdp_commands.get_full_ax_tree()
                    ax_tree = self._parse_ax_tree(ax_result)
                except Exception as e:
                    logger.warning(f"获取 AX Tree 失败: {e}")
            
            elements = self._parse_dom_snapshot(snapshot, ax_tree, include_hidden)
            return elements
            
        except Exception as e:
            logger.warning(f"CDP 序列化失败，回退到 JS 方式: {e}")
            return await self._serialize_with_js(include_hidden=include_hidden, max_depth=10)
    
    def _parse_dom_snapshot(
        self,
        snapshot: dict,
        ax_tree: dict | None,
        include_hidden: bool,
    ) -> list[DOMElementEnhanced]:
        """解析 CDP DOMSnapshot"""
        elements = []
        
        documents = snapshot.get("documents", [])
        if not documents:
            return elements
        
        for doc in documents:
            nodes = doc.get("nodes", {})
            layouts = doc.get("layout", {}).get("nodeIndex", [])
            
            for idx, node in enumerate(nodes):
                node_type = node.get("nodeType", 0)
                if node_type != 1:
                    continue
                
                node_name = node.get("nodeName", "").lower()
                node_value = node.get("nodeValue", "")
                attributes = node.get("attributes", [])
                backend_node_id = node.get("backendNodeId")
                
                attrs_dict = {}
                for i in range(0, len(attributes), 2):
                    if i + 1 < len(attributes):
                        attrs_dict[attributes[i]] = attributes[i + 1]
                
                is_visible = self._check_visibility_from_snapshot(node, layouts, idx)
                if not include_hidden and not is_visible:
                    continue
                
                is_interactive = self._is_interactive_element(node_name, attrs_dict)
                is_clickable = self._is_clickable_element(node_name, attrs_dict)
                is_input = self._is_input_element(node_name, attrs_dict)
                
                ax_info = {}
                if ax_tree and backend_node_id:
                    ax_info = ax_tree.get(backend_node_id, {})
                
                elem = DOMElementEnhanced(
                    element_id=f"elem_{self._element_index}",
                    tag_name=node_name,
                    text=node_value[:500] if node_value else "",
                    attributes=attrs_dict,
                    is_visible=is_visible,
                    is_clickable=is_clickable,
                    is_input=is_input,
                    is_interactive=is_interactive,
                    backend_node_id=backend_node_id,
                    ax_node_id=ax_info.get("nodeId"),
                    ax_role=ax_info.get("role"),
                    ax_name=ax_info.get("name"),
                    highlight_index=self._element_index if is_interactive else None,
                )
                
                self._selector_map[self._element_index] = elem
                self._element_index += 1
                elements.append(elem)
        
        return elements
    
    def _parse_ax_tree(self, ax_result: dict) -> dict[int, dict]:
        """解析可访问性树"""
        ax_map = {}
        
        nodes = ax_result.get("nodes", [])
        for node in nodes:
            node_id = node.get("nodeId")
            backend_node_id = node.get("backendDOMNodeId")
            
            if backend_node_id:
                ax_map[backend_node_id] = {
                    "nodeId": node_id,
                    "role": node.get("role", {}).get("value"),
                    "name": node.get("name", {}).get("value"),
                    "value": node.get("value", {}).get("value"),
                    "description": node.get("description", {}).get("value"),
                }
        
        return ax_map
    
    def _check_visibility_from_snapshot(
        self,
        node: dict,
        layouts: list,
        idx: int,
    ) -> bool:
        """从快照检查元素可见性"""
        computed_styles = node.get("computedStyles", [])
        
        if len(computed_styles) >= 3:
            display = computed_styles[0] if computed_styles[0] else ""
            visibility = computed_styles[1] if computed_styles[1] else ""
            opacity = computed_styles[2] if computed_styles[2] else ""
            
            if display == "none":
                return False
            if visibility == "hidden":
                return False
            if opacity == "0":
                return False
        
        return True
    
    async def _serialize_with_js(
        self,
        include_hidden: bool,
        max_depth: int,
    ) -> list[DOMElementEnhanced]:
        """使用 JavaScript 序列化"""
        script = """
        (args) => {
            const { includeHidden, maxDepth } = args;
            const elements = [];
            let elementIndex = 0;
            
            function isVisible(element) {
                if (!element) return false;
                const style = window.getComputedStyle(element);
                return style.display !== 'none' &&
                       style.visibility !== 'hidden' &&
                       style.opacity !== '0';
            }
            
            function isInteractive(element) {
                if (!element) return false;
                const tagName = element.tagName.toLowerCase();
                const interactiveTags = ['a', 'button', 'input', 'select', 'textarea', 'option', 'label', 'details', 'summary'];
                if (interactiveTags.includes(tagName)) return true;
                if (element.onclick) return true;
                if (element.getAttribute('role')) return true;
                const tabindex = element.getAttribute('tabindex');
                if (tabindex && tabindex !== '-1') return true;
                const style = window.getComputedStyle(element);
                return style.cursor === 'pointer';
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
                        if (sibling.nodeType === Node.ELEMENT_NODE && sibling.tagName === current.tagName) {
                            index++;
                        }
                        sibling = sibling.previousSibling;
                    }
                    parts.unshift(`${current.tagName.toLowerCase()}[${index}]`);
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
                
                const tagName = element.tagName.toLowerCase();
                const text = (element.innerText || element.textContent || '').substring(0, 500);
                const visible = isVisible(element);
                const interactive = isInteractive(element);
                const clickable = isClickable(element);
                const input = isInputElement(element);
                
                const highlightIndex = interactive ? elementIndex++ : null;
                
                const domElement = {
                    element_id: 'elem_' + elementIndex,
                    tag_name: tagName,
                    text: text,
                    attributes: getAttributes(element),
                    bounding_box: getBoundingBox(element),
                    is_visible: visible,
                    is_clickable: clickable,
                    is_input: input,
                    is_interactive: interactive,
                    children: [],
                    xpath: getXPath(element),
                    css_selector: getCssSelector(element),
                    highlight_index: highlightIndex
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
    
    def _parse_element(self, data: dict) -> DOMElementEnhanced:
        """解析元素数据"""
        elem = DOMElementEnhanced(
            element_id=data["element_id"],
            tag_name=data["tag_name"],
            text=data["text"],
            attributes=data["attributes"],
            bounding_box=data["bounding_box"],
            is_visible=data["is_visible"],
            is_clickable=data["is_clickable"],
            is_input=data["is_input"],
            is_interactive=data.get("is_interactive", False),
            children=[self._parse_element(c) for c in data.get("children", [])],
            xpath=data["xpath"],
            css_selector=data["css_selector"],
            backend_node_id=data.get("backend_node_id"),
            ax_node_id=data.get("ax_node_id"),
            ax_role=data.get("ax_role"),
            ax_name=data.get("ax_name"),
            highlight_index=data.get("highlight_index"),
        )
        
        if elem.highlight_index is not None:
            self._selector_map[elem.highlight_index] = elem
        
        return elem
    
    def _is_interactive_element(self, tag_name: str, attrs: dict) -> bool:
        """判断是否为可交互元素"""
        if tag_name in INTERACTIVE_TAGS:
            return True
        
        if attrs.get("onclick"):
            return True
        
        if attrs.get("role"):
            return True
        
        tabindex = attrs.get("tabindex")
        if tabindex and tabindex != "-1":
            return True
        
        return False
    
    def _is_clickable_element(self, tag_name: str, attrs: dict) -> bool:
        """判断是否为可点击元素"""
        if tag_name in {"a", "button", "input", "select", "textarea", "label"}:
            return True
        
        if attrs.get("onclick"):
            return True
        
        if attrs.get("role") == "button":
            return True
        
        return False
    
    def _is_input_element(self, tag_name: str, attrs: dict) -> bool:
        """判断是否为输入元素"""
        if tag_name in {"textarea", "select"}:
            return True
        
        if tag_name == "input":
            input_type = attrs.get("type", "text")
            return input_type in INPUT_TYPES
        
        return False
    
    async def detect_pagination_buttons(self) -> list[DOMElementEnhanced]:
        """
        检测分页按钮
        
        Returns:
            list[DOMElementEnhanced]: 分页按钮列表
        """
        elements = await self.serialize_dom(include_hidden=False)
        pagination_elements = []
        
        for elem in self._flatten_elements(elements):
            if not elem.is_clickable:
                continue
            
            text = elem.text.lower().strip()
            aria_label = (elem.attributes.get("aria-label") or "").lower()
            title = (elem.attributes.get("title") or "").lower()
            
            combined_text = f"{text} {aria_label} {title}".strip()
            
            for pattern in PAGINATION_PATTERNS:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    pagination_elements.append(elem)
                    break
            
            rel = elem.attributes.get("rel", "")
            if rel in {"next", "prev"}:
                pagination_elements.append(elem)
            
            classes = elem.attributes.get("class", "")
            if any(p in classes.lower() for p in ["next", "prev", "pagination", "pager"]):
                pagination_elements.append(elem)
        
        return pagination_elements
    
    def _flatten_elements(self, elements: list[DOMElementEnhanced]) -> list[DOMElementEnhanced]:
        """扁平化元素列表"""
        result = []
        for elem in elements:
            result.append(elem)
            result.extend(self._flatten_elements(elem.children))
        return result
    
    async def get_interactive_elements(self) -> list[DOMElementEnhanced]:
        """获取所有可交互元素"""
        elements = await self.serialize_dom(include_hidden=False)
        return [e for e in self._flatten_elements(elements) if e.is_interactive]
    
    def get_element_by_highlight_index(self, index: int) -> DOMElementEnhanced | None:
        """通过高亮索引获取元素"""
        return self._selector_map.get(index)
    
    def get_selector_map(self) -> dict[int, DOMElementEnhanced]:
        """获取选择器映射"""
        return self._selector_map.copy()
    
    def to_llm_representation(self) -> str:
        """生成 LLM 友好的 DOM 表示"""
        lines = ["[Interactive Elements]"]
        
        for index, elem in sorted(self._selector_map.items()):
            lines.append(elem.to_llm_text())
        
        return "\n".join(lines)
