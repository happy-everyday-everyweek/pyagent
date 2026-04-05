"""
Word 文档创建模块

提供从模板或空白创建 Word 文档的功能。
支持多种文档模板和自定义样式。

使用示例:
    from src.document.docx.creator import DocxCreator
    
    # 初始化
    creator = DocxCreator()
    
    # 创建空白文档
    creator.create_blank('new_document.docx')
    
    # 从模板创建
    creator.create_from_template('template.docx', 'new_document.docx')
    
    # 创建带内容的文档
    creator.create_with_content(
        'document.docx',
        title='文档标题',
        paragraphs=['段落1', '段落2']
    )
"""

import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


class DocxCreator:
    """
    Word 文档创建器。

    提供多种创建文档的方式：
    - 创建空白文档
    - 从模板创建
    - 创建带预定义内容的文档

    属性:
        template_dir: 模板目录路径
    """

    DEFAULT_STYLES = {
        "title": {"size": 28, "bold": True, "color": "000000"},
        "heading1": {"size": 24, "bold": True, "color": "000000"},
        "heading2": {"size": 20, "bold": True, "color": "000000"},
        "heading3": {"size": 16, "bold": True, "color": "000000"},
        "normal": {"size": 11, "bold": False, "color": "000000"},
    }

    def __init__(self, template_dir: str | None = None):
        """
        初始化文档创建器。

        参数:
            template_dir: 自定义模板目录路径
        """
        self.template_dir = Path(template_dir) if template_dir else Path(__file__).parent / "templates"

    def create_blank(
        self,
        output_path: str,
        author: str | None = None,
        title: str | None = None
    ) -> bool:
        """
        创建空白 Word 文档。

        参数:
            output_path: 输出文件路径
            author: 文档作者
            title: 文档标题

        返回:
            是否成功创建
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        content = self._generate_blank_document(author, title)

        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("[Content_Types].xml", self._get_content_types())
                zf.writestr("_rels/.rels", self._get_rels())
                zf.writestr("word/document.xml", content)
                zf.writestr("word/_rels/document.xml.rels", self._get_document_rels())
                zf.writestr("word/styles.xml", self._get_styles())
                zf.writestr("word/settings.xml", self._get_settings())
                zf.writestr("docProps/core.xml", self._get_core_props(author, title))
                zf.writestr("docProps/app.xml", self._get_app_props())
            return True
        except Exception as e:
            print(f"创建文档失败: {e}")
            return False

    def create_from_template(
        self,
        template_path: str,
        output_path: str,
        replacements: dict[str, str] | None = None
    ) -> bool:
        """
        从模板创建文档。

        参数:
            template_path: 模板文件路径
            output_path: 输出文件路径
            replacements: 要替换的文本映射 {旧文本: 新文本}

        返回:
            是否成功创建
        """
        template_path = Path(template_path)
        output_path = Path(output_path)

        if not template_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {template_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not replacements:
            shutil.copy(template_path, output_path)
            return True

        try:
            with zipfile.ZipFile(template_path, "r") as zf_in:
                with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf_out:
                    for name in zf_in.namelist():
                        content = zf_in.read(name)

                        if name.endswith(".xml"):
                            content_str = content.decode("utf-8")
                            for old_text, new_text in replacements.items():
                                content_str = content_str.replace(old_text, new_text)
                            content = content_str.encode("utf-8")

                        zf_out.writestr(name, content)
            return True
        except Exception as e:
            print(f"从模板创建文档失败: {e}")
            return False

    def create_with_content(
        self,
        output_path: str,
        title: str | None = None,
        paragraphs: list[str] | None = None,
        headings: dict[str, str] | None = None,
        author: str | None = None,
        styles: dict[str, dict] | None = None
    ) -> bool:
        """
        创建带内容的文档。

        参数:
            output_path: 输出文件路径
            title: 文档标题
            paragraphs: 段落文本列表
            headings: 标题字典 {级别: 文本}，级别为 "h1", "h2", "h3"
            author: 文档作者
            styles: 自定义样式

        返回:
            是否成功创建
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        merged_styles = {**self.DEFAULT_STYLES, **(styles or {})}

        content_parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
        content_parts.append('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">')
        content_parts.append("<w:body>")

        if title:
            content_parts.append(self._create_title_paragraph(title, merged_styles))

        if headings:
            for level, text in headings.items():
                content_parts.append(self._create_heading_paragraph(level, text, merged_styles))

        if paragraphs:
            for para_text in paragraphs:
                content_parts.append(self._create_normal_paragraph(para_text, merged_styles))

        content_parts.append("</w:body>")
        content_parts.append("</w:document>")

        content = "\n".join(content_parts)

        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("[Content_Types].xml", self._get_content_types())
                zf.writestr("_rels/.rels", self._get_rels())
                zf.writestr("word/document.xml", content)
                zf.writestr("word/_rels/document.xml.rels", self._get_document_rels())
                zf.writestr("word/styles.xml", self._get_styles())
                zf.writestr("docProps/core.xml", self._get_core_props(author, title))
                zf.writestr("docProps/app.xml", self._get_app_props())
            return True
        except Exception as e:
            print(f"创建文档失败: {e}")
            return False

    def create_report(
        self,
        output_path: str,
        title: str,
        sections: list[dict[str, Any]],
        author: str | None = None,
        include_toc: bool = False
    ) -> bool:
        """
        创建报告格式文档。

        参数:
            output_path: 输出文件路径
            title: 报告标题
            sections: 章节列表，每个章节包含:
                      - heading: 标题文本
                      - level: 标题级别 (1-3)
                      - content: 内容段落列表
            author: 作者
            include_toc: 是否包含目录

        返回:
            是否成功创建
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        content_parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
        content_parts.append('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">')
        content_parts.append("<w:body>")

        content_parts.append(self._create_title_paragraph(title, self.DEFAULT_STYLES))

        if include_toc:
            content_parts.append(self._create_toc())

        for section in sections:
            heading = section.get("heading", "")
            level = section.get("level", 1)
            content = section.get("content", [])

            if heading:
                content_parts.append(
                    self._create_heading_paragraph(f"h{level}", heading, self.DEFAULT_STYLES)
                )

            for para_text in content:
                content_parts.append(
                    self._create_normal_paragraph(para_text, self.DEFAULT_STYLES)
                )

        content_parts.append("</w:body>")
        content_parts.append("</w:document>")

        content = "\n".join(content_parts)

        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("[Content_Types].xml", self._get_content_types())
                zf.writestr("_rels/.rels", self._get_rels())
                zf.writestr("word/document.xml", content)
                zf.writestr("word/_rels/document.xml.rels", self._get_document_rels())
                zf.writestr("word/styles.xml", self._get_styles())
                zf.writestr("docProps/core.xml", self._get_core_props(author, title))
                zf.writestr("docProps/app.xml", self._get_app_props())
            return True
        except Exception as e:
            print(f"创建报告失败: {e}")
            return False

    def create_letter(
        self,
        output_path: str,
        recipient: str,
        sender: str,
        date: str | None = None,
        subject: str | None = None,
        body: list[str] | None = None,
        closing: str = "此致\n敬礼"
    ) -> bool:
        """
        创建信函格式文档。

        参数:
            output_path: 输出文件路径
            recipient: 收件人
            sender: 发件人
            date: 日期
            subject: 主题
            body: 正文段落列表
            closing: 结尾敬语

        返回:
            是否成功创建
        """
        if date is None:
            date = datetime.now().strftime("%Y年%m月%d日")

        if body is None:
            body = []

        paragraphs = [f"{recipient}:", ""]

        if subject:
            paragraphs.append(f"主题：{subject}")
            paragraphs.append("")

        paragraphs.extend(body)
        paragraphs.append("")
        paragraphs.append(closing)
        paragraphs.append("")
        paragraphs.append(sender)
        paragraphs.append(date)

        return self.create_with_content(
            output_path,
            paragraphs=paragraphs,
            author=sender
        )

    def list_templates(self) -> list[str]:
        """
        列出可用的模板文件。

        返回:
            模板文件名列表
        """
        if not self.template_dir.exists():
            return []

        return [f.name for f in self.template_dir.glob("*.docx")]

    def _generate_blank_document(
        self,
        author: str | None = None,
        title: str | None = None
    ) -> str:
        """生成空白文档 XML"""
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
<w:p><w:r><w:t></w:t></w:r></w:p>
</w:body>
</w:document>"""

    def _create_title_paragraph(self, text: str, styles: dict) -> str:
        """创建标题段落"""
        style = styles.get("title", self.DEFAULT_STYLES["title"])
        escaped_text = self._escape_xml(text)
        return f"""<w:p>
<w:pPr><w:pStyle w:val="Title"/></w:pPr>
<w:r><w:rPr><w:b/><w:sz w:val="{style['size'] * 2}"/></w:rPr><w:t>{escaped_text}</w:t></w:r>
</w:p>"""

    def _create_heading_paragraph(self, level: str, text: str, styles: dict) -> str:
        """创建标题段落"""
        style_key = f"heading{level[-1]}" if level.startswith("h") else level
        style = styles.get(style_key, self.DEFAULT_STYLES.get(style_key, self.DEFAULT_STYLES["normal"]))
        escaped_text = self._escape_xml(text)

        style_val = f"Heading{level[-1]}" if level.startswith("h") else level

        return f"""<w:p>
<w:pPr><w:pStyle w:val="{style_val}"/></w:pPr>
<w:r><w:rPr><w:b/><w:sz w:val="{style['size'] * 2}"/></w:rPr><w:t>{escaped_text}</w:t></w:r>
</w:p>"""

    def _create_normal_paragraph(self, text: str, styles: dict) -> str:
        """创建普通段落"""
        style = styles.get("normal", self.DEFAULT_STYLES["normal"])
        escaped_text = self._escape_xml(text)
        return f"""<w:p>
<w:r><w:rPr><w:sz w:val="{style['size'] * 2}"/></w:rPr><w:t>{escaped_text}</w:t></w:r>
</w:p>"""

    def _create_toc(self) -> str:
        """创建目录"""
        return """<w:p>
<w:pPr><w:pStyle w:val="TOCHeading"/></w:pPr>
<w:r><w:t>目录</w:t></w:r>
</w:p>
<w:p>
<w:r>
<w:fldChar w:fldCharType="begin"/>
</w:r>
<w:r>
<w:instrText>TOC \\o "1-3" \\h \\z \\u</w:instrText>
</w:r>
<w:r>
<w:fldChar w:fldCharType="separate"/>
</w:r>
<w:r>
<w:fldChar w:fldCharType="end"/>
</w:r>
</w:p>"""

    def _escape_xml(self, text: str) -> str:
        """转义 XML 特殊字符"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    def _get_content_types(self) -> str:
        """获取 Content Types XML"""
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""

    def _get_rels(self) -> str:
        """获取主关系文件"""
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""

    def _get_document_rels(self) -> str:
        """获取文档关系文件"""
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
</Relationships>"""

    def _get_styles(self) -> str:
        """获取样式文件"""
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults>
<w:rPrDefault><w:rPr><w:sz w:val="22"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="200" w:line="276"/></w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:styleId="Normal">
<w:name w:val="Normal"/>
<w:qFormat/>
</w:style>
<w:style w:type="paragraph" w:styleId="Title">
<w:name w:val="Title"/>
<w:basedOn w:val="Normal"/>
<w:pPr><w:spacing w:before="240" w:after="240"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="56"/></w:rPr>
<w:qFormat/>
</w:style>
<w:style w:type="paragraph" w:styleId="Heading1">
<w:name w:val="Heading 1"/>
<w:basedOn w:val="Normal"/>
<w:pPr><w:spacing w:before="360" w:after="120"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="44"/></w:rPr>
<w:qFormat/>
</w:style>
<w:style w:type="paragraph" w:styleId="Heading2">
<w:name w:val="Heading 2"/>
<w:basedOn w:val="Normal"/>
<w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="36"/></w:rPr>
<w:qFormat/>
</w:style>
<w:style w:type="paragraph" w:styleId="Heading3">
<w:name w:val="Heading 3"/>
<w:basedOn w:val="Normal"/>
<w:pPr><w:spacing w:before="200" w:after="80"/></w:pPr>
<w:rPr><w:b/><w:sz w:val="28"/></w:rPr>
<w:qFormat/>
</w:style>
</w:styles>"""

    def _get_settings(self) -> str:
        """获取设置文件"""
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:zoom w:percent="100"/>
<w:defaultTabStop w:val="720"/>
<w:characterSpacingControl w:val="doNotCompress"/>
<w:compat>
<w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>
<w:compatSetting w:name="overrideTableStyleFontSizeAndJustification" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>
<w:compatSetting w:name="enableOpenTypeFeatures" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>
<w:compatSetting w:name="doNotFlipMirrorIndents" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>
<w:compatSetting w:name="differentiateMultirowTableHeaders" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>
</w:compat>
<w:rsids>
<w:rsidRoot w:val="00000000"/>
<w:rsid w:val="00000000"/>
</w:rsids>
<w:themeFontLang w:val="zh-CN"/>
<w:clrSchemeMapping w:bg1="light1" w:t1="dark1" w:bg2="light2" w:t2="dark2" w:accent1="accent1" w:accent2="accent2" w:accent3="accent3" w:accent4="accent4" w:accent5="accent5" w:accent6="accent6" w:hyperlink="hyperlink" w:followedHyperlink="followedHyperlink"/>
</w:settings>"""

    def _get_core_props(self, author: str | None, title: str | None) -> str:
        """获取核心属性文件"""
        now = datetime.now().isoformat()
        author_str = author or "Unknown"
        title_str = title or ""

        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:creator>{self._escape_xml(author_str)}</dc:creator>
<dc:title>{self._escape_xml(title_str)}</dc:title>
<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>"""

    def _get_app_props(self) -> str:
        """获取应用程序属性文件"""
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
<Application>PyAgent Document Creator</Application>
<AppVersion>1.0</AppVersion>
</Properties>"""
