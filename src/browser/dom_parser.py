"""DOM parser for intelligent page structure analysis."""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ElementType(Enum):
    BUTTON = "button"
    LINK = "link"
    INPUT = "input"
    SELECT = "select"
    TEXT = "text"
    IMAGE = "image"
    FORM = "form"
    TABLE = "table"
    LIST = "list"
    CONTAINER = "container"
    OTHER = "other"


@dataclass
class DOMElement:
    tag: str
    element_type: ElementType
    selector: str
    text: str = ""
    attributes: dict[str, str] = field(default_factory=dict)
    children: list["DOMElement"] = field(default_factory=list)
    is_interactive: bool = False
    is_visible: bool = True
    bounding_box: dict[str, float] | None = None
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "element_type": self.element_type.value,
            "selector": self.selector,
            "text": self.text[:100] if self.text else "",
            "attributes": self.attributes,
            "is_interactive": self.is_interactive,
            "is_visible": self.is_visible,
            "confidence": self.confidence,
            "children_count": len(self.children),
        }


class DOMParser:
    """Parses and analyzes DOM structure for intelligent interaction."""

    INTERACTIVE_TAGS = {"button", "a", "input", "select", "textarea", "label"}
    INPUT_TYPES = {"text", "email", "password", "search", "tel", "url", "number"}

    def __init__(self):
        self._elements: list[DOMElement] = []
        self._interactive_elements: list[DOMElement] = []

    def parse(self, html_content: str) -> list[DOMElement]:
        self._elements = []
        self._interactive_elements = []

        elements = self._extract_elements(html_content)
        self._elements = elements
        self._interactive_elements = [e for e in elements if e.is_interactive]

        logger.info("Parsed %d elements, %d interactive", len(self._elements), len(self._interactive_elements))
        return self._elements

    def _extract_elements(self, html: str) -> list[DOMElement]:
        elements = []

        tag_pattern = re.compile(r"<(\w+)([^>]*)>([^<]*)</\1>|<(\w+)([^>]*)\s*/?>", re.IGNORECASE | re.DOTALL)

        for match in tag_pattern.finditer(html):
            if match.group(1):
                tag = match.group(1).lower()
                attrs_str = match.group(2)
                text = match.group(3).strip()
            else:
                tag = match.group(4).lower()
                attrs_str = match.group(5)
                text = ""

            if tag in {"script", "style", "meta", "link", "head"}:
                continue

            attrs = self._parse_attributes(attrs_str)
            element_type = self._determine_element_type(tag, attrs)
            selector = self._generate_selector(tag, attrs)
            is_interactive = self._is_interactive(tag, attrs)

            element = DOMElement(
                tag=tag,
                element_type=element_type,
                selector=selector,
                text=text[:500] if text else "",
                attributes=attrs,
                is_interactive=is_interactive,
            )
            elements.append(element)

        return elements

    def _parse_attributes(self, attrs_str: str) -> dict[str, str]:
        attrs = {}
        attr_pattern = re.compile(r'(\w+)=["\']([^"\']*)["\']|(\w+)(?=\s|>|$)')

        for match in attr_pattern.finditer(attrs_str):
            if match.group(1):
                attrs[match.group(1).lower()] = match.group(2)
            elif match.group(3):
                attrs[match.group(3).lower()] = ""

        return attrs

    def _determine_element_type(self, tag: str, attrs: dict[str, str]) -> ElementType:
        if tag == "button" or attrs.get("role") == "button":
            return ElementType.BUTTON
        elif tag == "a" or attrs.get("role") == "link":
            return ElementType.LINK
        elif tag == "input":
            return ElementType.INPUT
        elif tag == "select":
            return ElementType.SELECT
        elif tag == "img":
            return ElementType.IMAGE
        elif tag == "form":
            return ElementType.FORM
        elif tag == "table":
            return ElementType.TABLE
        elif tag in {"ul", "ol", "li"}:
            return ElementType.LIST
        elif tag in {"div", "section", "article", "main", "aside", "header", "footer", "nav"}:
            return ElementType.CONTAINER
        else:
            return ElementType.OTHER

    def _generate_selector(self, tag: str, attrs: dict[str, str]) -> str:
        if attrs.get("id"):
            return f"#{attrs['id']}"

        if attrs.get("data-testid"):
            return f"[data-testid='{attrs['data-testid']}']"

        if attrs.get("name"):
            return f"{tag}[name='{attrs['name']}']"

        if attrs.get("class"):
            classes = attrs["class"].split()
            if classes:
                return f"{tag}.{classes[0]}"

        if attrs.get("type"):
            return f"{tag}[type='{attrs['type']}']"

        if attrs.get("placeholder"):
            return f"{tag}[placeholder='{attrs['placeholder'][:30]}']"

        if attrs.get("aria-label"):
            return f"{tag}[aria-label='{attrs['aria-label'][:30]}']"

        return tag

    def _is_interactive(self, tag: str, attrs: dict[str, str]) -> bool:
        if tag in self.INTERACTIVE_TAGS:
            return True

        if attrs.get("onclick") or attrs.get("href"):
            return True

        role = attrs.get("role", "").lower()
        if role in {"button", "link", "checkbox", "radio", "tab", "menuitem", "option"}:
            return True

        tabindex = attrs.get("tabindex")
        if tabindex and tabindex not in ("-1", ""):
            return True

        return False

    def find_by_text(self, text: str, exact: bool = False) -> list[DOMElement]:
        results = []
        text_lower = text.lower()

        for element in self._interactive_elements:
            element_text = element.text.lower()
            if exact:
                if text_lower == element_text:
                    results.append(element)
            else:
                if text_lower in element_text:
                    results.append(element)

        return results

    def find_by_type(self, element_type: ElementType) -> list[DOMElement]:
        return [e for e in self._elements if e.element_type == element_type]

    def find_form_fields(self) -> list[DOMElement]:
        return [e for e in self._elements if e.element_type in {ElementType.INPUT, ElementType.SELECT}]

    def find_buttons(self) -> list[DOMElement]:
        return [e for e in self._elements if e.element_type == ElementType.BUTTON]

    def find_links(self) -> list[DOMElement]:
        return [e for e in self._elements if e.element_type == ElementType.LINK]

    def get_best_selector(self, description: str) -> str | None:
        elements = self.find_by_text(description)
        if elements:
            return elements[0].selector

        for element in self._interactive_elements:
            attrs_text = " ".join(element.attributes.values()).lower()
            if description.lower() in attrs_text:
                return element.selector

        return None

    def get_page_summary(self) -> dict[str, Any]:
        return {
            "total_elements": len(self._elements),
            "interactive_elements": len(self._interactive_elements),
            "by_type": {
                et.value: len(self.find_by_type(et)) for et in ElementType
            },
            "form_fields": len(self.find_form_fields()),
            "buttons": len(self.find_buttons()),
            "links": len(self.find_links()),
        }
