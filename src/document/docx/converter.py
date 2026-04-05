"""
Word 文档格式转换模块

提供 DOCX 与其他格式之间的转换功能。
支持 PDF、HTML、TXT、Markdown 等格式。

使用示例:
    from src.document.docx.converter import DocxConverter
    
    # 初始化
    converter = DocxConverter()
    
    # DOCX 转 PDF
    converter.to_pdf('document.docx', 'output.pdf')
    
    # DOCX 转 HTML
    converter.to_html('document.docx', 'output.html')
    
    # HTML 转 DOCX
    converter.from_html('input.html', 'output.docx')
"""

import shutil
import subprocess
from pathlib import Path


class DocxConverter:
    """
    Word 文档格式转换器。

    提供多种格式之间的转换功能，支持：
    - DOCX <-> PDF
    - DOCX <-> HTML
    - DOCX <-> TXT
    - DOCX <-> Markdown

    属性:
        libreoffice_path: LibreOffice 可执行文件路径
    """

    SUPPORTED_OUTPUT_FORMATS = {
        "pdf": "pdf",
        "html": "html",
        "txt": "txt",
        "odt": "odt",
        "rtf": "rtf",
        "doc": "doc",
    }

    def __init__(self, libreoffice_path: str | None = None):
        """
        初始化转换器。

        参数:
            libreoffice_path: LibreOffice 可执行文件路径。
                              如果未提供，将尝试自动检测。
        """
        self.libreoffice_path = libreoffice_path or self._find_libreoffice()

    def convert(
        self,
        input_path: str,
        output_path: str,
        output_format: str | None = None
    ) -> bool:
        """
        通用转换方法。

        参数:
            input_path: 输入文件路径
            output_path: 输出文件路径
            output_format: 输出格式 (可选，根据输出文件扩展名推断)

        返回:
            是否成功转换
        """
        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileNotFoundError(f"输入文件不存在: {input_path}")

        if output_format is None:
            output_format = output_path.suffix.lstrip(".")

        input_format = input_path.suffix.lstrip(".").lower()

        if input_format == "docx":
            return self._convert_from_docx(input_path, output_path, output_format)
        if output_format == "docx":
            return self._convert_to_docx(input_path, output_path, input_format)
        return self._convert_via_libreoffice(input_path, output_path, output_format)

    def to_pdf(
        self,
        input_path: str,
        output_path: str,
        use_libreoffice: bool = True
    ) -> bool:
        """
        将 DOCX 转换为 PDF。

        参数:
            input_path: DOCX 文件路径
            output_path: 输出 PDF 文件路径
            use_libreoffice: 是否使用 LibreOffice 进行转换

        返回:
            是否成功转换
        """
        if use_libreoffice and self.libreoffice_path:
            return self._convert_via_libreoffice(
                Path(input_path),
                Path(output_path),
                "pdf"
            )
        return self._convert_to_pdf_python(input_path, output_path)

    def to_html(
        self,
        input_path: str,
        output_path: str,
        include_styles: bool = True
    ) -> bool:
        """
        将 DOCX 转换为 HTML。

        参数:
            input_path: DOCX 文件路径
            output_path: 输出 HTML 文件路径
            include_styles: 是否包含样式

        返回:
            是否成功转换
        """
        return self._convert_via_libreoffice(
            Path(input_path),
            Path(output_path),
            "html"
        )

    def to_txt(
        self,
        input_path: str,
        output_path: str,
        encoding: str = "utf-8"
    ) -> bool:
        """
        将 DOCX 转换为纯文本。

        参数:
            input_path: DOCX 文件路径
            output_path: 输出文本文件路径
            encoding: 文本编码

        返回:
            是否成功转换
        """
        try:
            text = self._extract_text_from_docx(input_path)
            Path(output_path).write_text(text, encoding=encoding)
            return True
        except Exception as e:
            print(f"转换失败: {e}")
            return False

    def to_markdown(
        self,
        input_path: str,
        output_path: str
    ) -> bool:
        """
        将 DOCX 转换为 Markdown。

        参数:
            input_path: DOCX 文件路径
            output_path: 输出 Markdown 文件路径

        返回:
            是否成功转换
        """
        try:
            markdown = self._convert_to_markdown(input_path)
            Path(output_path).write_text(markdown, encoding="utf-8")
            return True
        except Exception as e:
            print(f"转换失败: {e}")
            return False

    def from_html(
        self,
        input_path: str,
        output_path: str
    ) -> bool:
        """
        将 HTML 转换为 DOCX。

        参数:
            input_path: HTML 文件路径
            output_path: 输出 DOCX 文件路径

        返回:
            是否成功转换
        """
        return self._convert_via_libreoffice(
            Path(input_path),
            Path(output_path),
            "docx"
        )

    def from_txt(
        self,
        input_path: str,
        output_path: str,
        encoding: str = "utf-8"
    ) -> bool:
        """
        将纯文本转换为 DOCX。

        参数:
            input_path: 文本文件路径
            output_path: 输出 DOCX 文件路径
            encoding: 文本编码

        返回:
            是否成功转换
        """
        try:
            text = Path(input_path).read_text(encoding=encoding)
            return self._create_docx_from_text(text, output_path)
        except Exception as e:
            print(f"转换失败: {e}")
            return False

    def get_supported_formats(self) -> list[str]:
        """
        获取支持的输出格式列表。

        返回:
            支持的格式列表
        """
        return list(self.SUPPORTED_OUTPUT_FORMATS.keys())

    def _find_libreoffice(self) -> str | None:
        """查找 LibreOffice 可执行文件"""
        common_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            "/usr/bin/libreoffice",
            "/usr/bin/soffice",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        ]

        for path in common_paths:
            if Path(path).exists():
                return path

        try:
            result = subprocess.run(
                ["which", "libreoffice"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        try:
            result = subprocess.run(
                ["where", "soffice"],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0:
                return result.stdout.strip().split("\n")[0]
        except Exception:
            pass

        return None

    def _convert_via_libreoffice(
        self,
        input_path: Path,
        output_path: Path,
        output_format: str
    ) -> bool:
        """使用 LibreOffice 进行转换"""
        if not self.libreoffice_path:
            raise RuntimeError("未找到 LibreOffice，无法进行转换")

        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        format_map = {
            "pdf": "pdf",
            "html": "html",
            "txt": "txt:Text",
            "docx": "docx",
            "doc": "doc",
            "odt": "odt",
            "rtf": "rtf",
        }

        convert_format = format_map.get(output_format.lower(), output_format)

        try:
            cmd = [
                self.libreoffice_path,
                "--headless",
                "--convert-to",
                convert_format,
                "--outdir",
                str(output_dir),
                str(input_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                print(f"LibreOffice 转换失败: {result.stderr}")
                return False

            expected_output = output_dir / f"{input_path.stem}.{output_format}"
            if expected_output.exists() and expected_output != output_path:
                shutil.move(str(expected_output), str(output_path))

            return output_path.exists()

        except subprocess.TimeoutExpired:
            print("LibreOffice 转换超时")
            return False
        except Exception as e:
            print(f"转换过程出错: {e}")
            return False

    def _convert_from_docx(
        self,
        input_path: Path,
        output_path: Path,
        output_format: str
    ) -> bool:
        """从 DOCX 转换到其他格式"""
        format_lower = output_format.lower()

        if format_lower == "pdf":
            return self.to_pdf(str(input_path), str(output_path))
        if format_lower == "html":
            return self.to_html(str(input_path), str(output_path))
        if format_lower in ("txt", "text"):
            return self.to_txt(str(input_path), str(output_path))
        if format_lower in ("md", "markdown"):
            return self.to_markdown(str(input_path), str(output_path))
        return self._convert_via_libreoffice(input_path, output_path, output_format)

    def _convert_to_docx(
        self,
        input_path: Path,
        output_path: Path,
        input_format: str
    ) -> bool:
        """从其他格式转换到 DOCX"""
        format_lower = input_format.lower()

        if format_lower == "html":
            return self.from_html(str(input_path), str(output_path))
        if format_lower in ("txt", "text"):
            return self.from_txt(str(input_path), str(output_path))
        return self._convert_via_libreoffice(input_path, output_path, "docx")

    def _extract_text_from_docx(self, input_path: str) -> str:
        """从 DOCX 提取纯文本"""
        import zipfile

        text_parts = []
        with zipfile.ZipFile(input_path, "r") as zf:
            if "word/document.xml" in zf.namelist():
                content = zf.read("word/document.xml").decode("utf-8")

                import re
                text_matches = re.findall(r"<w:t[^>]*>([^<]*)</w:t>", content)
                text_parts = text_matches

        return "\n".join(text_parts)

    def _convert_to_markdown(self, input_path: str) -> str:
        """将 DOCX 转换为 Markdown 格式"""
        text = self._extract_text_from_docx(input_path)
        paragraphs = text.split("\n")

        markdown_lines = []
        for para in paragraphs:
            para = para.strip()
            if para:
                markdown_lines.append(para)
                markdown_lines.append("")

        return "\n".join(markdown_lines)

    def _create_docx_from_text(self, text: str, output_path: str) -> bool:
        """从文本创建 DOCX 文件"""
        try:
            from docx import Document as PythonDocx
            doc = PythonDocx()

            for line in text.split("\n"):
                doc.add_paragraph(line)

            doc.save(output_path)
            return True
        except ImportError:
            print("警告: python-docx 未安装，使用基础方法创建文档")
            return self._create_basic_docx(text, output_path)

    def _create_basic_docx(self, text: str, output_path: str) -> bool:
        """使用基础方法创建 DOCX 文件"""
        import zipfile

        content = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
"""

        for line in text.split("\n"):
            escaped_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            content += f"""<w:p><w:r><w:t>{escaped_line}</w:t></w:r></w:p>
"""

        content += """</w:body>
</w:document>"""

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""")
            zf.writestr("word/document.xml", content)
            zf.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>""")

        return True

    def _convert_to_pdf_python(self, input_path: str, output_path: str) -> bool:
        """使用 Python 库转换为 PDF"""
        try:
            from docx2pdf import convert
            convert(input_path, output_path)
            return True
        except ImportError:
            print("警告: docx2pdf 未安装")
            if self.libreoffice_path:
                return self._convert_via_libreoffice(
                    Path(input_path),
                    Path(output_path),
                    "pdf"
                )
            return False
