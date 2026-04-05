"""
PyAgent 浏览器自动化模块 - 智能元素定位器

提供多种元素定位方式，支持索引定位、文本定位和坐标点击。
参考 browser-use 项目的元素定位设计实现。
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LocatorType(str, Enum):
    """定位器类型"""
    INDEX = "index"
    TEXT = "text"
    CSS_SELECTOR = "css_selector"
    XPATH = "xpath"
    COORDINATE = "coordinate"
    AX_NODE_ID = "ax_node_id"
    BACKEND_NODE_ID = "backend_node_id"


@dataclass
class ElementInfo:
    """元素信息"""
    index: int
    tag_name: str
    text: str | None = None
    attributes: dict[str, str] | None = None
    is_visible: bool = True
    is_interactive: bool = True
    is_clickable: bool = False
    is_input: bool = False
    bounds: dict[str, float] | None = None
    selector: str | None = None
    backend_node_id: int | None = None
    ax_node_id: str | None = None


@dataclass
class LocateResult:
    """定位结果"""
    success: bool
    element: ElementInfo | None = None
    error: str | None = None
    suggestion: str | None = None


class ClickElementParams(BaseModel):
    """点击元素参数"""
    index: int | None = None
    text: str | None = None
    selector: str | None = None
    coordinate: tuple[float, float] | None = None
    num_clicks: int = Field(default=1, ge=1, le=3)


class InputTextParams(BaseModel):
    """输入文本参数"""
    index: int | None = None
    text: str | None = None
    selector: str | None = None
    value: str
    press_enter: bool = False
    clear_first: bool = True


class ElementLocator:
    """智能元素定位器"""
    
    def __init__(self):
        self._elements: list[ElementInfo] = []
        self._selector_map: dict[int, ElementInfo] = {}
    
    def update_elements(self, elements: list[ElementInfo]) -> None:
        """
        更新元素列表
        
        Args:
            elements: 元素信息列表
        """
        self._elements = elements
        self._selector_map = {elem.index: elem for elem in elements}
        logger.debug(f"Updated {len(elements)} elements")
    
    def get_element_by_index(self, index: int) -> ElementInfo | None:
        """
        通过索引获取元素
        
        Args:
            index: 元素索引
            
        Returns:
            ElementInfo 或 None
        """
        return self._selector_map.get(index)
    
    def get_element_by_text(
        self,
        text: str,
        exact: bool = False,
        case_sensitive: bool = False,
    ) -> ElementInfo | None:
        """
        通过文本获取元素
        
        Args:
            text: 要匹配的文本
            exact: 是否精确匹配
            case_sensitive: 是否区分大小写
            
        Returns:
            ElementInfo 或 None
        """
        search_text = text if case_sensitive else text.lower()
        
        for elem in self._elements:
            if not elem.text:
                continue
            
            elem_text = elem.text if case_sensitive else elem.text.lower()
            
            if exact:
                if elem_text == search_text:
                    return elem
            else:
                if search_text in elem_text:
                    return elem
        
        return None
    
    def get_elements_by_text(
        self,
        text: str,
        exact: bool = False,
        case_sensitive: bool = False,
    ) -> list[ElementInfo]:
        """
        通过文本获取所有匹配的元素
        
        Args:
            text: 要匹配的文本
            exact: 是否精确匹配
            case_sensitive: 是否区分大小写
            
        Returns:
            匹配的元素列表
        """
        search_text = text if case_sensitive else text.lower()
        results = []
        
        for elem in self._elements:
            if not elem.text:
                continue
            
            elem_text = elem.text if case_sensitive else elem.text.lower()
            
            if exact:
                if elem_text == search_text:
                    results.append(elem)
            else:
                if search_text in elem_text:
                    results.append(elem)
        
        return results
    
    def get_clickable_elements(self) -> list[ElementInfo]:
        """获取所有可点击元素"""
        return [elem for elem in self._elements if elem.is_clickable]
    
    def get_input_elements(self) -> list[ElementInfo]:
        """获取所有输入元素"""
        return [elem for elem in self._elements if elem.is_input]
    
    def get_interactive_elements(self) -> list[ElementInfo]:
        """获取所有可交互元素"""
        return [elem for elem in self._elements if elem.is_interactive]
    
    def locate(
        self,
        locator_type: LocatorType,
        value: Any,
        **kwargs,
    ) -> LocateResult:
        """
        定位元素
        
        Args:
            locator_type: 定位器类型
            value: 定位值
            **kwargs: 额外参数
            
        Returns:
            LocateResult: 定位结果
        """
        try:
            if locator_type == LocatorType.INDEX:
                element = self.get_element_by_index(int(value))
                if element:
                    return LocateResult(success=True, element=element)
                return LocateResult(
                    success=False,
                    error=f"Element with index {value} not found",
                    suggestion=f"Available indices: 0-{len(self._elements) - 1}",
                )
            
            elif locator_type == LocatorType.TEXT:
                exact = kwargs.get("exact", False)
                case_sensitive = kwargs.get("case_sensitive", False)
                element = self.get_element_by_text(
                    str(value),
                    exact=exact,
                    case_sensitive=case_sensitive,
                )
                if element:
                    return LocateResult(success=True, element=element)
                return LocateResult(
                    success=False,
                    error=f"Element with text '{value}' not found",
                    suggestion="Try using partial text match or check case sensitivity",
                )
            
            elif locator_type == LocatorType.COORDINATE:
                if isinstance(value, (tuple, list)) and len(value) == 2:
                    return LocateResult(
                        success=True,
                        element=ElementInfo(
                            index=-1,
                            tag_name="coordinate",
                            bounds={
                                "x": float(value[0]),
                                "y": float(value[1]),
                                "width": 0,
                                "height": 0,
                            },
                        ),
                    )
                return LocateResult(
                    success=False,
                    error="Invalid coordinate format, expected (x, y)",
                )
            
            elif locator_type == LocatorType.CSS_SELECTOR:
                for elem in self._elements:
                    if elem.selector == value:
                        return LocateResult(success=True, element=elem)
                return LocateResult(
                    success=False,
                    error=f"Element with selector '{value}' not found",
                )
            
            else:
                return LocateResult(
                    success=False,
                    error=f"Unsupported locator type: {locator_type}",
                )
                
        except Exception as e:
            logger.error(f"Locate error: {e}")
            return LocateResult(
                success=False,
                error=str(e),
            )
    
    def find_best_match(
        self,
        description: str,
        element_type: str | None = None,
    ) -> ElementInfo | None:
        """
        根据描述找到最佳匹配的元素
        
        Args:
            description: 元素描述（如"登录按钮"、"搜索框"）
            element_type: 元素类型限制（button, input, link 等）
            
        Returns:
            ElementInfo 或 None
        """
        description_lower = description.lower()
        
        candidates = self._elements
        
        if element_type:
            tag_map = {
                "button": ["button", "input"],
                "input": ["input", "textarea"],
                "link": ["a"],
                "image": ["img"],
            }
            allowed_tags = tag_map.get(element_type.lower(), [element_type.lower()])
            candidates = [
                elem for elem in candidates
                if elem.tag_name.lower() in allowed_tags
            ]
        
        for elem in candidates:
            if not elem.text:
                continue
            
            elem_text = elem.text.lower()
            
            if description_lower == elem_text:
                return elem
            
            if description_lower in elem_text:
                return elem
        
        type_keywords = {
            "button": ["按钮", "button", "点击", "click"],
            "input": ["输入", "input", "框", "field", "搜索", "search"],
            "link": ["链接", "link", "跳转", "navigate"],
            "image": ["图片", "image", "img", "图标", "icon"],
        }
        
        if element_type:
            keywords = type_keywords.get(element_type.lower(), [])
            for keyword in keywords:
                if keyword in description_lower:
                    for elem in candidates:
                        if elem.text and keyword in elem.text.lower():
                            return elem
        
        return None
    
    def get_element_bounds(self, index: int) -> dict[str, float] | None:
        """
        获取元素的边界坐标
        
        Args:
            index: 元素索引
            
        Returns:
            边界坐标字典或 None
        """
        element = self.get_element_by_index(index)
        if element and element.bounds:
            return element.bounds
        return None
    
    def get_element_center(self, index: int) -> tuple[float, float] | None:
        """
        获取元素的中心坐标
        
        Args:
            index: 元素索引
            
        Returns:
            (x, y) 坐标元组或 None
        """
        bounds = self.get_element_bounds(index)
        if bounds:
            x = bounds.get("x", 0) + bounds.get("width", 0) / 2
            y = bounds.get("y", 0) + bounds.get("height", 0) / 2
            return (x, y)
        return None
    
    def to_llm_format(self) -> str:
        """
        生成 LLM 友好的元素列表
        
        Returns:
            格式化的元素列表字符串
        """
        lines = ["[Interactive Elements]"]
        
        for elem in self._elements:
            if not elem.is_interactive:
                continue
            
            text_preview = ""
            if elem.text:
                text_preview = elem.text[:50]
                if len(elem.text) > 50:
                    text_preview += "..."
            
            type_info = elem.tag_name
            if elem.is_clickable:
                type_info += " [clickable]"
            if elem.is_input:
                type_info += " [input]"
            
            lines.append(f"[{elem.index}] {type_info}: {text_preview}")
        
        return "\n".join(lines)
