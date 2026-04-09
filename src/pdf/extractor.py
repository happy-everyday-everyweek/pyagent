"""
PyAgent PDF模块 - 内容提取器
"""

from typing import Any

from .parser import Image, PDFDocument, Table


class ContentExtractor:
    """PDF内容提取器"""

    def __init__(self, document: PDFDocument | None = None):
        self.document = document

    def extract_text(self) -> str:
        if not self.document:
            return ""
        return "\n\n".join(page.text for page in self.document.pages)

    def extract_text_by_page(self, page_num: int) -> str:
        if not self.document:
            return ""
        if 0 < page_num <= len(self.document.pages):
            return self.document.pages[page_num - 1].text
        return ""

    def extract_tables(self) -> list[Table]:
        if not self.document:
            return []
        return self.document.tables

    def extract_images(self) -> list[Image]:
        if not self.document:
            return []
        return self.document.images

    def extract_links(self) -> list[dict[str, Any]]:
        import re
        if not self.document:
            return []

        links: list[dict[str, Any]] = []
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'

        for page in self.document.pages:
            found_urls = re.findall(url_pattern, page.text)
            for url in found_urls:
                links.append({
                    "url": url,
                    "page_num": page.page_num,
                })

        return links

    def extract_form_fields(self) -> list[dict[str, Any]]:
        if not self.document:
            return []
        return []

    def extract_structure(self) -> dict[str, Any]:
        if not self.document:
            return {}

        return {
            "title": self.document.metadata.get("title", ""),
            "author": self.document.metadata.get("author", ""),
            "page_count": self.document.page_count,
            "outline": [
                {"title": item.title, "level": item.level, "page": item.page_num}
                for item in self.document.outline
            ],
            "tables_count": len(self.document.tables),
            "images_count": len(self.document.images),
        }
