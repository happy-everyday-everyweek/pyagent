"""
PyAgent PDF模块 - 格式转换器
"""

from typing import Any

from .parser import PDFDocument


class FormatConverter:
    """PDF格式转换器"""

    def __init__(self, document: PDFDocument | None = None):
        self.document = document

    def to_markdown(self) -> str:
        if not self.document:
            return ""

        lines: list[str] = []
        lines.append(f"# {self.document.metadata.get('title', 'Untitled')}")
        lines.append("")

        author = self.document.metadata.get("author", "")
        if author:
            lines.append(f"**Author:** {author}")
            lines.append("")

        for page in self.document.pages:
            lines.append(f"## Page {page.page_num}")
            lines.append("")
            lines.append(page.text)
            lines.append("")

            for table in page.tables:
                lines.append("### Table")
                lines.append("")
                for row in table.data:
                    lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
                lines.append("")

        return "\n".join(lines)

    def to_html(self) -> str:
        if not self.document:
            return ""

        html_parts: list[str] = []
        html_parts.append("<!DOCTYPE html>")
        html_parts.append("<html>")
        html_parts.append("<head>")
        html_parts.append(f"<title>{self.document.metadata.get('title', 'Untitled')}</title>")
        html_parts.append("</head>")
        html_parts.append("<body>")

        for page in self.document.pages:
            html_parts.append(f"<section id='page-{page.page_num}'>")
            html_parts.append(f"<h2>Page {page.page_num}</h2>")
            html_parts.append(f"<div class='content'>{page.text}</div>")
            html_parts.append("</section>")

        html_parts.append("</body>")
        html_parts.append("</html>")

        return "\n".join(html_parts)

    def to_json(self) -> str:
        import json
        if not self.document:
            return "{}"

        return json.dumps(self.document.to_dict(), ensure_ascii=False, indent=2)

    def to_structured_data(self) -> dict[str, Any]:
        if not self.document:
            return {}

        sections: list[dict[str, Any]] = []
        for page in self.document.pages:
            section = {
                "page_number": page.page_num,
                "content": page.text,
                "word_count": len(page.text.split()),
                "tables": [
                    {
                        "rows": len(t.data),
                        "cols": len(t.data[0]) if t.data else 0,
                        "preview": t.data[:3] if t.data else [],
                    }
                    for t in page.tables
                ],
                "images": [
                    {
                        "x": img.x,
                        "y": img.y,
                        "width": img.width,
                        "height": img.height,
                    }
                    for img in page.images
                ],
            }
            sections.append(section)

        return {
            "metadata": self.document.metadata,
            "total_pages": self.document.page_count,
            "total_words": sum(len(p.text.split()) for p in self.document.pages),
            "total_tables": len(self.document.tables),
            "total_images": len(self.document.images),
            "sections": sections,
        }
